import os
import datetime
import markdown
import typer
from .feed import generate_rss


class MarkdownFeed:
    def _parse_file(path):
        """
        Extract metadata and content from a markdown file.
        Supports simple YAML-like front matter:
        ---
        title: My Post
        date: 2025-01-01
        link: https://example.com/my-post
        ---
        """
        content_lines = []

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        frontmatter = {}
        # Detect front matter
        if lines and lines[0].strip() == "---":
            i = 1
            while i < len(lines) and lines[i].strip() != "---":
                line = lines[i].strip()

                fields = ["title", "date", "link"]

                for field in fields:
                    prefix = f"{field}:"
                    if line.startswith(prefix):
                        frontmatter[field] = line.replace(prefix, "").strip()
                i += 1
            content_lines = lines[i + 1 :]
        else:
            content_lines = lines

        # Fallback title
        if not frontmatter.get("title"):
            frontmatter["title"] = os.path.splitext(os.path.basename(path))[0]

        # Fallback date (file modified time)
        if not frontmatter.get("date"):
            ts = os.path.getmtime(path)
            frontmatter["date"] = datetime.datetime.fromtimestamp(ts).strftime(
                "%Y-%m-%d"
            )

        html_content = markdown.markdown("".join(content_lines))

        return {
            "title": frontmatter["title"],
            "date": (
                datetime.datetime.strptime(frontmatter["date"], "%Y-%m-%dT%H:%M:%SZ")
                if "T" in frontmatter["date"]
                else datetime.datetime.strptime(frontmatter["date"], "%Y-%m-%d")
            ),
            "link": frontmatter.get("link", None),
            "content": html_content,
            "path": path,
        }

    def _create_state_content(title: str, message: str, date: str | None = None):
        """
        Create the content for a new markdown feed item, including front matter.
        The front matter includes the title and date, and is formatted as YAML-like metadata.
        Args:
            title (str): The title of the feed item.
            message (str): The content/message of the feed item.
            date (str | None): The date of the feed item in ISO format (optional).
        Returns:
            str: The complete content for the markdown file, including front matter and message.
        """
        attributes = {"title": title if title else None, "date": date}

        # Only include attributes that have a value (non-empty)
        front_matter = "\n".join(
            f"{key}: {value}" for key, value in attributes.items() if value
        )

        file_content = f"""---
{front_matter}
---
{message}
"""

    def create_state(
        destination: str, title: str, message: str, date: str | None = None
    ):
        content = MarkdownFeed._create_state_content(title, message, date)
        if os.path.exists(destination):
            typer.secho(
                f"❌ A feed '{destination}' already exists.", fg=typer.colors.RED
            )
            raise typer.Exit()
        with open(destination, "w", encoding="utf-8") as f:
            f.write(content)
        typer.secho(f"✅ New post created: {destination}", fg=typer.colors.GREEN)

    def collect(directory: str):
        md_files = [
            os.path.join(root, f)
            for root, _, files in os.walk(directory)
            for f in files
            if f.endswith(".md")
        ]

        states = [MarkdownFeed._parse_file(f) for f in md_files]
        states.sort(key=lambda x: x["date"], reverse=True)

        return states

    def build(
        states: list,
        title: str,
        link: str,
        description: str,
        author: str,
        email: str,
        language: str,
        output: str,
        sign: dict | None = None,
    ):
        author_data = {"name": author, "email": email}
        build_date = datetime.datetime.now()

        rss_xml = generate_rss(
            title, link, description, author_data, language, build_date, states, sign
        )

        print(f"Output file: {output}")

        with open(output, "w") as f:
            f.write(rss_xml)
