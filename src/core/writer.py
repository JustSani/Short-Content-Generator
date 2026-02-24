import os
import json
import re
from google import genai
from dotenv import load_dotenv

# Carica la chiave dal file .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ ERRORE: Chiave API Gemini non trovata nel file .env!")

# Nuova inizializzazione del Client GenAI
client = genai.Client(api_key=API_KEY)

def clean_json_string(text: str) -> str:
    """Pulisce la risposta dell'AI se include markdown"""
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()

def generate_script_core(topic: str) -> dict:
    prompt = f"""
    Sei un Copywriter Virale per TikTok. Scrivi uno script su: "{topic}".
    
    REGOLE DI SCRITTURA:
    1. HOOK VISIVO/UDITIVO: La prima frase deve fermare lo scroll.
    2. RITMO VELOCE: Usa frasi brevi. Niente subordinate complesse.
    3. NO FILLER: Niente "Ciao ragazzi". Inizia subito con l'azione.
    4. LINGUAGGIO: Italiano naturale, colloquiale.
    5. DURATA: Target 140 parole.

    FORMATO OUTPUT OBBLIGATORIO (JSON PURO):
    {{
        "title": "TITOLO BREVE E MAIUSCOLO (MAX 6 PAROLE), IMPORTANTE CHE CONTENGA IL NOME DELLA SERIE O FILM",
        "text": "Qui inserisci tutto il testo che verrà letto dal narratore. Niente emoji."
    }}
    """

    try:
        # Nuova sintassi per la generazione
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
        )
        clean_text = clean_json_string(response.text)
        
        script_data = json.loads(clean_text)
        
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