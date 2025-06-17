from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dsa, ec, ed25519, rsa
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_ssh_private_key,
)
from cryptography.x509.oid import NameOID

DSA_KEY_TYPE = "dsa"
ECDSA_KEY_TYPE = "ecdsa"
ED25519_KEY_TYPE = "ed25519"
RSA_KEY_TYPE = "rsa"
ED25519_SK_KEY_TYPE = "ed25519-sk"  # not supported?
ECDSA_SK_KEY_TYPE = "ecdsa-sk"  # not supported?


def key_to_str(key) -> str:
    if isinstance(key, ec.EllipticCurvePrivateKey):
        return ECDSA_KEY_TYPE
    if isinstance(key, ed25519.Ed25519PrivateKey):
        return ED25519_KEY_TYPE
    if isinstance(key, rsa.RSAPrivateKey):
        return RSA_KEY_TYPE
    if isinstance(key, dsa.DSAPrivateKey):
        return DSA_KEY_TYPE

    raise ValueError(f"Unsupported key type: {type(key)}")


def generate_ssh_key_pair(key_type: str = ED25519_KEY_TYPE) -> dict:
    """Generate private and public SSH keys"""

    if key_type not in (ED25519_KEY_TYPE, RSA_KEY_TYPE):
        raise ValueError(f"Key type '{key_type}' not supported.")

    if key_type == RSA_KEY_TYPE:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    else:
        private_key = ed25519.Ed25519PrivateKey.generate()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return {
        "private": private_bytes.decode(),
        "public": _generate_public_key_from_ssh_private(private_key),
        "key_type": key_type,
    }


def generate_ssh_public_key(private: str, is_ssl=False) -> dict:
    try:
        private_key = load_ssh_private_key(str.encode(private), None)
    except ValueError as ex:
        if "Not OpenSSH" in str(ex):
            private_key = load_pem_private_key(str.encode(private), None)
        else:
            raise ex
    return {
        "private": private,
        "key_type": key_to_str(private_key),
        "public": _generate_public_key_from_ssh_private(private_key),
    }


def _generate_public_key_from_ssh_private(private_key) -> str:
    public_key = private_key.public_key()
    return public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode()


def generate_azure_keypair() -> dict:
    """Generate a self-signed PEM file that can be used by Azure.
    This is very similar to generate_ssl_key_pair but Azure wants a
    very specific format that generate_ssl_key_pair doesn't generate.

    Making a new method seems more sensible than trying to if/else around
    in the existing method overmuch.
    """

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Thousand Oaks"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Datacoves"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Datacoves"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=5 * 365))
        .sign(key, hashes.SHA256())
    )

    return {
        "private": key.private_bytes(
            encoding=serialization.Encoding.PEM,
            encryption_algorithm=serialization.NoEncryption(),
            format=serialization.PrivateFormat.TraditionalOpenSSL,
        ).decode(),
        "public": cert.public_bytes(
            encoding=serialization.Encoding.PEM,
        ).decode(),
        "key_type": RSA_KEY_TYPE,
    }


def generate_ssl_key_pair(key_type: str = RSA_KEY_TYPE) -> dict:
    """Generate private and public OpenSSL keys"""

    if key_type != RSA_KEY_TYPE:
        raise ValueError(f"Key type '{key_type}' not supported.")

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return {
        "private": private_bytes.decode(),
        "key_type": key_type,
        "public": _generate_public_key_from_ssl_private(private_key),
    }


def generate_ssl_public_key(private: str) -> dict:
    if "-----BEGIN OPENSSH PRIVATE KEY-----" in private:
        private_key = load_ssh_private_key(str.encode(private), None)
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        private = pem.decode("utf-8")

    private_key = load_pem_private_key(str.encode(private), None)

    return {
        "private": private,
        "key_type": key_to_str(private_key),
        "public": _generate_public_key_from_ssl_private(private_key),
    }


def _generate_public_key_from_ssl_private(private_key) -> str:
    public_key = private_key.public_key()
    public_str = (
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
        .strip()
    )
    if public_str.startswith("--"):  # strip -----BEGIN PUBLIC KEY-----
        public_key_lines = public_str.split("\n")
        public_str = "".join(public_key_lines[1:-1])
    return public_str
