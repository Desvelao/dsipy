import os
import datetime
from email.utils import format_datetime
import typer
from functools import wraps
from .lib.utils import slugify
from .lib.markdown import (
    MarkdownFeed,
)
from ...shared.security import (
    load_private_key_pem,
    load_public_key_pem,
    public_key_to_b64der,
)

feed_types = {"markdown": MarkdownFeed}


def get_option_value(
    option_name: str,
    current_value: str | None,
    prompt_message: str,
    default_value: str,
    interactive: bool,
    throw_error: bool = True,
) -> str:
    """
    Get the value for an option, either from the current value or by prompting the user.
    """
    if not current_value:
        if interactive:
            return typer.prompt(
                prompt_message, default=default_value, show_default=True
            )
        else:
            typer.secho(
                f"❌ The {option_name} cannot be empty. Please provide a {option_name} using the --{option_name} option.",
                fg=typer.colors.RED,
            )
            raise typer.Exit()
    return current_value


app = typer.Typer(
    help="A CLI tool to generate RSS feeds from feed files",
)


def inject_settings(*settings):
    """
    A decorator to inject specific settings from the configuration file into the command.
    If a setting is not provided via the command arguments, it will be loaded from the configuration file.
    """

    def decorator(func):
        @wraps(func)  # Preserve the original function metadata
        def wrapper(*args, **kwargs):
            # Inject each requested setting
            for setting in settings:
                if setting not in kwargs or kwargs[setting] is None:
                    value = app.config.get(setting)
                    if value is None:
                        continue
                        # typer.secho(
                        #     f"❌ The '{setting}' parameter is not defined and cannot be loaded from the configuration file.",
                        #     fg=typer.colors.RED,
                        # )
                        # raise typer.Exit()
                    kwargs[setting] = value
            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.command()
def new(
    title: str = typer.Option("", "--title", "-t", help="Title for the new feed"),
    message: str = typer.Option(
        None, "--message", "-m", help="Content for the new feed item"
    ),
    filename: str = typer.Option(
        None, "--filename", "-f", help="Filename for the new feed"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive prompts"
    ),
    type: str = typer.Option(
        "markdown", "--type", help="Define the type of feed to create"
    ),
):

    feed_class = feed_types.get(type)

    if not feed_class:
        typer.secho(f"❌ Unsupported feed type: {type}", fg=typer.colors.RED)
        raise typer.Exit()

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    filename = get_option_value(
        "filename",
        filename,
        "Provide the filename for the new feed",
        slugify(now),
        interactive,
        False,
    )
    feed_path = os.path.join(f"{filename}")

    if os.path.exists(feed_path):
        typer.secho(
            f"❌ A feed directory with the name '{filename}' already exists. Please choose a different name.",
            fg=typer.colors.RED,
        )
        raise typer.Exit()

    title = get_option_value(
        "title",
        title,
        "Provide the title for the new feed",
        "My New Feed",
        interactive,
        False,
    )
    message = get_option_value(
        "message",
        message,
        "Provide the message for the new feed",
        "This is the content of my new feed item.",
        interactive,
    )

    file_content = feed_class.create_state(feed_path, title, message, now)

    typer.secho(f"Edit the file with a text editor: {feed_path}", fg=typer.colors.GREEN)


