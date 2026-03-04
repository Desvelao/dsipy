from datetime import datetime
import difflib
import os
from pathlib import Path
from rich.progress import Progress
from rich.syntax import Syntax
import sys
import typer
from typing import List
from ..shared.cli import Cli
from ..shared.qr import generate_qr
from ..shared.security import (
    action_generate_keypair,
    load_private_key_pem,
)
from ..shared.vcard import VCard, VCardInputs, vcard_main_attributes

app = Cli(
    help="A CLI tool to generate RSS feeds from markdown files", no_args_is_help=True
)


@app.command()
def create(
    output: Path = typer.Option(
        Path("dsi-card.vcf"), "--output", "-o", help="Output file to save the vCard"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive prompts", is_flag=True
    ),
    fn: str = typer.Option(
        vcard_main_attributes["fn"]["default"],
        help=vcard_main_attributes["fn"]["description"],
    ),
    n: str = typer.Option(
        vcard_main_attributes["n"]["default"],
        help=vcard_main_attributes["n"]["description"],
    ),
    nickname: str = typer.Option(
        vcard_main_attributes["nickname"]["default"],
        help=vcard_main_attributes["nickname"]["description"],
    ),
    lang: str = typer.Option(
        vcard_main_attributes["lang"]["default"],
        help=vcard_main_attributes["lang"]["description"],
    ),
    gender: str = typer.Option(
        vcard_main_attributes["gender"]["default"],
        help=vcard_main_attributes["gender"]["description"],
    ),
    email: str = typer.Option(
        vcard_main_attributes["email"]["default"],
        help=vcard_main_attributes["email"]["description"],
    ),
    categories: str = typer.Option(
        vcard_main_attributes["categories"]["default"],
        help=vcard_main_attributes["categories"]["description"],
    ),
    note: str = typer.Option(
        vcard_main_attributes["note"]["default"],
        help=vcard_main_attributes["note"]["description"],
    ),
    url: str = typer.Option(
        vcard_main_attributes["url"]["default"],
        help=vcard_main_attributes["url"]["description"],
    ),
    source: str = typer.Option(
        vcard_main_attributes["source"]["default"],
        help=vcard_main_attributes["source"]["description"],
    ),
    bday: str = typer.Option(
        vcard_main_attributes["bday"]["default"],
        help=vcard_main_attributes["bday"]["description"],
    ),
    anniversary: str = typer.Option(
        vcard_main_attributes["anniversary"]["default"],
        help=vcard_main_attributes["anniversary"]["description"],
    ),
    kind: str = typer.Option(
        vcard_main_attributes["kind"]["default"],
        help=vcard_main_attributes["kind"]["description"],
    ),
    adr: str = typer.Option(
        vcard_main_attributes["adr"]["default"],
        help=vcard_main_attributes["adr"]["description"],
    ),
    tel: str = typer.Option(
        vcard_main_attributes["tel"]["default"],
        help=vcard_main_attributes["tel"]["description"],
    ),
    impp: str = typer.Option(
        vcard_main_attributes["impp"]["default"],
        help=vcard_main_attributes["impp"]["description"],
    ),
    photo: str = typer.Option(
        vcard_main_attributes["photo"]["default"],
        help=vcard_main_attributes["photo"]["description"],
    ),
    generate_key: bool = typer.Option(
        False,
        "--generate-key",
        help="Generate a new Ed25519 keypair and save to PEM files (vcard_private.pem and vcard_public.pem)",
        is_flag=True,
    ),
):
    """
    Generate a vCard by asking the user for information.
    """

    custom_attributes = {}
    # Prompt the user for vCard fields if interactive mode is enabled
    if interactive:
        typer.secho("Let's create a new vCard!", fg=typer.colors.CYAN)
        temp_file = "vcard_create.tmp"

        # Load existing data from the temp file if it exists
        temp_data = {}
        if os.path.exists(temp_file):
            with open(temp_file, "r", encoding="utf-8") as f:
                for line in f:
                    key, value = line.strip().split("=", 1)
                    temp_data[key] = value

        def save_entry_temp(key, value):
            """Save a single entry to the temp file."""
            temp_data[key] = value
            with open(temp_file, "w", encoding="utf-8") as f:
                for k, v in temp_data.items():
                    f.write(f"{k}={v}\n")

        def prompt_with_temp(key, description, default):
            """Prompt the user and save the value to the temp file."""
            value = typer.prompt(description, default=temp_data.get(key, default))
            save_entry_temp(key, value)
            return value

        fn = prompt_with_temp("fn", vcard_main_attributes["fn"]["description"], fn)
        n = prompt_with_temp("n", vcard_main_attributes["n"]["description"], n)
        nickname = prompt_with_temp(
            "nickname", vcard_main_attributes["nickname"]["description"], nickname
        )
        lang = prompt_with_temp(
            "lang", vcard_main_attributes["lang"]["description"], lang
        )
        gender = prompt_with_temp(
            "gender", vcard_main_attributes["gender"]["description"], gender
        )
        email = prompt_with_temp(
            "email", vcard_main_attributes["email"]["description"], email
        )
        categories = prompt_with_temp(
            "categories", vcard_main_attributes["categories"]["description"], categories
        )
        bday = prompt_with_temp(
            "bday", vcard_main_attributes["bday"]["description"], bday
        )
        anniversary = prompt_with_temp(
            "anniversary",
            vcard_main_attributes["anniversary"]["description"],
            anniversary,
        )
        kind = prompt_with_temp(
            "kind", vcard_main_attributes["kind"]["description"], kind
        )
        adr = prompt_with_temp("adr", vcard_main_attributes["adr"]["description"], adr)
        tel = prompt_with_temp("tel", vcard_main_attributes["tel"]["description"], tel)
        impp = prompt_with_temp(
            "impp", vcard_main_attributes["impp"]["description"], impp
        )
        photo = prompt_with_temp(
            "photo", vcard_main_attributes["photo"]["description"], photo
        )
        note = prompt_with_temp(
            "note", vcard_main_attributes["note"]["description"], note
        )
        url = prompt_with_temp("url", vcard_main_attributes["url"]["description"], url)
        source = prompt_with_temp(
            "source", vcard_main_attributes["source"]["description"], source
        )

        # Add key
        generate_key = typer.confirm("Do you want to create new keys?", default=False)

        # Add the X-FEED attribute if the user wants to include it
        add_feed = typer.confirm(
            "Do you want to add a X-FEED attribute for an RSS feed?", default=False
        )
        if add_feed:
            feed_url = prompt_with_temp("x_feed", "Enter the RSS feed URL", "")
            custom_attributes["X-FEED"] = feed_url

        typer.secho(
            "ℹ️ If you have feeds in different languages, add X-FEED;LANGUAGE:language-region to the vCard."
        )
        custom_feeds = []
        add_feed = typer.confirm(
            "Do you want to add custom X-FEED;LANGUAGE:language-region entries?",
            default=False,
        )

        while add_feed:
            language = prompt_with_temp(
                f"x_feed_language_{len(custom_feeds)}",
                "Enter the language-region (e.g., 'en-US', 'es-ES')",
                "",
            ).strip()
            feed_url = prompt_with_temp(
                f"x_feed_url_{len(custom_feeds)}", "Enter the feed URL", ""
            ).strip()
            custom_feeds.append((language, feed_url))
            add_feed = typer.confirm(
                "Do you want to add another X-FEED;LANGUAGE entry?", default=False
            )

        # Add the X-FEED;LANGUAGE entries to the vCard content
        for language, feed_url in custom_feeds:
            attribute_name = f"FEED;LANGUAGE={language}"
            custom_attributes[f"X-{attribute_name}"] = feed_url

        # Social links
        add_custom_social = typer.confirm(
            "Do you want to add custom attributes for social media links?",
            default=False,
        )

        # Custom attributes for social media links or other information
        while add_custom_social:

            attribute_name = VCard.build_custom_attribute_social_platform(
                typer.prompt(
                    "Enter the name of the social platform (it will be prefixed with 'X-SOCIAL;PLATFORM=')"
                )
            )
            # Prompt the user for the custom attribute value and save it to the temp file
            attribute_value = prompt_with_temp(
                f"x_{attribute_name}", f"Enter the value for {attribute_name}", ""
            )
            custom_attributes[f"{attribute_name}"] = attribute_value
            add_custom_social = typer.confirm(
                "Do you want to add another social media link?", default=False
            )

        add_custom = typer.confirm(
            "Do you want to add custom attributes for other information?",
            default=False,
        )

        # Custom attributes for social media links or other information
        while add_custom:
            attribute_name = VCard.build_custom_attribute(
                typer.prompt(
                    "Enter the name of the custom attribute (it will be prefixed with 'X-')"
                )
            )
            # Prompt the user for the custom attribute value and save it to the temp file
            attribute_value = prompt_with_temp(
                f"x_{attribute_name}", f"Enter the value for X-{attribute_name}", ""
            )
            custom_attributes[f"X-{attribute_name}"] = attribute_value
            add_custom = typer.confirm(
                "Do you want to add another custom attribute?", default=False
            )

    keys = None
    if generate_key:
        priv, pub, key = action_generate_keypair(
            Path("vcard_private.pem"), Path("vcard_public.pem")
        )
        keys = [{"alg": "ed25519", "key_b64": key, "pref": 1, "encoding": "b"}]

    # Generate the vCard content
    vcard_content = VCard.build_content(
        fn,
        n,
        nickname,
        lang,
        gender,
        email,
        categories,
        bday,
        anniversary,
        kind,
        adr,
        tel,
        impp,
        photo,
        note,
        url,
        source,
        custom_attributes,
        keys,
    )

    # Print a summary of the vCard
    typer.secho("\nSummary of the vCard:", fg=typer.colors.CYAN)
    typer.echo(vcard_content)
    typer.echo("\n")

    # Ask for confirmation before saving
    if interactive:
        confirm_save = typer.confirm(
            "Do you want to save this vCard to the file?", default=True
        )
        if not confirm_save:
            typer.secho(
                "❌ Operation canceled. The vCard was not saved.", fg=typer.colors.RED
            )
            raise typer.Exit()

    # Write the vCard to the output file
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(vcard_content, encoding="utf-8")
    typer.secho(f"✅ vCard generated and saved to {output}", fg=typer.colors.GREEN)


