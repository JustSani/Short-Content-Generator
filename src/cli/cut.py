import typer
import os
from rich.console import Console
from src.core.cutter import cut_video_interval_core
from src.utils.state import get_last_video, save_state

app = typer.Typer()
console = Console()

@app.command()
def interval(
    start: str = typer.Option(..., help="Tempo di inizio in formato mm:ss (es. 00:10)"),
    end: str = typer.Option(..., help="Tempo di fine in formato mm:ss (es. 01:30)"),
    file_path: str = typer.Argument(None, help="File da tagliare (opzionale se ne hai già scaricato uno)")
):
    """
    Taglia un video specificando inizio e fine (mm:ss).
    """
    
    # Logica recupero ultimo video
    target_file = file_path
    if not target_file:
        last = get_last_video()
        if last and os.path.exists(last):
            target_file = last
            console.print(f"[dim]Uso l'ultimo video: {os.path.basename(target_file)}[/dim]")
        else:
            console.print("[bold red]❌ Nessun file specificato e cronologia vuota.[/bold red]")
            raise typer.Exit(code=1)

    console.print(f"[bold blue]✂️  Taglio video da {start} a {end}...[/bold blue]")

    # Non serve lo spinner elaborato perché sarà velocissimo
    result = cut_video_interval_core(target_file, start, end)

    if result["success"]:
        console.print(f"[bold green]✅ Video tagliato![/bold green]")
        console.print(f"📁 Salvato in: [italic]{result['path']}[/italic]")
        
        # Aggiorniamo lo stato
        save_state("last_processed_video", result['path'])
        save_state("last_downloaded_video", result['path']) # Così il prossimo comando userà questo clip
    else:
        console.print(f"[bold red]❌ Errore:[/bold red] {result['error']}")

if __name__ == "__main__":
    app()