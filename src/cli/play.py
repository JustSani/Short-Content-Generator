import typer
import os
from rich.console import Console
from src.utils.player import open_file_native
from src.utils.state import load_state

app = typer.Typer()
console = Console()

@app.command()
def start(
    file_path: str = typer.Argument(None, help="Percorso del file da aprire. Se vuoto, apre l'ultimo generato.")
):
    """
    Apre un video nel player predefinito di Windows.
    Se non specifichi il file, cerca l'ultimo video completato nel sistema.
    """
    
    target_file = file_path

    # Se l'utente non ha specificato un file, cerchiamo nella "memoria" del programma
    if not target_file:
        state = load_state()
        
        # Logica di priorità:
        # 1. Cerca l'ultimo video FINITO (con voce e sottotitoli)
        # 2. Se non c'è, cerca l'ultimo processato (tagliato/ridimensionato)
        # 3. Se non c'è, cerca l'ultimo scaricato (grezzo)
        
        possible_keys = ["last_completed_video", "last_processed_video", "last_downloaded_video"]
        
        for key in possible_keys:
            path = state.get(key)
            if path and os.path.exists(path):
                target_file = path
                console.print(f"[dim]Recuperato dallo stato ({key}): {os.path.basename(path)}[/dim]")
                break
    
    # Controllo finale
    if target_file and os.path.exists(target_file):
        console.print(f"[bold green]▶️  Apro il video:[/bold green] {target_file}")
        open_file_native(target_file)
    else:
        console.print("[bold red]❌ Nessun video trovato.[/bold red]")
        console.print("Non hai specificato un file e non c'è nulla nella cronologia recente.")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()