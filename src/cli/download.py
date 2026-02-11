import typer
from rich.console import Console
from src.core.downloader import download_video_core
from src.utils.state import save_state  # <--- IMPORTA QUESTO

app = typer.Typer()
console = Console()

@app.command()
def youtube(url: str):
    """
    Scarica un video da YouTube data la URL.
    """
    console.print(f"[bold blue]Avvio download da:[/bold blue] {url}")

    with console.status("[bold green]Scaricamento in corso...[/bold green]", spinner="dots"):
        result = download_video_core(url)

    if result["success"]:
        console.print(f"[bold green]✅ Download completato![/bold green]")
        console.print(f"📁 Salvato in: [italic]{result['path']}[/italic]")
        console.print(f"🎬 Titolo: {result['title']}")
        
        # --- SALVATAGGIO STATO ---
        # Salviamo il percorso assoluto o relativo del file nel JSON
        save_state("last_downloaded_video", result['path'])
        console.print(f"[dim]💾 Percorso salvato in data/state.json per uso futuro[/dim]")
        # -------------------------

    else:
        console.print(f"[bold red]❌ Errore durante il download:[/bold red]")
        console.print(result["error"])

if __name__ == "__main__":
    app()