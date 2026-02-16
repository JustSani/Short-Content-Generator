import os
import re
from datetime import datetime

def get_step_filename(input_path: str, step: str) -> str:
    """
    Genera il nome file nel formato: YY_MM_DD_HHMMSS_NomeOriginale_STEP.mp4
    Pulisce automaticamente il nome per evitare l'accumulo di vecchi step.
    """
    # 1. Genera la data odierna CON ore, minuti e secondi per unicità assoluta
    date_str = datetime.now().strftime("%y_%m_%d_%H%M%S")
    
    # 2. Prende il nome base senza cartelle e senza estensione (.mp4)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # 3. PULIZIA: Rimuove la data vecchia (sia che fosse solo YY_MM_DD, sia YY_MM_DD_HHMMSS)
    base_name = re.sub(r'^\d{2}_\d{2}_\d{2}(_\d{6})?_', '', base_name)
    
    # 4. PULIZIA: Rimuove i tag degli step precedenti per non fare catene lunghissime
    base_name = re.sub(r'_CUT_[\d-]+_[\d-]+', '', base_name)
    base_name = re.sub(r'_VERTICAL', '', base_name)
    base_name = re.sub(r'_NARRATED', '', base_name)
    
    # Rimuove eventuali underscore multipli rimasti
    base_name = re.sub(r'_+', '_', base_name).strip('_')
    
    # 5. Assembla il nome finale
    return f"{date_str}_{base_name}_{step}.mp4"