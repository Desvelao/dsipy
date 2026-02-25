import os
import typer
from ..shared.security import (
    action_generate_keypair,
    load_public_key_pem,
    public_key_to_b64der,
    b64der_to_public_key,
)

app = typer.Typer(
    help="A CLI tool to generate RSS feeds from markdown files",
)


@app.command(help="Generate a new Ed25519 keypair and save to PEM files")
def create(
    priv: str = typer.Option(
        "private.pem", "--priv", help="Path to save the private key PEM file"
    ),
    pub: str = typer.Option(
        "public.pem", "--pub", help="Path to save the public key PEM file"
    ),
):
    action_generate_keypair(priv, pub)


@app.command(
    help="Convert a public key PEM file to Base64-encoded DER format for vCard use"
)
def encode(
    file: str = typer.Argument(..., help="Path to the public key PEM file to convert")
):
    if not os.path.exists(file):
        typer.secho(f"❌ File '{file}' does not exist.", fg=typer.colors.RED)
        raise typer.Exit()

    if not os.path.isfile(file):
        typer.secho(f"❌ '{file}' is not a file.", fg=typer.colors.RED)
        raise typer.Exit()

    b64der_text = public_key_to_b64der(load_public_key_pem(open(file, "rb").read()))

    print(b64der_text)


@app.command(
    help="Convert a public key PEM file to Base64-encoded DER format for vCard use"
)
def decode(
    content: str = typer.Argument(
        ..., help="Base64-encoded DER content to decode and display as PEM"
    )
):
    print(b64der_to_public_key(content))


if __name__ == "__main__":
    app()
