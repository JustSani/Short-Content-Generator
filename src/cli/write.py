import typer
from rich.console import Console
from src.core.writer import generate_script_core, save_script_to_file

app = typer.Typer()
console = Console()

@app.command()
def topic(
    topic_input: str = typer.Argument(..., help="L'argomento del video (es. 'Curiosità su Marte')")
):
    """
    Genera uno script virale con l'AI (Gemini) e lo salva in JSON.
    """
    console.print(f"[bold cyan]🧠 Chiedo a Gemini di scrivere su:[/bold cyan] {topic_input}...")
    
    result = generate_script_core(topic_input)
    
    if result["success"]:
        data = result["data"]
        
        # Anteprima a schermo
        console.print("\n[bold green]✅ Script Generato![/bold green]")
        console.rule("[bold yellow]TITOLO[/bold yellow]")
        console.print(f"[bold white]{data['title']}[/bold white]")
        console.rule("[bold yellow]TESTO[/bold yellow]")
        console.print(f"[italic]{data['text']}[/italic]\n")
        
        # Salvataggio
        path = save_script_to_file(topic_input, data)
        console.print(f"💾 Salvato in: [yellow]{path}[/yellow]")
        console.print("👉 Ora puoi usarlo con: [dim]python main.py narrate process -t QUESTO_FILE[/dim]")
        
    else:
        console.print(f"[bold red]❌ Errore AI:[/bold red] {result['error']}")

if __name__ == "__main__":
    app()