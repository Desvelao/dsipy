import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.dsipy.shared.security import (
    action_generate_keypair,
    load_private_key_pem,
    load_public_key_b64_der,
    load_public_key_pem,
)


class TestActionGenerateKeypair(unittest.TestCase):
    def test_generates_keypair_saves_files_and_returns_content(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            priv_path = Path(tmp_dir) / "private.pem"
            pub_path = Path(tmp_dir) / "public.pem"

            with patch("src.dsipy.shared.security.typer.secho") as mock_secho:
                priv_pem, pub_pem, pub_b64 = action_generate_keypair(
                    priv_path, pub_path
                )

            self.assertTrue(priv_path.exists())
            self.assertTrue(pub_path.exists())

            self.assertEqual(priv_path.read_bytes(), priv_pem)
            self.assertEqual(pub_path.read_bytes(), pub_pem)

            self.assertGreater(len(pub_b64), 0)
            self.assertIsInstance(pub_b64, str)

            private_key = load_private_key_pem(priv_pem)
            public_key_pem = load_public_key_pem(pub_pem)
            public_key_b64 = load_public_key_b64_der(pub_b64)

            self.assertIsNotNone(private_key)
            self.assertIsNotNone(public_key_pem)
            self.assertIsNotNone(public_key_b64)

            self.assertEqual(mock_secho.call_count, 2)


if __name__ == "__main__":
    unittest.main()
