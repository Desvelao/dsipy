import os
import datetime
import sys
import typer
from functools import wraps
import qrcode
from ..shared.vcard import (
    build_vcard_content,
    build_vcard_custom_attribute,
    build_vcard_custom_attribute_social_platform,
    generate_opml_from_vcards,
)
from ..shared.file import write_file
from ..shared.qr import generate_qr
from ..shared.security import action_generate_keypair

app = typer.Typer(
    help="A CLI tool to generate RSS feeds from markdown files",
)


@app.command(
    help="Generate a QR code from the provided vCard file (support input piping) and save it to a file."
)
def qr(
    input: str = typer.Argument(None, help="Data to encode in the QR code"),
    output: str = typer.Option(None, help="Output file to save the QR code image"),
    image: str = typer.Option(None, help="Path to an image to include in the QR code"),
    caption_top: str = typer.Option("", help="Caption to display above the QR code"),
    caption_bottom: str = typer.Option("", help="Caption to display below the QR code"),
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

    generate_qr(image, output, data, caption_top, caption_bottom)


vcard_main_attributes = {
    "fn": {"default": "", "description": "Full Name (FN)"},
    "n": {"default": "", "description": "Name (N) in the format LastName;FirstName"},
    "nickname": {"default": "", "description": "Nickname (NICKNAME)"},
    "lang": {
        "default": "en-US",
        "description": "Language (LANG) in the format 'language-region' (e.g., 'en-US', 'es-ES')",
    },
    "gender": {
        "default": "",
        "description": "Gender (GENDER), e.g., 'M' for Male, 'F' for Female, or 'O' for Other",
    },
    "email": {"default": "", "description": "Email (EMAIL), e.g., 'example@mail.com'"},
    "categories": {
        "default": "",
        "description": "Categories (comma-separated, CATEGORIES), e.g., 'gamer,programmer'",
    },
    "bday": {"default": "", "description": "Birthday (BDAY) in the format YYYY-MM-DD"},
    "anniversary": {
        "default": "",
        "description": "Anniversary date (ANNIVERSARY) in the format YYYY-MM-DD",
    },
    "kind": {
        "default": "individual",
        "description": "Type of entity (KIND), e.g., 'individual' or 'org'",
    },
    "adr": {
        "default": "",
        "description": "Address (ADR) in the format ';;Street;City;State;PostalCode;Country'",
    },
    "tel": {
        "default": "",
        "description": "Telephone number (TEL), e.g., '+1234567890'",
    },
    "impp": {
        "default": "",
        "description": "Instant messaging protocol (IMPP), e.g., 'aim:exampleuser'",
    },
    "photo": {
        "default": "",
        "description": "URL to a photo (PHOTO), e.g., 'http://example.com/photo.jpg'",
    },
    "note": {"default": "", "description": "A short description about you (NOTE)"},
    "url": {
        "default": "",
        "description": "URL to public profile or personal web (URL), e.g., 'https://my.web.example.com/profile'",
    },
    "source": {
        "default": None,
        "description": "URL where the vCard will be hosted or can found (SOURCE)",
    },
}


@app.command()
def create(
    output: str = typer.Option("output.vcf", help="Output file to save the vCard"),
    interactive: bool = typer.Option(True, help="Interactive prompts"),
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
        "--key",
        "-k",
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
            "Do you want to add an X-FEED attribute for an RSS feed?", default=False
        )
        if add_feed:
            feed_url = prompt_with_temp("x_feed", "Enter the RSS feed URL", "")
            custom_attributes["X-FEED"] = feed_url

        typer.secho(
            "ℹ️ If you have feeds in different languages, add X-FEED;LANGUAGE:language-region to the vCard.",
            fg=typer.colors.BLUE,
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

            attribute_name = build_vcard_custom_attribute_social_platform(
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
            attribute_name = build_vcard_custom_attribute(
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
    print(generate_key)
    if generate_key:
        print("HELLO")
        priv, pub, key = action_generate_keypair(
            "vcard_private.pem", "vcard_public.pem"
        )
        keys = [{"alg": "ed25519", "key_b64": key, "pref": 1, "encoding": "b"}]

    # Generate the vCard content
    vcard_content = build_vcard_content(
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
    write_file(vcard_content, output)

    typer.secho(f"✅ vCard generated and saved to {output}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
