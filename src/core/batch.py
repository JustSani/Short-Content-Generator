import json
import os
import time
import asyncio
import edge_tts
from rich.console import Console

# Importiamo i nostri moduli esistenti
from src.core.writer import generate_script_core, save_script_to_file
from src.core.reddit import get_reddit_story_core
from src.core.downloader import download_video_core
from src.core.cutter import cut_video_interval_core, cut_video_random_core
from src.core.resizer import convert_to_vertical_core
from src.core.narrator import add_narration_core, get_audio_duration, VOICE, RATE, PITCH

console = Console()
JOBS_FILE = "jobs.json"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp")

def load_jobs():
    if not os.path.exists(JOBS_FILE): return []
    with open(JOBS_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f: json.dump(jobs, f, indent=4, ensure_ascii=False)

def update_job_status(index, status, error=None):
    jobs = load_jobs()
    jobs[index]["status"] = status
    if error: jobs[index]["error"] = error
    jobs[index]["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_jobs(jobs)

async def estimate_audio_duration(text: str) -> float:
    """Genera l'audio temporaneamente per misurarne la lunghezza esatta."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_path = os.path.join(TEMP_DIR, "estimate.mp3")
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(temp_path)
    duration = get_audio_duration(temp_path)
    if os.path.exists(temp_path): os.remove(temp_path)
    return duration

def run_batch_process():
    jobs = load_jobs()
    pending_jobs = [j for j in jobs if j.get("status") == "pending"]

    if not pending_jobs:
        console.print("[bold green]✅ Nessun lavoro in sospeso trovato in jobs.json![/bold green]")
        return

    console.print(f"[bold cyan]🏭 Avvio Factory Mode: {len(pending_jobs)} video in coda...[/bold cyan]")

    for i, job in enumerate(jobs):
        if job.get("status") != "pending": continue
        console.rule(f"[bold yellow]Job #{i+1}: {job['topic']}[/bold yellow]")
        
        try:
            # --- STEP 1: RECUPERO STORIA ---
            topic = job["topic"]
            if topic.startswith("http") and "reddit.com" in topic:
                console.print("[1/6] 👽 Estrazione storia da Reddit...")
                res_write = get_reddit_story_core(topic)
                safe_topic = "reddit_story"
            else:
                console.print("[1/6] 🧠 Generazione Script con Gemini...")
                res_write = generate_script_core(topic)
                safe_topic = topic

            if not res_write["success"]: raise Exception(f"Errore Storia: {res_write['error']}")
            
            script_data = res_write["data"]
            save_script_to_file(safe_topic, script_data)

            # --- STEP 2: MISURA DELLA VOCE (NUOVO) ---
            console.print("[2/6] ⏱️  Calcolo lunghezza esatta del doppiaggio...")
            body_text = script_data.get("text", "")
            # Misuriamo l'audio. Aggiungiamo 0.2s di offset iniziale e 0.5s di margine finale
            audio_seconds = asyncio.run(estimate_audio_duration(body_text)) + 0.7 
            console.print(f"      Durata prevista: {audio_seconds:.2f} secondi.")

            # --- STEP 3: ACQUISIZIONE VIDEO ---
            source = job["source"]
            current_video = source
            
            if source.startswith("http"):
                console.print("[3/6] ⬇️  Download video da YouTube...")
                res_dl = download_video_core(source)
                if not res_dl["success"]: raise Exception(f"Errore Download: {res_dl['error']}")
                current_video = res_dl["path"]
            else:
                console.print("[3/6] 📂 Uso file locale...")
                clean_source = source.strip('"').strip("'").lstrip("/").lstrip("\\")
                abs_path_from_root = os.path.join(BASE_DIR, clean_source)
                if os.path.exists(abs_path_from_root): current_video = abs_path_from_root
                elif os.path.exists(source): current_video = source
                else: raise Exception("File non trovato!")

            # --- STEP 4: TAGLIO CASUALE DINAMICO ---
            if job.get("start") and job.get("end"):
                # Se hai specificato i tempi a mano nel JSON, forza quelli
                console.print(f"[4/6] ✂️  Taglio manuale ({job['start']} - {job['end']})...")
                res_cut = cut_video_interval_core(current_video, job["start"], job["end"])
            else:
                # Altrimenti, TAGLIO CASUALE INTELLIGENTE
                console.print(f"[4/6] 🎲 Taglio casuale di {audio_seconds:.2f} secondi dal video originale...")
                res_cut = cut_video_random_core(current_video, audio_seconds)
                if res_cut.get("success"):
                    console.print(f"      Punto di inizio scelto dal bot: {res_cut['start_time']:.2f}s")
                    
            if not res_cut["success"]: raise Exception(f"Errore Taglio: {res_cut['error']}")
            current_video = res_cut["path"]

            # --- STEP 5: RESIZE VERTICALE ---
            console.print("[5/6] 📱 Conversione in 9:16...")
            res_resize = convert_to_vertical_core(current_video)
            if not res_resize["success"]: raise Exception(f"Errore Resize: {res_resize['error']}")
            current_video = res_resize["path"]

            # --- STEP 6: NARRAZIONE E SOTTOTITOLI ---
            console.print("[6/6] 🎙️  Doppiaggio e Sottotitoli (Whisper)...")
            res_narrate = add_narration_core(current_video, script_data)
            if not res_narrate["success"]: raise Exception(f"Errore Narratore: {res_narrate['error']}")
            
            final_video = res_narrate["path"]
            console.print(f"[bold green]✅ VIDEO COMPLETATO: {final_video}[/bold green]")
            update_job_status(i, "done")
            
        except Exception as e:
            console.print(f"[bold red]❌ FALLIMENTO JOB #{i+1}: {str(e)}[/bold red]")
            update_job_status(i, "error", str(e))
            continue