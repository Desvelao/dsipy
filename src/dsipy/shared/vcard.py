import os
import re
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
import requests
from .security import canonical_endorsement_string, sign_endorsement
import typer
import json

# -----------------------------
# Data structures
# -----------------------------


@dataclass
class PublicKey:
    alg: str
    key_b64: str
    pref: Optional[int] = None


@dataclass
class Endorsement:
    endorsee_key_b64: str
    signature_hex: str
    date: Optional[str] = None
    confidence: Optional[str] = None


@dataclass
class RevokedKey:
    key_b64: str
    reason: Optional[str] = None
    date: Optional[str] = None

@dataclass
class Feed:
    language: str
    category: str
    url: str

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


@dataclass
class Profile:
    fn: Optional[str] = None
    n: Optional[str] = None
    nickname: Optional[str] = None
    photo: Optional[str] = None
    lang: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    categories: Optional[str] = None
    bday: Optional[str] = None
    anniversary: Optional[str] = None
    kind: Optional[str] = None
    adr: Optional[str] = None
    tel: Optional[str] = None
    impp: Optional[str] = None
    note: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None # REQUIRED
    keys: List[PublicKey] = field(default_factory=list)
    endorsements: List[Endorsement] = field(default_factory=list)
    revocations: List[RevokedKey] = field(default_factory=list)
    feeds: List[Feed] = field(default_factory=list)
    raw: str = ""
    raw_lines: List[dict] = field(default_factory=list)  # Store raw lines with metadata


# -----------------------------
# Helper: parse parameters
# -----------------------------


def parse_params(header: str) -> dict:
    """
    Extracts parameters from a vCard property header.
    Example:
        'X-ENDORSE;ENCODING=b;SIG=abcd;DATE=2026...' ->
        {'ENCODING': 'b', 'SIG': 'abcd', 'DATE': '2026...'}
    """
    params = {}
    parts = header.split(";")[1:]  # skip property name
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.upper()] = v
    return params


