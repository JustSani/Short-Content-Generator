import os
import yt_dlp

# Percorso assoluto della cartella dove salvare i video grezzi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "data", "raw")

def download_video_core(url: str) -> dict:
    """
    Scarica un video da YouTube usando yt-dlp e lo salva in data/raw.
    Restituisce un dizionario con i metadati del video (titolo, percorso file, ecc).
    """
    
    # Assicuriamoci che la cartella esista
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Configurazione di yt-dlp
    ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(BASE_DIR, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            
            # --- FIX PER IL TIMEOUT ---
            'socket_timeout': 60,          # Aspetta 60 secondi invece di arrendersi subito
            'source_address': '0.0.0.0',   # Forza l'uso di IPv4 (Risolve il 99% dei timeout)
            'extractor_retries': 3,        # Riprova 3 volte se fallisce
            'http_headers': {              # Finge di essere un browser Chrome su Windows
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Estraiamo le info prima di scaricare per avere il titolo
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'video_sconosciuto')
            
            # 2. Scarichiamo effettivamente
            ydl.download([url])
            
            # Costruiamo il percorso del file finale (stimato)
            filename = ydl.prepare_filename(info)
            
            return {
                "success": True,
                "title": video_title,
                "path": filename,
                "duration": info.get('duration')
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }