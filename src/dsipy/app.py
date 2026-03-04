import logging
import os
import typer
from .apps.vcard import app as vcard_app
from .apps.feeds.app import app as feeds_app
from .apps.connections.app import app as connections_app
from .apps.key import app as key_app

main_app = typer.Typer(
    help="DSI Tools: A collection of CLI tools for working with vCards, feeds, connections, and keys"
)

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


# If no subcommand is provided, show the help message
@main_app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())

    # Set up logging for the entire application context
    # ctx.logger = logging.getLogger(__name__)

    # ctx.logger.setLevel(logging.INFO)

    # # Avoid adding handlers multiple times if the logger is reused
    # if not ctx.logger.handlers:
    #     handler = logging.StreamHandler()
    #     handler.setLevel(logging.INFO)

    #     formatter = logging.Formatter(
    #         # "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    #         "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    #     )
    #     handler.setFormatter(formatter)

    #     ctx.logger.addHandler(handler)

    # ctx.obj = {"config_path": "config.toml", "verbose": True, "logger": ctx.logger}



if __name__ == "__main__":
    main_app()