# @app.command()
def option_value_decorator(
    option_name: str, prompt_message: str, default_value: str, interactive: bool
):
    """
    A decorator to inject or validate an option value for a command.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_value = kwargs.get(option_name)
            if not current_value:
                if interactive:
                    kwargs[option_name] = typer.prompt(
                        prompt_message, default=default_value, show_default=True
                    )
                else:
                    typer.secho(
                        f"❌ The {option_name} cannot be empty. Please provide a {option_name} using the --{option_name} option.",
                        fg=typer.colors.RED,
                    )
                    raise typer.Exit()
            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.command()
@option_value_decorator(
    "title", "Provide the title for the RSS feed", "My RSS Feed", True
)
@option_value_decorator(
    "link", "Provide the base link for the RSS feed items", "https://example.com", True
)
@option_value_decorator(
    "description",
    "Provide the description for the RSS feed",
    "This is my RSS feed",
    True,
)
@option_value_decorator(
    "author", "Provide the author name for the RSS feed", "Author Name", True
)
@option_value_decorator(
    "email", "Provide the author email for the RSS feed", "author@email.com", True
)
def build(
    directory: str = typer.Argument(
        ..., help="Directory where the feed files are located"
    ),
    output: str = typer.Option("feed.rss", "--output", "-o", help="Output RSS file"),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit number of states to include in the feed"
    ),
    title: str = typer.Option(None, "--title", "-t", help="RSS feed title"),
    link: str = typer.Option(None, "--link", "-k", help="Base link for items"),
    description: str = typer.Option(
        None, "--description", "-d", help="RSS feed description"
    ),
    language: str = typer.Option(
        "en-US", "--language", "-g", help="Language of the feed"
    ),
    author: str = typer.Option(None, "--author", "-a", help="Author information"),
    email: str = typer.Option(None, "--email", "-e", help="Email of the author"),
    type: str = typer.Option("markdown", "--type", help="Define the type of states"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive prompts"
    ),
    signing_key_priv_file: str | None = typer.Option(
        None, "--sign-priv", help="Private key file to sign RSS items"
    ),
    signing_key_public_file: str | None = typer.Option(
        None, "--sign-pub", help="Public key file to verify RSS item signatures"
    ),
):

    feed_class = feed_types.get(type)

    if not feed_class:
        typer.secho(f"❌ Unsupported feed type: {type}", fg=typer.colors.RED)
        raise typer.Exit()

    states = feed_class.collect(directory)

    if limit:
        states = states[:limit]

    link = get_option_value(
        "link",
        link,
        "Provide the base link for the RSS feed items",
        "https://example.com",
        interactive,
    )
    description = get_option_value(
        "description",
        description,
        "Provide the description for the RSS feed",
        "This is my RSS feed",
        interactive,
    )
    author = get_option_value(
        "author",
        author,
        "Provide the author name for the RSS feed",
        "Author Name",
        interactive,
    )
    email = get_option_value(
        "email",
        email,
        "Provide the author email for the RSS feed",
        "author@email.com",
        interactive,
    )
    signing_key_priv_file = get_option_value(
        "sign-priv",
        signing_key_priv_file,
        "Provide the signing key file to sign the RSS feed items",
        None,
        interactive,
        False,
    )
    signing_key_public_file = get_option_value(
        "sign-public",
        signing_key_public_file,
        "Provide the signing key file to sign the RSS feed items",
        None,
        interactive,
        False,
    )

    if signing_key_priv_file:
        signing_key_priv_file = os.path.join(signing_key_priv_file)
        if not os.path.isfile(signing_key_priv_file):
            typer.secho(
                f"❌ The private signing key file '{signing_key_priv_file}' does not exist or is not a file.",
                fg=typer.colors.RED,
            )
            raise typer.Exit()

    if signing_key_public_file:
        signing_key_public_file = os.path.join(signing_key_public_file)
        if not os.path.isfile(signing_key_public_file):
            typer.secho(
                f"❌ The public signing key file '{signing_key_public_file}' does not exist or is not a file.",
                fg=typer.colors.RED,
            )
            raise typer.Exit()

    states = feed_class.collect(directory)

    if limit:
        states = states[:limit]

    sign = None

    if signing_key_priv_file and signing_key_public_file:
        sign = {
            "key": load_private_key_pem(open(signing_key_priv_file, "rb").read()),
            "id": public_key_to_b64der(
                load_public_key_pem(open(signing_key_public_file, "rb").read())
            ),
        }

    feed_class.build(
        states, title, link, description, author, email, language, output, sign
    )

    typer.secho(f"✅ RSS feed generated: {output}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
