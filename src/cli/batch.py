import typer
from rich.console import Console
from src.core.batch import run_batch_process, load_jobs

app = typer.Typer()
console = Console()

@app.command()
def run():
    """
    Avvia la produzione automatica leggendo i lavori da 'jobs.json'.
    Esegue in sequenza: Scrittura AI -> Download -> Cut -> Resize -> Narrate.
    """
    run_batch_process()

@app.command()
def list():
    """
    Mostra lo stato dei lavori in jobs.json.
    """
    jobs = load_jobs()
    if not jobs:
        console.print("Nessun job trovato.")
        return

    from rich.table import Table
    table = Table(title="Coda di Produzione")
    table.add_column("ID", style="cyan")
    table.add_column("Stato", style="magenta")
    table.add_column("Topic", style="green")
    table.add_column("Video Source")

    for i, job in enumerate(jobs):
        status_color = "green" if job.get("status") == "done" else "red" if job.get("status") == "error" else "yellow"
        table.add_row(
            str(i+1), 
            f"[{status_color}]{job.get('status')}[/{status_color}]", 
            job.get("topic"), 
            os.path.basename(job.get("source", ""))[:30] + "..."
        )
    
    console.print(table)

if __name__ == "__main__":
    app()