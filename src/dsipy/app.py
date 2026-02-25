import os
import typer
from .apps.vcard import app as vcard_app
from .apps.feeds.app import app as feeds_app
from .apps.connections.app import app as connections_app
from .apps.key import app as key_app

main_app = typer.Typer(help="Main CLI application")

# Add the apps as a subcommands to the main app
main_app.add_typer(vcard_app, name="vcard", help="Commands related to vCard processing")
main_app.add_typer(feeds_app, name="feeds", help="Commands related to feeds processing")
main_app.add_typer(
    connections_app,
    name="connections",
    help="Commands related to connections processing",
)
main_app.add_typer(
    key_app,
    name="key",
    help="Commands related to keys",
)

if __name__ == "__main__":
    main_app()
