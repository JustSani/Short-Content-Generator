import typer
import json
import os
from rich.console import Console

# Import moduli CLI
from src.cli import download, resize, cut, narrate, play, manage,write, batch, reddit

# Import funzioni CORE
from src.core.downloader import download_video_core
from src.core.cutter import cut_video_interval_core
from src.core.resizer import convert_to_vertical_core
from src.core.narrator import add_narration_core
from src.utils.state import save_state
from src.utils.player import open_file_native


app = typer.Typer(help="Content Automator CLI - Automazione contenuti 2026")
console = Console()

# Registrazione sottomoduli
app.add_typer(download.app, name="download", help="Scarica video")
app.add_typer(resize.app, name="resize", help="Ridimensiona video")
app.add_typer(cut.app, name="cut", help="Taglia video")
app.add_typer(narrate.app, name="narrate", help="Voce IA e Sottotitoli")
app.add_typer(play.app, name="play", help="Riproduci video")
app.add_typer(manage.app, name="manage", help="Gestione manuale dello stato")
app.add_typer(write.app, name="write", help="Genera script con AI")
app.add_typer(batch.app, name="batch", help="Gestione coda automatica (Factory Mode)")

@app.command()
def create(
    source: str = typer.Argument(..., help="URL YouTube O percorso file locale"),
    start: str = typer.Option(None, "--start", "-s", help="Tempo inizio (es. 00:00:10). Se omesso, salta il taglio."),
    end: str = typer.Option(None, "--end", "-e", help="Tempo fine (es. 00:00:20). Se omesso, salta il taglio."),
    vertical: bool = typer.Option(True, "--vertical/--no-vertical", help="Converti in 9:16? Default: Sì."),
    text_input: str = typer.Option(None, "--text", "-t", help="Testo o file .txt. Se omesso, salta la narrazione."),
    play_result: bool = typer.Option(False, "--play", "-p", help="Riproduci alla fine")
):
    """
    🚀 PIPELINE MODULARE:
    - Se passi un URL -> Scarica.
    - Se passi un FILE -> Usa quello.
    - Se passi i TEMPI -> Taglia.
    - Se passi il TESTO -> Narra.
    """
    
    console.rule("[bold red]PIPELINE DI CREAZIONE[/bold red]")
    
    current_file = ""

    # --- STEP 1: ACQUISIZIONE (Download o Locale) ---
    clean_source = source.strip('"').strip("'")
    
    if clean_source.startswith("http"):
        console.print(f"\n[1/4] [bold blue]⬇️  Rilevato URL, avvio download...[/bold blue]")
        res_dl = download_video_core(clean_source)
        if not res_dl["success"]:
            console.print(f"[bold red]❌ Errore Download:[/bold red] {res_dl['error']}")
            raise typer.Exit(1)
        current_file = res_dl["path"]
        save_state("last_downloaded_video", current_file)
    else:
        if os.path.exists(clean_source):
            console.print(f"\n[1/4] [bold green]📂 Rilevato file locale, salto download.[/bold green]")
            current_file = clean_source
            save_state("last_downloaded_video", current_file) # Aggiorniamo lo stato per coerenza
        else:
            console.print(f"[bold red]❌ Errore:[/bold red] Il file locale non esiste: {clean_source}")
            raise typer.Exit(1)

    # --- STEP 2: TAGLIO (Condizionale) ---
    if start and end:
        console.print(f"\n[2/4] [bold yellow]✂️  Taglio clip ({start} - {end})...[/bold yellow]")
        res_cut = cut_video_interval_core(current_file, start, end)
        if not res_cut["success"]:
            console.print(f"[bold red]❌ Errore Taglio:[/bold red] {res_cut['error']}")
            raise typer.Exit(1)
        current_file = res_cut["path"]
    else:
        console.print(f"\n[2/4] [dim]⏩ Nessun tempo specificato, salto il taglio.[/dim]")

    # --- STEP 3: RESIZE (Condizionale) ---
    if vertical:
        console.print(f"\n[3/4] [bold magenta]📱 Conversione in 9:16...[/bold magenta]")
        res_resize = convert_to_vertical_core(current_file)
        if not res_resize["success"]:
            console.print(f"[bold red]❌ Errore Resize:[/bold red] {res_resize['error']}")
            raise typer.Exit(1)
        current_file = res_resize["path"]
        save_state("last_processed_video", current_file)
    else:
        console.print(f"\n[3/4] [dim]⏩ Opzione --no-vertical attiva, salto il resize.[/dim]")

    # --- STEP 4: GESTIONE TESTO e TITOLO  ---
    story_data = {"title": "", "text": ""}
    clean_text_input = text_input.strip('"').strip("'") if text_input else ""
    
    if clean_text_input:
        if os.path.exists(clean_text_input) and os.path.isfile(clean_text_input):
            if clean_text_input.endswith('.json'):
                console.print(f"[dim]📂 Leggo la storia strutturata dal JSON: {clean_text_input}[/dim]")
                try:
                    with open(clean_text_input, "r", encoding="utf-8") as f:
                        story_data = json.load(f)
                except Exception as e:
                    console.print(f"[bold red]❌ Errore lettura JSON:[/bold red] {e}")
                    raise typer.Exit(1)
            else:
                # Fallback per vecchi file .txt
                with open(clean_text_input, "r", encoding="utf-8") as f:
                    story_data["text"] = f.read()
        else:
            # Fallback se scrivi la frase a mano
            story_data["text"] = clean_text_input

    if not story_data["text"]:
        console.print("[bold red]❌ Errore:[/bold red] Il testo principale è vuoto.")
        raise typer.Exit(1)

    # --- STEP 5: NARRAZIONE (Condizionale) ---
    if text_input:
        console.print(f"\n[4/4] [bold cyan]🎙️  Aggiunta Voce e Sottotitoli...[/bold cyan]")
        
        story_data = {"title": "", "text": ""}
        clean_text_path = text_input.strip('"').strip("'")
        
        if os.path.exists(clean_text_path) and os.path.isfile(clean_text_path):
            # Se è un file JSON, lo leggiamo come dizionario
            if clean_text_path.endswith('.json'):
                try:
                    with open(clean_text_path, "r", encoding="utf-8") as f:
                        story_data = json.load(f)
                except json.JSONDecodeError:
                    console.print(f"[bold red]❌ Errore:[/bold red] Il file {clean_text_path} non è un JSON valido.")
                    raise typer.Exit(1)
            else:
                # Se è un vecchio file .txt, mettiamo tutto nel "text"
                with open(clean_text_path, "r", encoding="utf-8") as f:
                    story_data["text"] = f.read()
        else:
            # Se hai scritto la frase direttamente da terminale
            story_data["text"] = clean_text_path

        # IMPORTANTE: Passiamo story_data (Dizionario), non final_text (Stringa)
        res_narrate = add_narration_core(current_file, story_data)
        
        if not res_narrate["success"]:
            console.print(f"[bold red]❌ Errore Narrazione:[/bold red] {res_narrate['error']}")
            raise typer.Exit(1)
            
        current_file = res_narrate["path"]
        save_state("last_completed_video", current_file)
    else:
        console.print(f"\n[4/4] [dim]⏩ Nessun testo specificato, salto la narrazione.[/dim]")

    # --- CONCLUSIONE ---
    console.rule("[bold green]✅ COMPLETATO[/bold green]")
    console.print(f"🎬 File Finale: [yellow]{current_file}[/yellow]")

    if play_result:
        console.print("[dim]▶️ Avvio player...[/dim]")
        open_file_native(current_file)

if __name__ == "__main__":
    app()