@app.command()
def fetch(
    inputs: List[str] = typer.Argument(
        ...,
        help="One or more .vcf files, directories containing .vcf files, or URLs to vCard files.",
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory to write updated vCards. Defaults to overwriting in place.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be updated without writing any files.",
    ),
    backup: bool = typer.Option(
        False,
        "--backup",
        "-b",
        help="Create a .bak copy before overwriting.",
        is_flag=True,
    ),
    show_diff: bool = typer.Option(
        False,
        "--diff",
        "-d",
        help="Show colored unified diff between old and new content.",
    ),
):
    """
    Fetch or update vCards by fetching the remote vCard referenced in their SOURCE property.

    Supports multiple files, directories, URLs, dry-run mode, backups, colored diffs,
    a progress bar, and a final summary report.
    """

    vcard_inputs = VCardInputs(inputs)
    total_inputs = len(vcard_inputs.vcard_files) + len(vcard_inputs.vcard_urls)
    if total_inputs == 0:
        typer.secho("No valid .vcf files or URLs provided.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Summary counters
    downloaded = 0
    updated = 0
    skipped = 0
    failed = 0

    with Progress() as progress:
        task = progress.add_task("Processing vCards...", total=total_inputs)

        for url in vcard_inputs.vcard_urls:
            progress.console.print(f"[bold]Processing URL:[/bold] {url}")
            try:
                vcard = VCard(url=url)
                filename = vcard.path
                destination = output_dir / filename if output_dir else Path(filename)
                vcard.to_file(destination)
                progress.console.print(
                    f"[green]  Downloaded and saved to:[/green] {url} -> {destination.name}"
                )
                downloaded += 1
            except Exception as e:
                progress.console.print(f"[red]  Failed to fetch URL {url}: {e}[/red]")
                failed += 1
            progress.update(task, advance=1)

        for file in vcard_inputs.vcard_files:
            progress.console.print(f"[bold]Processing:[/bold] {file}")

            vcard = VCard(path=file)
            old_text = vcard.profile.raw

            if not vcard.profile.source:
                progress.console.print(
                    "[yellow]  No SOURCE property found. Skipping.[/yellow]"
                )
                skipped += 1
                progress.update(task, advance=1)
                continue

            url = vcard.profile.source
            progress.console.print(f"  Fetching: {url}")

            try:
                new_text = VCard(url=url).profile.raw
            except Exception as e:
                progress.console.print(f"[red]  Failed to fetch SOURCE: {e}[/red]")
                failed += 1
                progress.update(task, advance=1)
                continue

            # Show colored diff if requested
            if show_diff:
                diff = "\n".join(
                    difflib.unified_diff(
                        old_text.splitlines(),
                        new_text.splitlines(),
                        fromfile=str(file),
                        tofile="(fetched)",
                        lineterm="",
                    )
                )
                if diff.strip():
                    syntax = Syntax(diff, "diff", theme="ansi_dark", line_numbers=False)
                    progress.console.print(syntax)
                else:
                    progress.console.print("[green]  No differences.[/green]")

            # Dry-run mode: do not write anything
            if dry_run:
                progress.console.print("[cyan]  Dry-run: no changes written.[/cyan]")
                updated += 1
                progress.update(task, advance=1)
                continue

            # Determine output path
            if output_dir:
                out_path = output_dir / file.name
            else:
                out_path = file

            # Backup if overwriting in place
            if backup and out_path.exists() and not output_dir:
                backup_path = out_path.with_suffix(out_path.suffix + ".bak")
                backup_path.write_text(old_text, encoding="utf-8")
                progress.console.print(f"[blue]  Backup created:[/blue] {backup_path}")

            # Write updated vCard
            out_path.write_text(new_text, encoding="utf-8")
            progress.console.print(f"[green]  Updated:[/green] {out_path}")
            updated += 1

            progress.update(task, advance=1)

    typer.secho(f"Summary:")
    typer.secho(f"  Downloaded: {downloaded}", fg=typer.colors.GREEN)
    typer.secho(f"  Updated: {updated}", fg=typer.colors.GREEN)
    typer.secho(f"  Skipped: {skipped}", fg=typer.colors.YELLOW)
    typer.secho(f"  Failed: {failed}", fg=typer.colors.RED)
    typer.secho(f"Done.")


@app.command()
def parse(
    input: Path = typer.Argument(
        None, exists=True, readable=True, help="Path to the vCard file to parse"
    )
):
    """
    Parse a vCard file and display its properties in a human-readable format.
    """
    try:
        text = None
        if input.is_file():
            text = input.read_text(encoding="utf-8")
        elif not os.isatty(0):  # Check if stdin is not a terminal
            text = sys.stdin.read().strip()

        if not text:
            typer.secho("❌ No input data provided for parsing.", fg=typer.colors.RED)
            raise typer.Exit()
        json_string = VCard(text=text).to_json()
        print(json_string)

    except Exception as e:
        typer.secho(f"Failed to parse vCard: {e}", fg=typer.colors.RED)
        raise typer.Exit()


@app.command(help="Sign canonical endorsement strings for one or more vCard files")
def endorse(
    inputs: List[str] = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to a vCard file. Pass multiple to process multiple files.",
    ),
    v_card_destination: Path = typer.Option(
        None,
        "--vcard",
        "-v",
        exists=True,
        readable=True,
        help="Path to the .vcf where the endorsement will be added",
    ),
    priv: Path = typer.Option(
        ...,
        "--priv",
        exists=True,
        readable=True,
        help="Path to the private key PEM used to sign endorsements.",
    ),
    confidence: str = typer.Option(
        "medium",
        "--confidence",
        "-c",
        help="Confidence level for the endorsement (low, medium, high). This is just metadata and does not affect the signature.",
    ),
    write: bool = typer.Option(
        False,
        "--write",
        help="Whether to write the endorsement to the vCard file. If false, the endorsement will be generated and printed but not saved.",
        is_flag=True,
    ),
):
    """
    Parse each vCard, extract its preferred key, build canonical endorsement string,
    and sign it.
    """

    valid_confidence_levels = {"low", "medium", "high"}
    if confidence not in valid_confidence_levels:
        typer.secho(
            f"❌ Invalid confidence level '{confidence}'. Must be one of: {', '.join(valid_confidence_levels)}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    try:
        private_key = load_private_key_pem(priv.read_bytes())
    except Exception as e:
        typer.secho(
            f"Failed to load private key from '{priv}': {e}", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    v_card_inputs = VCardInputs(inputs)

    for vcard_path in v_card_inputs.vcard_files:
        try:
            v_card_input = VCard(path=vcard_path)

            preferred_key = v_card_input.get_preferred_key()

            if not preferred_key:
                raise ValueError("No valid KEY entries found in the vCard")

            signature_endorsement = VCard.sign_endorsement(
                private_key, preferred_key.key_b64
            )

            has_endorsement = v_card_input.has_endorsement_for_key(
                preferred_key.key_b64
            )

            endorsement_value = VCard.build_custom_attribute_endorsement(
                preferred_key.key_b64,
                signature_endorsement,
                confidence=confidence,
                date=datetime.now().strftime("%Y%m%dT%H%M%SZ"),
            )
            if write:
                v_card = VCard(path=v_card_destination)
                if has_endorsement:
                    typer.secho(
                        f"⚠️ Endorsement already exists for key {preferred_key.key_b64} in {v_card_destination}. Skipping write.",
                        fg=typer.colors.YELLOW,
                    )
                else:
                    v_card.add_line(endorsement_value)
                    v_card.to_file()
                    typer.secho(
                        f"✅ Endorsement added to {v_card.path}: {endorsement_value}",
                        fg=typer.colors.GREEN,
                    )
            else:
                print(endorsement_value)

        except Exception as e:
            typer.secho(
                f"Failed to parse vCard from '{vcard_path}': {e}", fg=typer.colors.RED
            )


@app.command(
    help="Generate a QR code from the provided vCard file (support input piping) and save it to a file."
)
def qr(
    input: str = typer.Argument(None, help="Data to encode in the QR code"),
    output: str = typer.Option(
        None, "--output", "-o", help="Output file to save the QR code image"
    ),
    image: str = typer.Option(
        None, "--image", "-i", help="Path to an image to include in the QR code"
    ),
    caption_top: str = typer.Option(
        "", "--caption-top", "-ct", help="Caption to display above the QR code"
    ),
    caption_bottom: str = typer.Option(
        "", "--caption-bottom", "-cb", help="Caption to display below the QR code"
    ),
    font: Path = typer.Option(
        None,
        "--font",
        "-f",
        help="Path to a .ttf font file to use for captions (optional)",
    ),
):
    """
    Generate a QR code from the provided data and save it to a file.
    """
    # Check if the input is provided via standard input (piped data)

    data = None
    if input:
        if os.path.isfile(input):
            with open(input, "r", encoding="utf-8") as file:
                data = file.read().strip()
    elif not os.isatty(0):  # Check if stdin is not a terminal
        data = sys.stdin.read().strip()

    if not data:
        typer.secho("❌ No input data provided for the QR code.", fg=typer.colors.RED)
        raise typer.Exit()

    if image and not os.path.isfile(image):
        typer.secho(
            f"❌ The specified image file does not exist: {image}", fg=typer.colors.RED
        )
        raise typer.Exit()

    if not output:
        typer.secho(
            "❌ Output file path is required to save the QR code image.",
            fg=typer.colors.RED,
        )
        raise typer.Exit()

    if caption_top or caption_bottom:
        if not font:
            typer.secho(
                "❌ A font file must be specified when using captions.",
                fg=typer.colors.RED,
            )
            raise typer.Exit()
        elif not os.path.isfile(font):
            typer.secho(
                f"❌ The specified font file does not exist: {font}",
                fg=typer.colors.RED,
            )
            raise typer.Exit()

    generate_qr(image, output, data, caption_top, caption_bottom)


if __name__ == "__main__":
    app()