# -----------------------------
# -----------------------------
# Main parser
# -----------------------------
class VCard:
    def __init__(self, text: str = None, path: Path = None, url: str = None):
        self.profile = Profile()
        if text:
            self.profile = parse_vcard(text)
        elif path:
            if not path.is_file():
                raise ValueError(f"The specified path is not a file: {path}")
            self.path = path
            self.profile = parse_vcard(path.read_text(encoding="utf-8"))
        elif url:
            text, filename = VCard._fetch(url)
            self.profile = parse_vcard(text)
            self.url = url
            self.path = filename if filename.endswith((".vcf", ".vcard")) else f"{filename}.vcf"
        else:
            raise ValueError("Either text, path, or url must be provided to initialize the vCard.")
    def parse(self, text: str) -> Profile:
        """Parse vCard text and update the profile."""
        self.profile = parse_vcard(text)
        return self.profile
    
    def build(self) -> str:
        """Build vCard content from the current profile."""
        return build_vcard_from_raw_lines(self.profile)
    
    def add_line(self, line: str) -> None:
        """Add a line to the vCard."""
        content = self.profile.raw or self.build()
        end_vcard = "END:VCARD"
        if content:
            if not content.strip().endswith(end_vcard):
                raise ValueError(f"Invalid vCard format: missing {end_vcard}")
            new_content = content.replace(end_vcard, f"{line}\n{end_vcard}")
            self.profile = self.parse(new_content)  # Re-parse to update the profile

    def to_string(self) -> str:
        """Return the vCard as a string."""
        return self.profile.raw or self.build()
    
    def to_file(self, path: Path = None) -> None:
        """Save the vCard to a file."""
        file_path = path if path else getattr(self, "path", None)
        if not file_path:
            raise ValueError("No path specified for saving the vCard.")
        file_path.write_text(self.to_string(), encoding="utf-8")
    
    def to_json(self) -> str:
        """Return the vCard profile as a JSON string."""
        return json.dumps(asdict(self.profile), ensure_ascii=False)

    def get_preferred_key(self) -> Optional[PublicKey]:
        """Get the preferred public key based on the PREF parameter."""
        if not self.profile.keys:
            return None
        preferred_keys = sorted(
            self.profile.keys, key=lambda k: k.pref if k.pref is not None else float("inf")
        )
        return preferred_keys[0]  # Return the key with the lowest PREF value (highest priority)
    @staticmethod
    def sign_endorsement(private_key, endorsee_key_b64: str) -> str:
        """Return the endorsement signature in hexadecimal format."""
        return sign_endorsement(private_key, canonical_endorsement_string(endorsee_key_b64))
    
    def has_endorsement_for_key(self, endorsee_key_b64: str) -> bool:
        """Check if there is an endorsement for the given endorsee key."""
        return any(e.endorsee_key_b64 == endorsee_key_b64 for e in self.profile.endorsements)
    
    @staticmethod
    def _fetch(url: str) -> str:
        """
        Fetch a vCard from a URL.

        Args:
            url (str): The URL to fetch the vCard from.

        Returns:
            str: The vCard content as text.

        Raises:
            requests.RequestException: If the URL fetch fails.
        """
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        filename = response.headers.get('Content-Disposition', '').split('filename=')[-1].strip('"\'') or url.split('/')[-1]

        text = response.text
        if not text.strip().startswith("BEGIN:VCARD"):
            raise ValueError(f"URL does not contain a valid vCard: {url}")
        
        return text, filename
    @staticmethod
    def build_custom_attribute_social_platform(name):
        """
        Build a custom attribute string for the vCard.

        Args:
            name (str): The name of the custom attribute.

        Returns:
            str: The formatted custom attribute string.
        """
        return f"X-SOCIAL;PLATFORM={name.strip().lower()}"
    @staticmethod
    def build_custom_attribute(name):
        """
        Build a custom attribute string for the vCard.

        Args:
            name (str): The name of the custom attribute.

        Returns:
            str: The formatted custom attribute string.
        """
        return f"{name.strip().upper()}="
    @staticmethod
    def build_custom_attribute_endorsement(canonical_value: str, signature_hex, date=None, confidence=None, encoding="b"):
        """
        Build a custom endorsement attribute string for the vCard.

        Args:
            signature_hex (str): The endorsement signature in hexadecimal format.
            date (str, optional): The date of the endorsement in ISO format (YYYY-MM-DD). Defaults to None.
            confidence (str, optional): The confidence level of the endorsement. Defaults to None.
            encoding (str, optional): The encoding of the endorsement. Defaults to "b".
        Returns:
            str: The formatted custom endorsement attribute string.
        """
        params = []
        params.append(f"SIG={signature_hex}")
        if date:
            params.append(f"DATE={date}")
        if confidence:
            params.append(f"CONFIDENCE={confidence}")
        params.append(f"ENCODING={encoding}")
        params_str = ";" + ";".join(params) if params else ""
        return f"X-ENDORSE{params_str}:{canonical_value}"
    @staticmethod
    def build_content(
        fn=None,
        n=None,
        nickname=None,
        lang=None,
        gender=None,
        email=None,
        categories=None,
        bday=None,
        anniversary=None,
        kind=None,
        adr=None,
        tel=None,
        impp=None,
        photo=None,
        note=None,
        url=None,
        source=None,
        custom_attributes=None,
        keys=None,
    ):
        """
        Build the vCard content based on the provided fields.

        Args:
            fn (str): Full name.
            n (str): Name components.
            nickname (str): Nickname.
            lang (str): Language.
            gender (str): Gender.
            email (str): Email address.
            categories (str): Categories.
            bday (str): Birthday.
            anniversary (str): Anniversary.
            kind (str): Kind of contact.
            adr (str): Address.
            tel (str): Telephone number.
            impp (str): Instant messaging and presence protocol.
            photo (str): Photo URL.
            note (str): Note.
            url (str): URL.
            source (str): Source URL.
            custom_attributes (dict): Custom attributes as key-value pairs.
            keys (list): List of public keys, each as a dict with 'alg', 'key_b64', and optional 'pref'.

        Returns:
            str: The generated vCard content.
        """
        if custom_attributes is None:
            custom_attributes = {}

        # Start building the vCard content
        vcard_content = "BEGIN:VCARD\nVERSION:4.0\n"

        # Add optional fields conditionally
        if fn:
            vcard_content += f"FN:{fn}\n"
        if n:
            vcard_content += f"N:{n};;;;\n"
        if nickname:
            vcard_content += f"NICKNAME:{nickname}\n"
        if lang:
            vcard_content += f"LANG:{lang}\n"
        if gender:
            vcard_content += f"GENDER:{gender}\n"
        if email:
            vcard_content += f"EMAIL:{email}\n"
        if categories:
            vcard_content += f"CATEGORIES:{categories}\n"
        if bday:
            vcard_content += f"BDAY:{bday}\n"
        if anniversary:
            vcard_content += f"ANNIVERSARY:{anniversary}\n"
        if kind:
            vcard_content += f"KIND:{kind}\n"
        if adr:
            vcard_content += f"ADR:{adr}\n"
        if tel:
            vcard_content += f"TEL:{tel}\n"
        if impp:
            vcard_content += f"IMPP:{impp}\n"
        if photo:
            vcard_content += f"PHOTO:{photo}\n"
        if note:
            vcard_content += f"NOTE;LANGUAGE=en-US:{note}\n"
        if url:
            vcard_content += f"URL:{url}\n"
        if source:
            vcard_content += f"SOURCE:{source}\n"
        if keys:
            for key in keys:
                vcard_content += f"KEY;TYPE=public;ALG={key['alg'].lower()};PREF={key.get('pref', 1)};ENCODING={key['encoding']}:{key['key_b64']}\n"

        # Add custom attributes conditionally
        for attribute_name, attribute_value in custom_attributes.items():
            vcard_content += f"{attribute_name}:{attribute_value}\n"

        # End the vCard content
        vcard_content += "END:VCARD"

        return vcard_content
        


