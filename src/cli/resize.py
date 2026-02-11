import typer
import os
from rich.console import Console
from src.core.resizer import convert_to_vertical_core
from src.utils.state import get_last_video, save_state

app = typer.Typer()
console = Console()

@app.command()
def vertical(file_path: str = typer.Argument(None, help="Percorso del video da ritagliare. Se vuoto, usa l'ultimo scaricato.")):
    """
    Trasforma un video in formato 9:16 (Verticale) tramite ritaglio centrale.
    """
    
    # Se l'utente non passa un file, cerchiamo nello state.json
    target_file = file_path
    if not target_file:
        console.print("[yellow]⚠️  Nessun file specificato. Cerco l'ultimo video scaricato...[/yellow]")
        last_video = get_last_video()
        
        if last_video and os.path.exists(last_video):
            target_file = last_video
            console.print(f"[dim]Trovato: {target_file}[/dim]")
        else:
            console.print("[bold red]❌ Nessun video trovato nella cronologia. Specifica un percorso file.[/bold red]")
            raise typer.Exit(code=1)

    console.print(f"[bold blue]✂️  Avvio ritaglio verticale per:[/bold blue] {os.path.basename(target_file)}")

    # Avvio processo (MoviePy può essere lento, mostriamo uno spinner)
    with console.status("[bold green]Elaborazione video in corso (questo potrebbe richiedere tempo)...[/bold green]", spinner="clock"):
        result = convert_to_vertical_core(target_file)

    if result["success"]:
        console.print(f"[bold green]✅ Video ritagliato con successo![/bold green]")
        console.print(f"📁 Salvato in: [italic]{result['path']}[/italic]")
        
        # Aggiorniamo lo stato: il "nuovo ultimo video" è ora quello editato
        save_state("last_processed_video", result['path'])
        # Sovrascriviamo anche last_downloaded per permettere un editing a catena (es. sottotitoli successivi)
        save_state("last_downloaded_video", result['path']) 
        
    else:
        console.print(f"[bold red]❌ Errore durante il ritaglio:[/bold red]")
        console.print(result["error"])

if __name__ == "__main__":
    app()