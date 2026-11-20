from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

key = Ed25519PrivateKey.generate()
private_pem = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
public_pem = (
    key.public_key()
    .public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode()
)


def env_line(name: str, pem: str) -> str:
    # El .env necesita todo en una línea: los saltos de línea se escriben como \n
    return f'{name}="' + pem.strip().replace("\n", "\\n") + '"'


print(env_line("APP_JWT_PRIVATE_KEY", private_pem))
print(env_line("APP_JWT_PUBLIC_KEY", public_pem))
