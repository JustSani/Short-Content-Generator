import os
import json
import re
import requests

def get_reddit_story_core(url: str) -> dict:
    """
    Scarica titolo e testo da un post o commento specifico di Reddit.
    Sfrutta l'endpoint .json pubblico di Reddit.
    """
    # 1. Pulizia URL e aggiunta del suffisso magico .json
    clean_url = url.split('?')[0].rstrip('/')
    json_url = f"{clean_url}.json"
    
    # Reddit blocca le richieste senza un User-Agent credibile
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ShortVideoGenerator/1.0'
    }
    
    try:
        response = requests.get(json_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 2. Estrazione del Titolo (sempre presente nel primo blocco)
        post_data = data[0]['data']['children'][0]['data']
        title = post_data.get('title', 'Reddit Story').upper()
        
        # 3. Estrazione del Testo (Post principale o Commento specifico)
        text = ""
        # Se l'URL puntava a un commento, lo troviamo nel secondo blocco dell'array JSON
        if len(data) > 1 and len(data[1]['data']['children']) > 0:
            comment_data = data[1]['data']['children'][0]['data']
            if 'body' in comment_data:
                text = comment_data['body']
        
        # Se non era un commento (o se ha fallito), prendiamo il testo del post
        if not text:
            text = post_data.get('selftext', '')
            
        # 4. Pulizia del Markdown di Reddit per il TTS
        # Rimuove asterischi, underscore per il corsivo/grassetto e formatta i link
        text = re.sub(r'[\*\_~]', '', text) 
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text) 
        
        if not text.strip():
            return {"success": False, "error": "Il post è un'immagine o non contiene testo."}
            
        return {
            "success": True, 
            "data": {"title": title, "text": text}
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}