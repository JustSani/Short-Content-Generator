import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Carica la chiave dal file .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ ERRORE: Chiave API Gemini non trovata nel file .env!")

genai.configure(api_key=API_KEY)

def clean_json_string(text: str) -> str:
    """Pulisce la risposta dell'AI se include markdown"""
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()

def generate_script_core(topic: str) -> dict:
    # Usiamo il modello stabile e gratuito
    model = genai.GenerativeModel('gemini-3-flash-preview')

    prompt = f"""
    Sei un esperto sceneggiatore di video Short/TikTok virali.
    Il tuo compito è scrivere uno script coinvolgente sull'argomento: "{topic}".
    
    REGOLE RIGIDE:
    1. Rispondi ESCLUSIVAMENTE con un oggetto JSON valido. Niente testo prima o dopo.
    2. Il JSON deve avere due chiavi: "title" e "text".
    3. "title": Gancio breve, scioccante, tutto in MAIUSCOLO (max 6 parole).
    4. "text": Script da leggere (circa 130-150 parole).
       - Inizia con un hook forte.
       - Linguaggio semplice e diretto.
       - Niente hashtag o emoji.
       - Lingua: ITALIANO.

    Esempio Output:
    {{
        "title": "NON CREDERAI A QUESTO!",
        "text": "Sapevi che le banane sono radioattive? Esatto, contengono potassio..."
    }}
    """

    try:
        response = model.generate_content(prompt)
        clean_text = clean_json_string(response.text)
        
        # --- CORREZIONE QUI ---
        # Usiamo json.loads (stringa) invece di json.load (file)
        script_data = json.loads(clean_text)
        # ----------------------
        
        if "title" not in script_data or "text" not in script_data:
            return {"success": False, "error": "JSON non valido."}
            
        return {"success": True, "data": script_data}

    except Exception as e:
        return {"success": False, "error": str(e)}

def save_script_to_file(topic: str, data: dict) -> str:
    stories_dir = os.path.join("stories")
    os.makedirs(stories_dir, exist_ok=True)
    
    safe_name = re.sub(r'[^\w\s-]', '', topic).strip().lower()
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    filename = f"{safe_name}.json"
    
    file_path = os.path.join(stories_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    return file_path