import os
import asyncio
import subprocess
import re
import json
import edge_tts
from src.utils.naming import get_step_filename

# --- CONFIGURAZIONI ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp")
FONTS_DIR_ABS = os.path.join(BASE_DIR, "assets", "fonts")

VOICE = "it-IT-GiuseppeMultilingualNeural"
RATE = "+42%"
PITCH = "-14Hz"

def clean_text_display(text: str) -> str:
    text = re.sub(r'[^\w\s\']', '', text) 
    return text.strip()

def split_into_sentences(text: str):
    sentences = re.split(r'(?<=[.?!])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

async def generate_chunk_audio(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(output_path)

def get_audio_duration(file_path: str) -> float:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

# --- NUOVO FORMATO TEMPO PER FILE .ASS ---
def fmt_time_ass(t):
    """Formatta il tempo per il file ASS: H:MM:SS.cs"""
    hours = int(t / 3600)
    mins = int((t % 3600) / 60)
    secs = int(t % 60)
    centis = int((t - int(t)) * 100) # Centesimi di secondo
    return f"{hours}:{mins:02}:{secs:02}.{centis:02}"

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

    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    for f in os.listdir(TEMP_DIR): os.remove(os.path.join(TEMP_DIR, f))

    output_filename = get_step_filename(video_path, "NARRATED")
    output_path = os.path.join(PROCESSED_DIR, output_filename)
    
    final_audio_path = os.path.join(TEMP_DIR, "full_narration.mp3")
    ass_path = os.path.join(TEMP_DIR, "subtitles.ass") # UNICO FILE ASS

    try:
        word_timings = []
        total_time_cursor = 0.0
        
        concat_list_path = os.path.join(TEMP_DIR, "concat_list.txt")
        concat_file = open(concat_list_path, "w", encoding="utf-8")

        # --- 1. GESTIONE TITOLO ---
        if title_text:
            title_audio_path = os.path.join(TEMP_DIR, "title.mp3")
            asyncio.run(generate_chunk_audio(title_text, title_audio_path))
            title_duration = get_audio_duration(title_audio_path)
            concat_file.write(f"file 'title.mp3'\n")
            total_time_cursor += title_duration + 0.4 
            
        # --- 2. GESTIONE CORPO ---
        sentences = split_into_sentences(body_text)
        for idx, sentence in enumerate(sentences):
            chunk_filename = f"chunk_{idx}.mp3"
            chunk_path = os.path.join(TEMP_DIR, chunk_filename)
            asyncio.run(generate_chunk_audio(sentence, chunk_path))
            duration = get_audio_duration(chunk_path)
            
            words = sentence.split()
            # Calcolo pesi (inline per brevità)
            cleaned_words = [clean_text_display(w) for w in words]
            weights = []
            for w, cw in zip(words, cleaned_words):
                weight = len(cw)
                if len(cw) <= 3: weight *= 0.6
                elif len(cw) >= 8: weight *= 1.4
                if w.endswith('.') or w.endswith('?') or w.endswith('!'): weight += 4
                elif w.endswith(','): weight += 2
                weights.append(weight)

            total_weight = sum(weights)
            current_time = total_time_cursor

            if total_weight > 0 and duration > 0:
                for i, cw in enumerate(cleaned_words):
                    segment_duration = max(0.1, (weights[i] / total_weight) * duration)
                    end = current_time + segment_duration
                    word_timings.append((current_time, end, cw.upper()))
                    current_time = end

            total_time_cursor += duration
            concat_file.write(f"file '{chunk_filename}'\n")

        concat_file.close()

        # --- 3. UNIONE AUDIO ---
        concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list_path, "-c", "copy", final_audio_path
        ]
        subprocess.run(concat_cmd, check=True, capture_output=True)

        # --- 4. GENERAZIONE FILE .ASS (La VERA MAGIA GRAFICA) ---
        # Dato che la tela ora è 1080x1920, la dimensione "15" di prima equivale a circa "60" qui.
        # Alignment 8 = In alto al centro. Alignment 5 = Centro esatto.
        
        # ⚠️ NOME FONT: Se "The Bold Font" continua a non andare, scrivi "Impact" al suo posto
        FONT_NAME = "The Bold Font"

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1080\n")  # FONDAMENTALE: Dichiariamo le dimensioni del video!
            f.write("PlayResY: 1920\n")
            f.write("WrapStyle: 1\n\n")

            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            # Stile Titolo (Giallo, Outline nero sottile, Alto Centro con margine 150 dal top)
            f.write(f"Style: TitleStyle,{FONT_NAME},150,&H0000FFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,10,0,8,0,0,150,1\n")
            # Stile Corpo (Bianco, Outline nero sottile, Centro Assoluto con margine 0)
            f.write(f"Style: BodyStyle,{FONT_NAME},100,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,10,0,5,0,0,0,1\n\n")

            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            if title_text:
                f.write(f"Dialogue: 0,0:00:00.00,9:59:59.99,TitleStyle,,0,0,0,,{title_text.upper()}\n")
            for start, end, word_text in word_timings:
                f.write(f"Dialogue: 0,{fmt_time_ass(start)},{fmt_time_ass(end)},BodyStyle,,0,0,0,,{word_text}\n")

        # --- 5. MERGE VIDEO ---
        ass_path_safe = ass_path.replace("\\", "/").replace(":", "\\:")
        fonts_dir_safe = FONTS_DIR_ABS.replace("\\", "/").replace(":", "\\:")
        
        # Il filtro diventa semplicissimo: usa il file ASS e cerca i font nella cartella.
        filter_complex = (
            f"[0:v]ass='{ass_path_safe}':fontsdir='{fonts_dir_safe}'[v_out];"
            f"[1:a]volume=1.2[a_out]"
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