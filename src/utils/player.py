import os
import platform
import subprocess

def open_file_native(file_path: str):
    """
    Apre un file con il player predefinito del sistema operativo.
    """
    if not os.path.exists(file_path):
        print(f"❌ Errore: Il file {file_path} non esiste.")
        return

    system_name = platform.system()

    try:
        if system_name == "Windows":
            # Metodo nativo Windows (velocissimo)
            os.startfile(file_path)
        
        elif system_name == "Darwin":  # macOS
            subprocess.run(["open", file_path], check=True)
        
        else:  # Linux
            subprocess.run(["xdg-open", file_path], check=True)
            
    except Exception as e:
        print(f"❌ Impossibile aprire il file automaticamente: {e}")