import datetime
import difflib
from functools import wraps
import os
from pathlib import Path
from rich.progress import Progress
from rich.syntax import Syntax
import typer
from typing import List
from .lib.feed import RSSFeed
from .lib.markdown import get_feed_class
from ...shared.cli import Cli
from ...shared.publish import get_publisher
from ...shared.security import (
    load_private_key_pem,
    load_public_key_pem,
    public_key_to_b64der,
)
from ...shared.utils import slugify


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


app = Cli(help="A CLI tool to generate RSS feeds from feed files", no_args_is_help=True)


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
        False, "--interactive", "-i", help="Interactive prompts", is_flag=True
    ),
    feed_type: str = typer.Option(
        "markdown", "--type", help="Define the type of feed to create"
    ),
):

    feed_class = get_feed_class(feed_type)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # TODO: review usage of option_value_decorator vs get_option_value for consistency and flexibility
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
            f"❌ A feed file with the name '{filename}' already exists. Please choose a different name.",
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

    feed_class.create_state(feed_path, title, message, now)

    typer.secho(f"ℹ️  Edit the file with a text editor: {feed_path}")


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
    output: Path = typer.Option("feed.rss", "--output", "-o", help="Output RSS file"),
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
    feed_type: str = typer.Option(
        "markdown", "--type", help="Define the type of states"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive prompts", is_flag=True
    ),
    signing_key_priv_file: str | None = typer.Option(
        None, "--sign-priv", help="Private key file to sign RSS items"
    ),
    signing_key_public_file: str | None = typer.Option(
        None, "--sign-pub", help="Public key file to verify RSS item signatures"
    ),
    var: List[str] = typer.Option(
        None, "--var", help="Template variables as key=value pairs"
    ),
    var_file: Path = typer.Option(
        None, "--var-file", help="File with template variables (one KEY=VALUE per line)"
    )
):

    feed_class = get_feed_class(feed_type)

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

    sign = None

    if signing_key_priv_file and signing_key_public_file:
        priv_key_data = None
        pub_key_data = None

        if os.path.isfile(signing_key_priv_file):
            priv_key_data = Path(signing_key_priv_file).read_bytes()
        else:
            priv_key_data = signing_key_priv_file.encode()

        if os.path.isfile(signing_key_public_file):
            pub_key_data = Path(signing_key_public_file).read_bytes()
        else:
            pub_key_data = signing_key_public_file.encode()
            
        if priv_key_data and pub_key_data:
            sign = {
                "key": load_private_key_pem(priv_key_data),
                "id": public_key_to_b64der(load_public_key_pem(pub_key_data)),
            }

    # Parse var arguments into a dictionary
    vars_dict = {}
    # Parse var-file if provided
    if var_file:
        if var_file.exists():
            for line in var_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    vars_dict[key.strip()] = value.strip()
        else:
            typer.secho(
                f"❌ Variable file not found: {var_file}",
                fg=typer.colors.RED,
            )
            raise typer.Exit()
    
    # Parse var arguments
    if var:
        for arg in var:
            key, value = arg.split("=", 1)
            vars_dict[key] = value

    states = feed_class.collect(directory)

    if limit:
        states = states[:limit]    

    # Simple templating for content using metadata values (e.g. {{ title }}, {{ date }}, etc.)
    for state in states:
        if state.get("title"):
            state["title"] = RSSFeed.replace_template_variables(state["title"], state["metadata"], vars_dict)

        if state.get("id"):
            state["id"] = RSSFeed.replace_template_variables(state["id"], state["metadata"], vars_dict)

        if state.get("link"):
            state["link"] = RSSFeed.replace_template_variables(state["link"], state["metadata"], vars_dict)

        if state.get("image"):
            state["image"] = RSSFeed.replace_template_variables(state["image"], state["metadata"], vars_dict)

        if state.get("content"):
            state["content"] = RSSFeed.replace_template_variables(state["content"], state["metadata"], vars_dict)
            # Allow HTML in RSS description
            if state.get("content_type") == "html":
                state["content"] = f"<![CDATA[{state['content']}]]>"

    build_date = datetime.datetime.now()
    # TODO: consider adding more feed formats (e.g. JSON Feed) and allowing users to choose the output format
    feed_content = RSSFeed.build(
        title, link, description, author, email, language, build_date, states, sign
    )

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(feed_content, encoding="utf-8")
        typer.secho(f"✅ RSS feed generated: {output}", fg=typer.colors.GREEN)
    else:
        print(feed_content)


