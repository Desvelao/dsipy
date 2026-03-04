from functools import wraps
import typer
import traceback
import logging


def cmd_error_handler(message: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if e.__class__ is typer.Exit:
                    raise
                typer.secho(f"❌ {message}: {str(e)}", fg=typer.colors.RED)
                # traceback.print_exc() # TODO: remove
                raise typer.Exit()

        return wrapper

    return decorator

class Cli(typer.Typer):
    """Custom Typer application that automatically wraps all commands with a generic error handler."""

    def __init__(self, *args, logger: logging.Logger = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger or logging.getLogger(__name__)

    def command(self, *args, **kwargs):
        """Override the command decorator to wrap all commands with a generic error handler."""
        original_decorator = super().command(*args, **kwargs)

        def decorator(func):
            wrapped_func = cmd_error_handler(f"Command '{func.__name__}' failed")(func)
            return original_decorator(wrapped_func)

        return decorator
    
