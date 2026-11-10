"""Create local-only credentials and TLS material without printing secrets."""

import os
import secrets
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    target = ROOT / ".env"
    if target.exists():
        raise SystemExit(".env already exists; refusing to replace runtime credentials")
    tls = ROOT / ".data" / "tls"
    tls.mkdir(parents=True, exist_ok=True, mode=0o700)

    def openssl(*args: str) -> None:
        subprocess.run(["openssl", *args], cwd=tls, check=True, capture_output=True)

    openssl(
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-days",
        "365",
        "-subj",
        "/CN=RAG local development CA",
        "-keyout",
        "ca.key",
        "-out",
        "root-ca.pem",
    )
    for name, subject in (
        ("esnode", "/CN=node-0.example.com/OU=SSL/O=Test/L=Test/C=DE"),
        ("kirk", "/CN=kirk/OU=client/O=client/L=test/C=de"),
    ):
        openssl(
            "req",
            "-new",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-subj",
            subject,
            "-keyout",
            f"{name}-key.pem",
            "-out",
            f"{name}.csr",
        )
        ext = tls / f"{name}.ext"
        ext.write_text("subjectAltName=DNS:opensearch,DNS:node-0.example.com,DNS:localhost\n")
        openssl(
            "x509",
            "-req",
            "-in",
            f"{name}.csr",
            "-CA",
            "root-ca.pem",
            "-CAkey",
            "ca.key",
            "-CAcreateserial",
            "-days",
            "365",
            "-extfile",
            ext.name,
            "-out",
            f"{name}.pem",
        )
    for path in tls.glob("*.pem"):
        path.chmod(0o644)  # Container UID can read; parent directory stays owner-only.
    (tls / "ca.key").chmod(0o600)
    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
        for key in ("POSTGRES_PASSWORD", "RABBITMQ_PASSWORD", "OPENSEARCH_INITIAL_ADMIN_PASSWORD"):
            stream.write(f"{key}=Aa1_{secrets.token_hex(24)}\n")
    print("Created local .env and TLS material. Keep .env and .data private and untracked.")


if __name__ == "__main__":
    main()