def iter_feed_files(paths: List[Path]):
    exts = {".xml", ".json", ".atom", ".rss"}
    for p in paths:
        if p.is_file() and p.suffix.lower() in exts:
            yield p
        elif p.is_dir():
            for file in p.rglob("*"):
                if file.suffix.lower() in exts:
                    yield file


@app.command("publish")
def publish(
    inputs: List[Path] = typer.Argument(...),
    provider: str = typer.Option(
        ..., "--provider", help="Provider: github, s3, webdav, local"
    ),
    prefix: str = typer.Option("", "--prefix", help="Path prefix on provider"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    show_diff: bool = typer.Option(False, "--diff"),
    provider_args: List[str] = typer.Option(
        None,
        "--arg",
        help="Provider-specific arguments: key=value",
    ),
):
    """
    Publish feeds to multiple providers (GitHub, S3, WebDAV, local).
    """

    # Parse provider args
    kwargs = {}
    if provider_args:
        for arg in provider_args:
            key, value = arg.split("=", 1)
            kwargs[key] = value

    prov = get_publisher(provider, **kwargs)

    feed_files = list(iter_feed_files(inputs))
    if not feed_files:
        typer.secho(
            f"❌ No feed files found in the specified paths: {inputs}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    published = 0
    unchanged = 0
    failed = 0

    with Progress() as progress:
        task = progress.add_task("Publishing feeds...", total=len(feed_files))

        for file in feed_files:
            rel_path = f"{prefix}{file.name}" if prefix else file.name
            progress.console.print(f"[bold]Publishing:[/bold] {file} → {rel_path}")

            local_text = file.read_text()

            try:
                remote_text, version = prov.get_remote(rel_path)
            except Exception as e:
                progress.console.print(f"[red]  Failed to fetch remote: {e}[/red]")
                failed += 1
                progress.update(task, advance=1)
                continue

            # Diff
            if show_diff and remote_text is not None:
                diff = "\n".join(
                    difflib.unified_diff(
                        remote_text.splitlines(),
                        local_text.splitlines(),
                        fromfile="(remote)",
                        tofile=str(file),
                        lineterm="",
                    )
                )
                if diff.strip():
                    syntax = Syntax(diff, "diff", theme="ansi_dark")
                    progress.console.print(syntax)
                else:
                    progress.console.print("[green]  No differences.[/green]")

            # Skip if unchanged
            if remote_text == local_text:
                progress.console.print("[green]  Unchanged.[/green]")
                unchanged += 1
                progress.update(task, advance=1)
                continue

            if dry_run:
                progress.console.print("[cyan]  Dry-run: no changes written.[/cyan]")
                published += 1
                progress.update(task, advance=1)
                continue

            try:
                prov.publish(rel_path, local_text, version)
                progress.console.print(f"[green]  Published:[/green] {rel_path}")
                published += 1
            except Exception as e:
                progress.console.print(f"[red]  Failed to publish: {e}[/red]")
                failed += 1

            progress.update(task, advance=1)

    typer.secho("Summary:", bold=True)
    typer.secho(f"  Published:  {published}", fg=typer.colors.GREEN)
    typer.secho(f"  Unchanged:   {unchanged}", fg=typer.colors.CYAN)
    typer.secho(f"  Failed:      {failed}", fg=typer.colors.RED)
    typer.secho("Done.")


if __name__ == "__main__":
    app()
