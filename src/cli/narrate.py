import typer
import os
from rich.console import Console
from src.core.narrator import add_narration_core
from src.utils.state import load_state, save_state
from src.utils.player import open_file_native

app = typer.Typer()
console = Console()

@app.command()
def process(
    file_path: str = typer.Argument(None, help="Percorso video. Se vuoto usa l'ultimo processato."),
    text_input: str = typer.Option(..., "--text", "-t", help="Testo, frase, o percorso file .json/.txt"),
    play_result: bool = typer.Option(False, "--play", "-p", help="Avvia il video automaticamente al termine")
):
    """
    Aggiunge voce IA e sottotitoli a un video esistente.
    Legge il testo direttamente dall'input o da un file .json/.txt
    """
    
    # 1. Recupero Video Target
    target_file = file_path
    if not target_file:
        state = load_state()
        # Diamo priorità al video già ridimensionato/processato
        target_file = state.get("last_processed_video") or state.get("last_downloaded_video")
        
    if not target_file or not os.path.exists(target_file):
        console.print("[bold red]❌ Errore:[/bold red] Nessun video trovato nella cronologia.")
        console.print("Passa il percorso del video come argomento, oppure usa prima il comando 'manage set-processed'.")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]🎙️  Generazione voce e sottotitoli per:[/bold blue] {os.path.basename(target_file)}")
    
    # 2. Esecuzione (Il core capirà da solo se text_input è un JSON, un TXT o una frase)
    with console.status("[bold green]Rendering finale in corso (può richiedere un minuto)...[/bold green]"):
        result = add_narration_core(target_file, text_input)

    # 3. Risultato
    if result["success"]:
        console.print(f"[bold green]✅ Video Completato![/bold green]")
        console.print(f"🎬 Output finale: [yellow]{result['path']}[/yellow]")
        save_state("last_completed_video", result['path'])
        
        if play_result:
            console.print("[dim]▶️ Avvio riproduzione...[/dim]")
            open_file_native(result['path'])
            
    else:
        console.print(f"[bold red]❌ Errore:[/bold red] {result['error']}")

if __name__ == "__main__":
    app()