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
        'format': 'bestvideo+bestaudio/best', # Miglior qualità possibile
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'), # Nome file = Titolo video
        'quiet': True,             # Meno output nel terminale (gestiamo noi i messaggi)
        'no_warnings': True,
        'restrictfilenames': True, # Rimuove caratteri strani dal nome file
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