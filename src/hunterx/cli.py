from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hunterx.config import Settings
from hunterx.models import ATSScore, Job, OptimizationRound

app = typer.Typer(
    name="hunterx",
    help="ATS resume optimizer powered by Kimi",
    add_completion=False,
)
console = Console()


def _get_settings(**overrides) -> Settings:
    filtered = {k: v for k, v in overrides.items() if v is not None}
    return Settings(**filtered)


def _display_score_table(score: ATSScore, title: str = "ATS Score Breakdown") -> None:
    table = Table(title=title, show_header=True)
    table.add_column("Dimension", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Weight", justify="right")
    table.add_column("Weighted", justify="right")
    table.add_column("Status")

    for dim in score.dimensions:
        status = "[green]PASS[/green]" if dim.score >= 80 else "[red]NEEDS WORK[/red]"
        table.add_row(
            dim.name,
            f"{dim.score:.0f}",
            f"{dim.weight:.0%}",
            f"{dim.weighted_score:.1f}",
            status,
        )

    table.add_section()
    total = score.total_score
    color = "green" if total >= 95 else "yellow" if total >= 80 else "red"
    table.add_row("TOTAL", f"[bold {color}]{total:.1f}[/bold {color}]", "", "", "")

    console.print(table)
    console.print(f"\n{score.overall_assessment}\n")


@app.command("dump")
def dump_jd(
    url: str = typer.Argument(..., help="URL of a job posting to scrape"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Fetch a job posting URL and extract the description as text."""
    from hunterx.scraper import fetch_job_description

    with console.status(f"Fetching {url}..."):
        text = fetch_job_description(url)

    if not text.strip():
        console.print("[red]Error: Could not extract job description from URL.[/red]")
        raise typer.Exit(1)

    if output is None:
        jd_dir = Path("output/jds")
        jd_dir.mkdir(parents=True, exist_ok=True)
        parsed = urlparse(url)
        slug = parsed.path.strip("/").replace("/", "_")
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in slug)[:80] or "job"
        output = jd_dir / f"{safe}.txt"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text)

    console.print(f"[green]Saved job description to:[/green] {output}")
    console.print(f"[dim]({len(text)} characters extracted)[/dim]")


_DEFAULT_RESUME = Path("orig/resume3.md")


@app.command("optimize")
def optimize_resume(
    resume: Optional[Path] = typer.Argument(None, help="Path to base resume markdown file"),
    jd_file: Path = typer.Option(..., "--jd", help="Path to job description text file", exists=True),
    rounds: Optional[int] = typer.Option(None, "--rounds", "-r", help="Number of optimization rounds"),
    target: Optional[int] = typer.Option(None, "--target", "-t", help="Target ATS score (0-100)"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Kimi model to use"),
) -> None:
    """Optimize a resume for a specific job description."""
    if resume is None:
        resume = _DEFAULT_RESUME
    if not resume.exists():
        console.print(f"[red]Error: Resume file not found: {resume}[/red]")
        raise typer.Exit(1)

    settings = _get_settings(
        optimization_rounds=rounds,
        target_score=target,
        output_dir=output_dir,
        kimi_model=model,
    )

    base_resume = resume.read_text()
    jd_text = jd_file.read_text()
    job = Job(description=jd_text)

    console.print(Panel(f"[bold]Optimizing resume against JD[/bold]\n{jd_file}", title="Target Job"))

    from hunterx.optimizer.engine import OptimizationEngine

    def on_round_complete(r: OptimizationRound) -> None:
        console.print(f"\n[bold]Round {r.round_number}[/bold] complete")
        _display_score_table(r.score, title=f"Round {r.round_number} Score")

    engine = OptimizationEngine(settings, on_round_complete=on_round_complete)

    console.print(
        f"\nStarting optimization ({settings.optimization_rounds} rounds, "
        f"target: {settings.target_score})...\n"
    )
    result = engine.optimize(base_resume, job)

    out_dir = settings.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_title = jd_file.stem[:50].strip() or "optimized"
    out_file = out_dir / f"{safe_title}_optimized.md"
    score_file = out_dir / f"{safe_title}_score.json"

    out_file.write_text(result.optimized_resume)
    score_file.write_text(result.final_score.model_dump_json(indent=2))

    console.print(
        Panel(
            f"Resume saved to: [bold]{out_file}[/bold]\n"
            f"Score saved to: [bold]{score_file}[/bold]",
            title="[green]Optimization Complete[/green]",
        )
    )

    _display_score_table(result.final_score, title="Final ATS Score")


@app.command("cover")
def cover_letter(
    jd_file: Path = typer.Option(..., "--jd", help="Path to job description text file", exists=True),
    resume: Path = typer.Option(_DEFAULT_RESUME, "--rs", help="Path to resume markdown file"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Kimi model to use"),
) -> None:
    """Generate a cover letter based on your resume and a job description."""
    if not resume.exists():
        console.print(f"[red]Error: Resume file not found: {resume}[/red]")
        raise typer.Exit(1)

    settings = _get_settings(kimi_model=model)

    resume_text = resume.read_text()
    jd_text = jd_file.read_text()

    from hunterx.optimizer.engine import OptimizationEngine

    engine = OptimizationEngine(settings)

    with console.status("Generating cover letter..."):
        letter = engine.generate_cover_letter(resume_text, jd_text)

    out_dir = settings.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_title = jd_file.stem[:50].strip() or "cover"
    out_file = out_dir / f"{safe_title}_cover_letter.md"
    out_file.write_text(letter)

    console.print(
        Panel(
            f"Cover letter saved to: [bold]{out_file}[/bold]",
            title="[green]Cover Letter Complete[/green]",
        )
    )

    console.print()
    console.print(letter)


@app.command("eval")
def eval_resume(
    resume: Path = typer.Argument(..., help="Path to resume markdown file", exists=True),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Kimi model to use"),
) -> None:
    """Evaluate a resume's general ATS readiness without a job description."""
    settings = _get_settings(kimi_model=model)
    from hunterx.optimizer.scorer import ATSScorer

    resume_text = resume.read_text()

    with console.status("Evaluating resume..."):
        scorer = ATSScorer(settings)
        score = scorer.evaluate(resume_text)

    out_dir = settings.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_title = resume.stem[:50].strip() or "eval"
    score_file = out_dir / f"{safe_title}_eval.json"
    score_file.write_text(score.model_dump_json(indent=2))

    console.print(
        Panel(
            f"Score saved to: [bold]{score_file}[/bold]",
            title="[green]Evaluation Complete[/green]",
        )
    )

    _display_score_table(score, title="ATS Evaluation Score")

    for dim in score.dimensions:
        if dim.findings:
            console.print(f"\n[bold]{dim.name} Findings:[/bold]")
            for f in dim.findings:
                console.print(f"  - {f}")
        if dim.suggestions:
            console.print(f"[yellow]{dim.name} Suggestions:[/yellow]")
            for s in dim.suggestions:
                console.print(f"  - {s}")


@app.command("score")
def score_resume(
    resume: Path = typer.Argument(..., help="Path to resume markdown file", exists=True),
    jd_file: Path = typer.Option(..., "--jd", help="Path to job description text file", exists=True),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Kimi model to use"),
) -> None:
    """Score a resume against a job description without optimizing."""
    settings = _get_settings(kimi_model=model)
    from hunterx.optimizer.scorer import ATSScorer

    resume_text = resume.read_text()
    jd_text = jd_file.read_text()

    with console.status("Scoring resume..."):
        scorer = ATSScorer(settings)
        score = scorer.score(resume_text, jd_text)

    _display_score_table(score)

    for dim in score.dimensions:
        if dim.findings:
            console.print(f"\n[bold]{dim.name} Findings:[/bold]")
            for f in dim.findings:
                console.print(f"  - {f}")
        if dim.suggestions:
            console.print(f"[yellow]{dim.name} Suggestions:[/yellow]")
            for s in dim.suggestions:
                console.print(f"  - {s}")
