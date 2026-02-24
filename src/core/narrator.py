import os
import asyncio
import subprocess
import re
import json
import shutil
import edge_tts
from faster_whisper import WhisperModel
from src.utils.naming import get_step_filename

# --- CONFIGURAZIONI ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
READY_DIR = os.path.join(BASE_DIR, "data", "ready")
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp")
FONTS_DIR_ABS = os.path.join(BASE_DIR, "assets", "fonts")

# Config Audio
VOICE = "it-IT-GiuseppeMultilingualNeural"
RATE = "+42%"
PITCH = "-14Hz"

# Config Whisper
WHISPER_MODEL_SIZE = "medium" 
WHISPER_DEVICE = "cpu" 

def get_audio_duration(file_path: str) -> float:
    """Restituisce la durata di un file audio/video in secondi usando ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def clean_text_display(text: str) -> str:
    """Pulisce il testo per la visualizzazione a video"""
    return text.strip()

async def generate_full_audio(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(output_path)

def fmt_time_ass(t):
    """Formatta il tempo per il file ASS: H:MM:SS.cs"""
    hours = int(t / 3600)
    mins = int((t % 3600) / 60)
    secs = int(t % 60)
    centis = int((t - int(t)) * 100)
    return f"{hours}:{mins:02}:{secs:02}.{centis:02}"

def transcribe_audio_with_whisper(audio_path: str, offset_seconds: float):
    """
    Usa Whisper per ottenere i timestamp precisi di ogni parola.
    Applica un offset temporale.
    """
    print(f"   ...Caricamento modello Whisper ({WHISPER_MODEL_SIZE})...")
    model = WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type="int8")

    print("   ...Trascrizione e allineamento in corso...")
    segments, _ = model.transcribe(audio_path, word_timestamps=True, language="it")

    word_timings = []
    
    for segment in segments:
        for word in segment.words:
            start_t = word.start + offset_seconds
            end_t = word.end + offset_seconds
            text = word.word.strip().upper() 
            
            # Filtro per rimuovere punteggiatura isolata
            if text in [".", ",", "!", "?", ":", ";"]:
                continue
                
            word_timings.append((start_t, end_t, text))

    return word_timings

def add_narration_core(video_path: str, text_input) -> dict:
    if not os.path.exists(video_path):
        return {"success": False, "error": f"Video non trovato: {video_path}"}

    # --- NORMALIZZAZIONE INPUT ---
    story_data = {"title": "", "text": ""}
    if isinstance(text_input, dict):
        story_data = text_input
    elif isinstance(text_input, str):
        clean_path = text_input.strip('"').strip("'")
        if os.path.exists(clean_path) and os.path.isfile(clean_path):
            if clean_path.endswith('.json'):
                try:
                    with open(clean_path, "r", encoding="utf-8") as f:
                        story_data = json.load(f)
                except Exception as e:
                    return {"success": False, "error": f"Errore lettura JSON: {e}"}
            else:
                with open(clean_path, "r", encoding="utf-8") as f:
                    story_data["text"] = f.read()
        else:
            story_data["text"] = clean_path
    
    title_text = story_data.get("title", "").strip()
    body_text = story_data.get("text", "").strip()
    
    if not body_text:
        return {"success": False, "error": "Testo principale vuoto."}

    # --- SETUP CARTELLE ---
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(READY_DIR, exist_ok=True)
    for f in os.listdir(TEMP_DIR): os.remove(os.path.join(TEMP_DIR, f))

    output_filename = get_step_filename(video_path, "NARRATED")
    output_path = os.path.join(READY_DIR, output_filename)
    
    # Percorsi file temporanei
    final_audio_path = os.path.join(TEMP_DIR, "final_audio.mp3")
    ass_path = os.path.join(TEMP_DIR, "subtitles.ass")

    try:
        # --- 1. GENERAZIONE AUDIO (SOLO CORPO TESTO) ---
        current_offset = 0.2
        asyncio.run(generate_full_audio(body_text, final_audio_path))

        # --- 2. TRASCRIZIONE CON WHISPER ---
        word_timings = transcribe_audio_with_whisper(final_audio_path, current_offset)

        # --- 3. CREAZIONE FILE .ASS ---
        FONT_NAME = "The Bold Font"

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1080\n")
            f.write("PlayResY: 1920\n")
            f.write("WrapStyle: 1\n\n")

            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            # Stile Titolo
            f.write(f"Style: TitleStyle,{FONT_NAME},150,&H0000FFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,10,0,8,0,0,150,1\n")
            # Stile Corpo
            f.write(f"Style: BodyStyle,{FONT_NAME},100,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,10,0,5,0,0,0,1\n\n")

            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            # Il titolo appare a schermo ma non viene pronunciato
            if title_text:
                f.write(f"Dialogue: 0,0:00:00.20,9:59:59.99,TitleStyle,,0,0,0,,{title_text.upper()}\n")
            
            for start, end, word_text in word_timings:
                f.write(f"Dialogue: 0,{fmt_time_ass(start)},{fmt_time_ass(end)},BodyStyle,,0,0,0,,{word_text}\n")

        # --- 4. MERGE VIDEO ---
        ass_path_safe = ass_path.replace("\\", "/").replace(":", "\\:")
        fonts_dir_safe = FONTS_DIR_ABS.replace("\\", "/").replace(":", "\\:")
        
        # Aggiungiamo un ritardo di 200ms all'audio per matchare l'offset
        filter_complex = (
            f"[0:v]ass='{ass_path_safe}':fontsdir='{fonts_dir_safe}'[v_out];"
            f"[1:a]adelay=200|200,volume=1.2[a_out]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", final_audio_path,
            "-filter_complex", filter_complex,
            "-map", "[v_out]",
            "-map", "[a_out]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-tune", "zerolatency",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        return {"success": True, "path": output_path, "srt_path": ass_path}

    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        return {"success": False, "error": f"Errore FFmpeg: {err_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}