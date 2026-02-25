import re
from dataclasses import dataclass, field
from typing import List, Optional

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
class Profile:
    fn: Optional[str] = None
    photo: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    public_keys: List[PublicKey] = field(default_factory=list)
    endorsements: List[Endorsement] = field(default_factory=list)
    revocations: List[RevokedKey] = field(default_factory=list)
    raw: str = ""


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
# Main parser
# -----------------------------


def parse_vcard(text: str) -> Profile:
    profile = Profile(raw=text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:

        # -------------------------
        # FN (full name)
        # -------------------------
        if line.startswith("FN:"):
            profile.fn = line[3:]
            continue

        # -------------------------
        # PHOTO
        # -------------------------
        if line.startswith("PHOTO:"):
            profile.photo = line[6:]
            continue

        # -------------------------
        # Public keys
        # -------------------------
        if line.startswith("KEY;"):
            header, value = line.split(":", 1)
            params = parse_params(header)
            profile.public_keys.append(
                PublicKey(
                    alg=params.get("ALG", "").lower(),
                    key_b64=value,
                    pref=int(params["PREF"]) if "PREF" in params else None,
                )
            )
            continue

        # -------------------------
        # Revoked keys
        # -------------------------
        if line.startswith("REVKEY;"):
            header, value = line.split(":", 1)
            params = parse_params(header)
            profile.revocations.append(
                RevokedKey(
                    key_b64=value, reason=params.get("REASON"), date=params.get("DATE")
                )
            )
            continue

        # -------------------------
        # Endorsements (single-line format)
        # -------------------------
        if line.startswith("X-ENDORSE;"):
            header, value = line.split(":", 1)
            params = parse_params(header)
            profile.endorsements.append(
                Endorsement(
                    endorsee_key_b64=value,
                    signature_hex=params.get("SIG", ""),
                    date=params.get("DATE"),
                    confidence=params.get("CONFIDENCE"),
                )
            )
            continue

    return profile


def build_vcard_content(
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


def build_vcard_custom_attribute(name):
    """
    Build a custom attribute string for the vCard.

    Args:
        name (str): The name of the custom attribute.

    Returns:
        str: The formatted custom attribute string.
    """
    return f"{name.strip().upper()}="


def build_vcard_custom_attribute_social_platform(name):
    """
    Build a custom attribute string for the vCard.

    Args:
        name (str): The name of the custom attribute.

    Returns:
        str: The formatted custom attribute string.
    """
    return f"X-SOCIAL;PLATFORM={name.strip().lower()}"


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