def parse_vcard(text: str) -> Profile:
    profile = Profile(raw=text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:

        attr_name=None
        value=None
        attributes={}

        match = re.match(r"^[^:;]+", line)
        
        # -------------------------
        # Public keys
        # -------------------------
        if line.startswith("KEY;"):
            attr_name = "key"
            header, value = line.split(":", 1)
            attributes = parse_params(header)
            profile.keys.append(
                PublicKey(
                    alg=attributes.get("ALG", "").lower(),
                    key_b64=value,
                    pref=int(attributes["PREF"]) if "PREF" in attributes else None,
                )
            )

        # -------------------------
        # Revoked keys
        # -------------------------
        elif line.startswith("REVKEY;"):
            attr_name = "revkey"
            header, value = line.split(":", 1)
            attributes = parse_params(header)
            profile.revocations.append(
                RevokedKey(
                    key_b64=value, reason=attributes.get("REASON"), date=attributes.get("DATE")
                )
            )

        # -------------------------
        # Endorsements (single-line format)
        # -------------------------
        elif line.startswith("X-ENDORSE;"):
            attr_name = "x-endorse"
            header, value = line.split(":", 1)
            attributes = parse_params(header)
            profile.endorsements.append(
                Endorsement(
                    endorsee_key_b64=value,
                    signature_hex=attributes.get("SIG", ""),
                    date=attributes.get("DATE"),
                    confidence=attributes.get("CONFIDENCE"),
                )
            )

        # -------------------------
        # Feeds (single-line format)
        # -------------------------
        elif line.startswith("X-FEED;"):
            attr_name = "x-feed"
            header, value = line.split(":", 1)
            attributes = parse_params(header)

            profile.feeds.append(
                Feed(
                    language=attributes.get("LANGUAGE", ""),
                    category=attributes.get("CATEGORY", ""),
                    url=value,
                )
            )
        elif match:
            attr_name_matched = match.group(0).lower()
            if attr_name_matched in vcard_main_attributes:
                attr_name = attr_name_matched
                value = line[len(attr_name_matched) + 1:]
                setattr(profile, attr_name_matched, value)
        
        profile.raw_lines.append({"line": line, "attr_name": attr_name, "value": value, "attributes": attributes})

    return profile


def build_vcard_from_raw_lines(profile: Profile) -> str:
    """
    Build a vCard string from the raw_lines stored in a Profile object.

    Args:
        profile (Profile): The Profile object containing parsed vCard data.

    Returns:
        str: The reconstructed vCard content.
    """
    vcard_content = "BEGIN:VCARD\nVERSION:4.0\n"
    
    for raw_line in profile.raw_lines:
        line = raw_line.get("line", "")
        if line and not line.startswith("BEGIN:") and not line.startswith("END:") and not line.startswith("VERSION:"):
            vcard_content += f"{line}\n"
    
    vcard_content += "END:VCARD"
    return vcard_content



def generate_opml_from_vcards(vcard_files):
    """
    Reads vCard files and generates an OPML file.

    Args:
        vcard_files (list): List of paths to vCard files.
    """
    import vobject
    from opyml import OPML, Outline

    opml = OPML()

    for vcard_file in vcard_files:
        with open(vcard_file, "r", encoding="utf-8") as f:
            for vcard in vobject.readComponents(f):
                # Extract the name and feed URL from the vCard
                name = vcard.fn.value if hasattr(vcard, "fn") else "Unknown"
                feed_url = vcard.x_feed.value if hasattr(vcard, "x_feed") else None

                if feed_url:
                    opml.body.outlines.append(
                        Outline(text=name, title=name, xml_url=feed_url)
                    )

    return opml.to_xml()

def fetch_vcard_from_url(url):
    """
    Fetch a vCard from a URL.

    Args:
        url (str): The URL to fetch the vCard from.

    Returns:
        str: The vCard content as text.

    Raises:
        requests.RequestException: If the URL fetch fails.
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    filename = response.headers.get('Content-Disposition', '').split('filename=')[-1].strip('"\'') or url.split('/')[-1]

    text = response.text
    if not text.strip().startswith("BEGIN:VCARD"):
        raise ValueError(f"URL does not contain a valid vCard: {url}")
    
    return text, filename

def fetch_save_vcard_from_url(url, output_dir: Path = None) -> tuple[Path, str]:
    """
    Fetch a vCard from a URL and save it to the specified output directory.

    Args:
        url (str): The URL to fetch the vCard from.
        output_dir (Path, optional): The directory to save the fetched vCard. Defaults to None.

    Returns:
        tuple: A tuple containing the destination Path and the vCard content as text.
    Raises:
        requests.RequestException: If the URL fetch fails."""
    
    text, filename = fetch_vcard_from_url(url)
   
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    filename = filename if filename.endswith((".vcf", ".vcard")) else f"{filename}.vcf"
    destination = output_dir / filename if output_dir else Path(filename)
    destination.write_text(text, encoding="utf-8")
    return destination, text

class VCardInputs:
    def __init__(self, inputs: List[str]):
        self.inputs = inputs
        self.classified = VCardInputs.classify_inputs(inputs)
        self.vcard_files = VCardInputs.get_vcard_local_files_from_inputs(self.classified["paths"])
        self.vcard_urls = self.classified["urls"]
    @staticmethod
    def classify_inputs(inputs):
        """
        Classify inputs as URLs or local file/directory paths.

        Args:
            inputs (list): List of input strings (URLs or file paths).

        Returns:
            dict: Dictionary with 'urls' and 'paths' keys, each containing a list of classified inputs.
        """
        classified = {"urls": [], "paths": []}
        
        url_pattern = r"^https?://"
        
        for input_item in inputs:
            if isinstance(input_item, str) and re.match(url_pattern, input_item):
                classified["urls"].append(input_item)
            else:
                classified["paths"].append(Path(input_item) if isinstance(input_item, str) else input_item)
        
        return classified
    @staticmethod
    def get_vcard_local_files_from_inputs(inputs):

        vcf_files = []
        for input_path in inputs:
            if not input_path.exists():
                typer.secho(f"Input path does not exist: {input_path}", fg=typer.colors.RED)
                continue
            if not input_path.is_file() and not input_path.is_dir():
                typer.secho(f"Input path is not a file or directory: {input_path}", fg=typer.colors.RED)
                continue
            if input_path.is_file() and (input_path.suffix.lower() in [".vcf", ".vcard"]):
                vcf_files.append(input_path)
            if input_path.is_dir():
                for root, _, files in os.walk(input_path):
                    for f in files:
                        if f.lower().endswith((".vcf", ".vcard")):
                            vcf_files.append(Path(root) / f)
        return vcf_files
    


def add_line_to_vcard(vcard_content: str, line: str) -> str:
    """
    Add a new line before the END:VCARD statement.

    Args:
        vcard_content (str): The vCard content as text.
        line (str): The line to add before END:VCARD.

    Returns:
        str: The modified vCard content.
    """
    if not vcard_content.strip().endswith("END:VCARD"):
        raise ValueError("Invalid vCard format: missing END:VCARD")
    
    return vcard_content.replace("END:VCARD", f"{line}\nEND:VCARD")
