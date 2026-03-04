from functools import wraps
from typing import List
from pathlib import Path
import typer
from ...shared.cli import Cli
from ...shared.vcard import generate_opml_from_vcards, VCardInputs

app = Cli(help="A CLI tool to the connections", no_args_is_help=True)


@app.command(help="Generate an OPML file from vCard files (files, directories)")
def feed(
    inputs: List[str] = typer.Argument(
        ..., help="Directories to retrieve the vCards (.vcf or .vcard files)"
    ),
    output: Path = typer.Option(None, "--output", "-o", help="Output OPML file"),
):
    vcard_inputs = VCardInputs(inputs)

    if len(vcard_inputs.vcard_files) == 0:
        typer.secho(
            f"❌ No vCard files found in the specified directory or files: {inputs}",
            fg=typer.colors.RED,
        )
        raise typer.Exit()

    opml = generate_opml_from_vcards(vcard_inputs.vcard_files)

    # Write the OPML to the output file
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(opml, encoding="utf-8")
        typer.secho(f"✅ OPML file generated: {output}")
    else:
        print(opml)


if __name__ == "__main__":
    app()
