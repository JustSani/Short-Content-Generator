import os
import subprocess

from src.utils.naming import get_step_filename

# Definiamo i percorsi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def convert_to_vertical_core(input_path: str) -> dict:
    """
    Prende un video di qualsiasi formato (16:9, 4:3, 1:1) e lo converte
    in 9:16 (1080x1920) riempiendo lo schermo (Center Crop) usando FFmpeg.
    """
    
    if not os.path.exists(input_path):
        return {"success": False, "error": f"File non trovato: {input_path}"}

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    try:
        # --- NUOVA GESTIONE NOME ---
        output_filename = get_step_filename(input_path, "VERTICAL")
        output_path = os.path.join(PROCESSED_DIR, output_filename)
        # ---------------------------
        
        # --- LA MAGIA DI FFMPEG ---
        # Filtro vf:
        # 1. scale=1080:1920:force_original_aspect_ratio=increase
        #    Ingrandisce il video finché entrambi i lati sono >= 1080x1920.
        #    Mantiene l'aspect ratio originale (non schiaccia l'immagine).
        # 2. crop=1080:1920:(iw-1080)/2:(ih-1920)/2
        #    Ritaglia un rettangolo di 1080x1920 esattamente al centro.
        # 3. setsar=1
        #    Imposta il Pixel Aspect Ratio a 1 (quadrato) per evitare problemi su player vecchi.
        
        filter_complex = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-1080)/2:(ih-1920)/2,setsar=1"

        cmd = [
            "ffmpeg",
            "-y",                     # Sovrascrivi se esiste
            "-i", input_path,         # Input
            "-vf", filter_complex,    # Applica il filtro video smart
            "-c:v", "libx264",        # Codec Video H.264 (Standard universale)
            "-preset", "fast",        # Bilanciamento velocità/compressione
            "-crf", "23",             # Qualità visuale (valore più basso = qualità più alta)
            "-c:a", "aac",            # Codec Audio AAC (Standard per TikTok/YT)
            "-b:a", "128k",           # Bitrate audio
            "-movflags", "+faststart",# Ottimizza per lo streaming web
            output_path
        ]

        # Eseguiamo
        subprocess.run(cmd, check=True, capture_output=True)

        return {
            "success": True,
            "path": output_path,
            "original_path": input_path
        }

    except subprocess.CalledProcessError as e:
        # Se FFmpeg fallisce, catturiamo l'output di errore
        err_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        return {
            "success": False,
            "error": f"Errore FFmpeg: {err_msg}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }