import os
import typer
from ...shared.vcard import generate_opml_from_vcards
from ...shared.file import write_file

app = typer.Typer(help="A CLI tool to the connections")


@app.command(help="Generate an OPML file from vCard files in a specified directory")
def feed(
    directory: str = typer.Argument(
        ..., help="Directory to retrieve the vCards (.vcf or .vcard files)"
    ),
    output: str = typer.Argument(None, help="Output OPML file"),
):
    if not os.path.isdir(directory):
        typer.secho(
            f"❌ The specified directory does not exist: {directory}",
            fg=typer.colors.RED,
        )
        raise typer.Exit()

    directory = os.path.abspath(directory)

    files = [
        os.path.join(root, f)
        for root, _, files in os.walk(directory)
        for f in files
        if f.endswith(".vcf") or f.endswith(".vcard")
    ]

    opml = generate_opml_from_vcards(files)

    # Write the OPML to the output file
    if output:
        write_file(opml, output)

        typer.secho(f"✅ OPML file generated: {output}")
    else:
        print(opml)


if __name__ == "__main__":
    app()
