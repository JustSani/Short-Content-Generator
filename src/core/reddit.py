import os
import json
import re
import requests

def get_reddit_story_core(url: str) -> dict:
    """
    Scarica titolo e testo da un post di Reddit.
    Prende il contenuto del post principale (selftext).
    """
    clean_url = url.split('?')[0].rstrip('/')
    json_url = f"{clean_url}.json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ShortVideoGenerator/2.0'
    }
    
    try:
        response = requests.get(json_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Dati del post principale
        post_data = data[0]['data']['children'][0]['data']
        title = post_data.get('title', 'Reddit Story').upper()
        
        # 1. PRENDIAMO IL TESTO DEL POST PRINCIPALE (La storia)
        text = post_data.get('selftext', '').strip()
        
        # 2. Solo se il post principale è vuoto (es. hai incollato il link diretto a un commento),
        # cerchiamo nei commenti
        if not text and len(data) > 1 and len(data[1]['data']['children']) > 0:
            comment_data = data[1]['data']['children'][0]['data']
            text = comment_data.get('body', '').strip()
            
        # Pulizia del Markdown di Reddit
        text = re.sub(r'[\*\_~]', '', text) 
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text) 
        
        if not text.strip():
            return {"success": False, "error": "Il post è vuoto, è un'immagine o non contiene testo."}
            
        return {
            "success": True, 
            "data": {"title": title, "text": text}
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}