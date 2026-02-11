import os
import re
from datetime import datetime

def get_step_filename(input_path: str, step: str) -> str:
    """
    Genera il nome file nel formato: YY_MM_DD_NomeOriginale_STEP.mp4
    Pulisce automaticamente il nome per evitare l'accumulo di vecchi step.
    """
    # 1. Genera la data odierna (es. 26_02_11)
    date_str = datetime.now().strftime("%y_%m_%d")
    
    # 2. Prende il nome base senza cartelle e senza estensione (.mp4)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # 3. PULIZIA: Rimuove la data se era già presente all'inizio (es. per evitare 26_02_11_26_02_11_)
    base_name = re.sub(r'^\d{2}_\d{2}_\d{2}_', '', base_name)
    
    # 4. PULIZIA: Rimuove i tag degli step precedenti per non fare catene lunghissime
    base_name = re.sub(r'_CUT_[\d-]+_[\d-]+', '', base_name)
    base_name = re.sub(r'_VERTICAL', '', base_name)
    base_name = re.sub(r'_NARRATED', '', base_name)
    
    # 5. Assembla il nome finale
    return f"{date_str}_{base_name}_{step}.mp4"