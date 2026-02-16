import json
import os
import time
from rich.console import Console

# Importiamo i nostri moduli esistenti
from src.core.writer import generate_script_core, save_script_to_file
from src.core.downloader import download_video_core
from src.core.cutter import cut_video_interval_core
from src.core.resizer import convert_to_vertical_core
from src.core.narrator import add_narration_core

console = Console()
JOBS_FILE = "jobs.json"

# --- CALCOLO CARTELLA RADICE DEL PROGETTO ---
# Risale di 3 livelli da: src/core/batch.py -> src/core -> src -> PROJECT_ROOT
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4, ensure_ascii=False)

def update_job_status(index, status, error=None):
    jobs = load_jobs()
    jobs[index]["status"] = status
    if error:
        jobs[index]["error"] = error
    jobs[index]["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_jobs(jobs)

def run_batch_process():
    jobs = load_jobs()
    pending_jobs = [j for j in jobs if j.get("status") == "pending"]

    if not pending_jobs:
        console.print("[bold green]✅ Nessun lavoro in sospeso (pending) trovato in jobs.json![/bold green]")
        return

    console.print(f"[bold cyan]🏭 Avvio Factory Mode: {len(pending_jobs)} video in coda...[/bold cyan]")

    for i, job in enumerate(jobs):
        if job.get("status") != "pending":
            continue

        console.rule(f"[bold yellow]Job #{i+1}: {job['topic']}[/bold yellow]")
        
        try:
            # --- STEP 1: SCRITTURA SCRIPT (AI) ---
            console.print("[1/5] 🧠 Generazione Script con Gemini...")
            res_write = generate_script_core(job["topic"])
            if not res_write["success"]:
                raise Exception(f"Errore AI: {res_write['error']}")
            
            script_data = res_write["data"]
            script_path = save_script_to_file(job["topic"], script_data)
            console.print(f"      📝 Script salvato: {os.path.basename(script_path)}")

            # --- STEP 2: ACQUISIZIONE VIDEO (FIX PATH RELATIVI) ---
            source = job["source"]
            current_video = source
            
            if source.startswith("http"):
                console.print(f"[2/5] ⬇️  Download video da YouTube...")
                res_dl = download_video_core(source)
                if not res_dl["success"]:
                    raise Exception(f"Errore Download: {res_dl['error']}")
                current_video = res_dl["path"]
            else:
                console.print(f"[2/5] 📂 Rilevamento file locale...")
                
                # --- LOGICA INTELLIGENTE PER I PATH ---
                # 1. Puliamo il percorso da virgolette o slash iniziali inutili
                clean_source = source.strip('"').strip("'").lstrip("/").lstrip("\\")
                
                # 2. Costruiamo il percorso assoluto partendo dalla root del progetto
                abs_path_from_root = os.path.join(BASE_DIR, clean_source)
                
                # 3. Cerchiamo il file
                if os.path.exists(abs_path_from_root):
                    current_video = abs_path_from_root
                    console.print(f"      📍 Trovato in: [dim]{current_video}[/dim]")
                elif os.path.exists(source):
                    # Fallback: magari l'utente ha messo un path assoluto (C:\...)
                    current_video = source
                    console.print(f"      📍 Trovato (path assoluto): [dim]{current_video}[/dim]")
                else:
                    raise Exception(f"File non trovato! Cercato in:\n - {abs_path_from_root}\n - {source}")

            # --- STEP 3: TAGLIO ---
            if job.get("start") and job.get("end"):
                console.print(f"[3/5] ✂️  Taglio clip ({job['start']} - {job['end']})...")
                res_cut = cut_video_interval_core(current_video, job["start"], job["end"])
                if not res_cut["success"]:
                    raise Exception(f"Errore Taglio: {res_cut['error']}")
                current_video = res_cut["path"]
            else:
                console.print("[3/5] ⏩ Salto taglio (timestamp non forniti)")

            # --- STEP 4: RESIZE VERTICALE ---
            console.print(f"[4/5] 📱 Conversione in 9:16...")
            res_resize = convert_to_vertical_core(current_video)
            if not res_resize["success"]:
                raise Exception(f"Errore Resize: {res_resize['error']}")
            current_video = res_resize["path"]

            # --- STEP 5: NARRAZIONE + SOTTOTITOLI ---
            console.print(f"[5/5] 🎙️  Doppiaggio e Sottotitoli (Whisper)...")
            res_narrate = add_narration_core(current_video, script_data)
            if not res_narrate["success"]:
                raise Exception(f"Errore Narratore: {res_narrate['error']}")
            
            final_video = res_narrate["path"]

            # --- CONCLUSIONE ---
            console.print(f"[bold green]✅ VIDEO COMPLETATO: {final_video}[/bold green]")
            update_job_status(i, "done")
            
        except Exception as e:
            console.print(f"[bold red]❌ FALLIMENTO JOB #{i+1}: {str(e)}[/bold red]")
            update_job_status(i, "error", str(e))
            continue