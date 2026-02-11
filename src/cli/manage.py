import typer
import os
from rich.console import Console
from src.utils.state import save_state, load_state

app = typer.Typer()
console = Console()

def clean_path_input(path: str) -> str:
    """Pulisce il percorso da virgolette e spazi."""
    return path.strip().strip('"').strip("'")

@app.command()
def set_downloaded(file_path: str):
    """
    Imposta manualmente il video 'Grezzo' (Last Downloaded).
    Utile se hai scaricato un file manualmente.
    """
    clean_path = clean_path_input(file_path)
    
    if not os.path.exists(clean_path):
        console.print(f"[bold red]❌ Errore:[/bold red] Il file non esiste: {clean_path}")
        raise typer.Exit(1)

    save_state("last_downloaded_video", clean_path)
    console.print(f"[green]✅ Stato aggiornato![/green] Video scaricato impostato su:\n[dim]{clean_path}[/dim]")

@app.command()
def set_processed(file_path: str):
    """
    Imposta manualmente il video 'Pronto' (Last Processed).
    Utile se vuoi applicare la narrazione a un file specifico già editato.
    """
    clean_path = clean_path_input(file_path)

    if not os.path.exists(clean_path):
        console.print(f"[bold red]❌ Errore:[/bold red] Il file non esiste: {clean_path}")
        raise typer.Exit(1)

    save_state("last_processed_video", clean_path)
    # Spesso se settiamo il processed, vogliamo che sia anche considerato l'ultimo "video attivo" in generale
    console.print(f"[green]✅ Stato aggiornato![/green] Video processato impostato su:\n[dim]{clean_path}[/dim]")

@app.command()
def set_all(file_path: str):
    """
    Imposta lo STESSO file sia come Scaricato che come Processato.
    Il "Reset Totale" per lavorare su un file nuovo immediatamente.
    """
    clean_path = clean_path_input(file_path)

    if not os.path.exists(clean_path):
        console.print(f"[bold red]❌ Errore:[/bold red] Il file non esiste: {clean_path}")
        raise typer.Exit(1)

    save_state("last_downloaded_video", clean_path)
    save_state("last_processed_video", clean_path)
    console.print(f"[bold green]✅ Tutto aggiornato![/bold green] Il file è ora il target principale per tutto:\n[dim]{clean_path}[/dim]")

@app.command()
def show():
    """Mostra lo stato attuale (quali file sono in memoria)."""
    state = load_state()
    console.print("\n[bold underline]📂 Stato Attuale:[/bold underline]")
    console.print(f"[blue]Scaricato:[/blue]  {state.get('last_downloaded_video', 'Nessuno')}")
    console.print(f"[magenta]Processato:[/magenta] {state.get('last_processed_video', 'Nessuno')}")
    console.print(f"[green]Completato:[/green] {state.get('last_completed_video', 'Nessuno')}")
    console.print(f"[yellow]Testo:[/yellow]       {state.get('current_text', '')[:50]}...")

if __name__ == "__main__":
    app()