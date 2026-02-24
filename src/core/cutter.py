import os
import random
import subprocess
from src.utils.naming import get_step_filename

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def get_video_duration(file_path: str) -> float:
    """Restituisce la durata del video in secondi usando ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def cut_video_interval_core(input_path: str, start: str, end: str) -> dict:
    """Taglio manuale classico (se l'utente specifica start ed end)."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    output_filename = get_step_filename(input_path, f"CUT_{start.replace(':', '')}_{end.replace(':', '')}")
    output_path = os.path.join(PROCESSED_DIR, output_filename)

    cmd = ["ffmpeg", "-y", "-i", input_path, "-ss", start, "-to", end, "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", output_path]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return {"success": True, "path": output_path}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr.decode()}

def cut_video_random_core(input_path: str, target_duration: float) -> dict:
    """
    Sceglie un punto casuale nel video e taglia esattamente la durata richiesta.
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    total_duration = get_video_duration(input_path)
    
    # Se il video originale è più corto o uguale all'audio, partiamo dall'inizio
    if total_duration <= target_duration:
        start_time = 0.0
    else:
        # Il punto di partenza massimo per non finire "fuori" dal video
        max_start = total_duration - target_duration
        start_time = random.uniform(0, max_start)
    
    # Formattiamo il timestamp casuale in secondi
    start_str = f"{start_time:.2f}"
    duration_str = f"{target_duration:.2f}"
    
    output_filename = get_step_filename(input_path, f"CUT_RANDOM")
    output_path = os.path.join(PROCESSED_DIR, output_filename)

    cmd = [
        "ffmpeg", "-y",
        "-ss", start_str,        # Vai al punto casuale velocemente
        "-i", input_path,        # Leggi il video
        "-t", duration_str,      # Taglia esattamente per la durata dell'audio
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return {"success": True, "path": output_path, "start_time": start_time}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr.decode()}