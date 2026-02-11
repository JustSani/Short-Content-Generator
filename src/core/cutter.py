import os
import subprocess
from src.utils.time_utils import parse_time_str
from src.utils.naming import get_step_filename

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def cut_video_interval_core(input_path: str, start_str: str, end_str: str) -> dict:
    """
    Taglia un video usando 'Input Seeking' (molto più veloce) e re-encoding veloce.
    """
    if not os.path.exists(input_path):
        return {"success": False, "error": f"File non trovato: {input_path}"}

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    try:
        # Convertiamo i tempi in secondi
        start_sec = parse_time_str(start_str)
        end_sec = parse_time_str(end_str)

        if start_sec >= end_sec:
            return {"success": False, "error": "Il tempo di inizio deve essere minore della fine."}

        # CALCOLO DURATA (Necessario per Input Seeking)
        # Quando usiamo -ss prima dell'input, il timestamp riparte da 0.
        # Quindi non possiamo usare -to (tempo finale), ma dobbiamo dire "dura X secondi".
        duration = end_sec - start_sec

        # --- NUOVA GESTIONE NOME ---
        safe_start = start_str.replace(":", "-")
        safe_end = end_str.replace(":", "-")
        
        output_filename = get_step_filename(input_path, f"CUT_{safe_start}_{safe_end}")
        output_path = os.path.join(PROCESSED_DIR, output_filename)
        # ---------------------------

        # Costruiamo il comando FFmpeg OTTIMIZZATO
        cmd = [
            "ffmpeg",
            "-y", 
            
            # --- INPUT SEEKING (La chiave della velocità) ---
            # Mettere -ss PRIMA di -i fa saltare ffmpeg direttamente al punto
            "-ss", str(start_sec),
            
            "-i", input_path,       # Input
            
            "-t", str(duration),    # Durata del taglio (non punto finale)
            
            # --- ENCODING VELOCE ---
            "-c:v", "libx264",      # Codec Video
            "-preset", "ultrafast", # <--- CAMBIATO: Massima velocità
            "-crf", "23",           # Qualità standard
            "-c:a", "aac",          # Codec Audio
            "-b:a", "128k",
            "-movflags", "+faststart",
            
            "-map", "0",
            output_path
        ]

        # Eseguiamo
        subprocess.run(cmd, check=True, capture_output=True)

        return {
            "success": True,
            "path": output_path,
            "original_path": input_path,
            "start": start_str,
            "end": end_str
        }

    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8') if e.stderr else str(e)
        return {
            "success": False,
            "error": f"Errore FFmpeg: {error_message}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }