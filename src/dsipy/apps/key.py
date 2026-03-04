from pathlib import Path
import sys
import typer
from ..shared.cli import Cli
from ..shared.security import (
    action_generate_keypair,
    load_public_key_pem,
    public_key_to_b64der,
    b64der_to_public_key,
)

app = Cli(
    help="A CLI tool to generate RSS feeds from markdown files", no_args_is_help=True
)


@app.command(help="Generate a new Ed25519 keypair and save to PEM files")
def create(
    priv: Path = typer.Option(
        "private.pem", "--priv", help="Path to save the private key PEM file"
    ),
    pub: Path = typer.Option(
        "public.pem", "--pub", help="Path to save the public key PEM file"
    ),
):
    action_generate_keypair(priv, pub)


@app.command(
    help="Convert a public key PEM file to Base64-encoded DER format for vCard use"
)
def pub_encode(
    file: Path = typer.Argument(..., help="Path to the public key PEM file to convert")
):
    if not file.is_file():
        typer.secho(f"❌ '{file}' is not a file.", fg=typer.colors.RED)
        raise typer.Exit()

    b64der_text = public_key_to_b64der(load_public_key_pem(file.read_bytes()))

    print(b64der_text)


@app.command(
    help="Convert a Base64-encoded DER format for vCard use to public key PEM file"
)
def pub_decode(
    content: str = typer.Argument(
        None, help="Base64-encoded DER content to decode and display as PEM"
    ),
):
    if content is None:
        content = sys.stdin.read().strip()

    if not content:
        typer.secho("❌ No content provided.", fg=typer.colors.RED)
        raise typer.Exit()

    print(b64der_to_public_key(content))

# @app.command()
# def priv_decode(
#     content: str = typer.Argument(
#         None, help="Base64-encoded DER content to decode and display as PEM"
#     ),
# ):
#     if content is None:
#         content = sys.stdin.read().strip()

#     if not content:
#         typer.secho("❌ No content provided.", fg=typer.colors.RED)
#         raise typer.Exit()

#     print(b64der_to_private_key(content))


if __name__ == "__main__":
    app()
