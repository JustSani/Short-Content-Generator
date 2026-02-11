import json
import os

# Definiamo il percorso del file di stato: content-automator/data/state.json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(BASE_DIR, "data", "state.json")

def load_state() -> dict:
    """Legge il file di stato. Se non esiste, ritorna un dizionario vuoto."""
    if not os.path.exists(STATE_FILE):
        return {}
    
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_state(key: str, value: str):
    """Salva una coppia chiave-valore nel file di stato."""
    # 1. Carichiamo lo stato attuale
    current_state = load_state()
    
    # 2. Aggiorniamo il valore
    current_state[key] = value
    
    # 3. Scriviamo su disco
    # Creiamo la cartella data se per assurdo non esistesse
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_state, f, indent=4)

def get_last_video() -> str:
    """Recupera il percorso dell'ultimo video scaricato."""
    data = load_state()
    return data.get("last_downloaded_video", None)

def save_text_content(text: str):
    """Salva il testo da narrare."""
    save_state("current_text", text)

def get_text_content() -> str:
    """Recupera il testo da narrare."""
    data = load_state()
    return data.get("current_text", "")