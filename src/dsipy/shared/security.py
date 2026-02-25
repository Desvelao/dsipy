from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64
import typer

# ============================================================
# Key generation
# ============================================================


def generate_keypair() -> tuple[bytes, bytes, str]:
    """
    Generates an Ed25519 private/public keypair.
    Returns (private_key_pem, public_key_pem, public_key_b64_der)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # PEM export
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # DER → base64 (for vCard)
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_b64 = base64.b64encode(public_der).decode("ascii")

    return private_pem, public_pem, public_b64


def action_generate_keypair(priv: str, pub: str) -> tuple[bytes, bytes, str]:
    """Generates an Ed25519 keypair and saves to the specified PEM files.

    Args:
        priv (str): Path to save the private key PEM file.
        pub (str): Path to save the public key PEM file.
    Returns:
        tuple: (private_key_pem, public_key_pem, public_key_b64_der)
    """
    priv_pem, pub_pem, pub_b64 = generate_keypair()

    open(priv, "wb").write(priv_pem)
    open(pub, "wb").write(pub_pem)

    typer.secho(
        f"✅ Keypair generated and saved to '{priv}' and '{pub}'", fg=typer.colors.GREEN
    )
    typer.secho(
        f"📋 Public key (Base64-encoded DER for vCard): {pub_b64}", fg=typer.colors.BLUE
    )

    return priv_pem, pub_pem, pub_b64


def public_key_to_der(public_key) -> bytes:
    """
    Export a public key to DER format.

    Args:
        public_key: The public key object to export.

    Returns:
        bytes: The public key in DER format.
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def public_key_to_b64der(public_key) -> bytes:
    """
    Export a public key to DER format and then encode it in Base64.
    Args:
        public_key: The public key object to export.
    Returns:
        str: The public key in Base64-encoded DER format.
    """
    return base64.b64encode(
        public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    ).decode("utf-8")


def b64der_to_public_key(content: str) -> str:
    """
    Decode a Base64-encoded DER public key and return it in PEM format.
    Args:
        content (str): The Base64-encoded DER content of the public key.
    Returns:
        str: The public key in PEM format (raw text).
    """
    public_key = load_public_key_b64_der(content)

    # Serialize the public key back to PEM format (raw text)
    pem_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return pem_key.decode("utf-8")


# ============================================================
# Key loading
# ============================================================


def load_private_key_pem(pem_bytes: bytes) -> bytes:
    """
    Load a private key from PEM bytes.
    Args:
        pem_bytes (bytes): The PEM-encoded private key bytes.
    Returns:
        The private key object.
    """
    return serialization.load_pem_private_key(pem_bytes, password=None)


def load_public_key_pem(pem_bytes: bytes) -> bytes:
    """
    Load a public key from PEM bytes.
    Args:
        pem_bytes (bytes): The PEM-encoded public key bytes.
    Returns:
        The public key object.
    """
    return serialization.load_pem_public_key(pem_bytes)


def load_public_key_b64_der(b64: str) -> bytes:
    """
    Load a public key from a Base64-encoded DER string.
    Args:
        b64 (str): The Base64-encoded DER string of the public key.
    Returns:
        The public key object.
    """
    der = base64.b64decode(b64.encode("ascii"))
    return serialization.load_der_public_key(der)


# ============================================================
# Endorsement signing
# ============================================================


def canonical_endorsement_string(endorsee_key_b64: str) -> bytes:
    """
    Canonical string defined in the RFC:
        endorse:<BASE64_DER_KEY>
    """
    return f"endorse:{endorsee_key_b64}".encode("utf-8")


def sign_endorsement(private_key, endorsee_key_b64: str) -> str:
    """
    Signs an endorsement and returns hex signature.
    """
    canonical = canonical_endorsement_string(endorsee_key_b64)
    sig = private_key.sign(canonical)
    return sig.hex()


def verify_endorsement_signature(
    public_key, endorsee_key_b64: str, signature_hex: str
) -> bool:
    canonical = canonical_endorsement_string(endorsee_key_b64)
    try:
        public_key.verify(bytes.fromhex(signature_hex), canonical)
        return True
    except Exception:
        return False


# ============================================================
# Feed signing (RSS items)
# ============================================================


def canonical_feed_string(pub_date: str, title: str, description_plain: str) -> bytes:
    """
    Canonical string defined in the RFC:
        <pubDate>\n<title>\n<description_plain>
    """
    return f"{pub_date}\n{title}\n{description_plain}".encode("utf-8")


def sign_feed_item(
    private_key, pub_date: str, title: str, description_plain: str
) -> str:
    """
    Signs a feed item and returns hex signature.
    """
    canonical = canonical_feed_string(pub_date, title, description_plain)
    sig = private_key.sign(canonical)
    print(canonical.decode("utf-8"), "->", sig.hex())
    return sig.hex()


def verify_feed_signature(
    public_key, pub_date: str, title: str, description_plain: str, signature_hex: str
) -> bool:
    """Verifies a feed item signature."""
    canonical = canonical_feed_string(pub_date, title, description_plain)
    try:
        public_key.verify(bytes.fromhex(signature_hex), canonical)
        return True
    except Exception:
        return False
