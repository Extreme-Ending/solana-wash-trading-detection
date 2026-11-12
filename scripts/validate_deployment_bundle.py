"""Fail closed when a Firebase static bundle contains research/private material."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FORBIDDEN_NAMES = {
    ".env",
    "AGENTS.md",
    "CODEX_IMPLEMENTATION_PROMPT.md",
    "CODEX_PHASE_PROMPTS.md",
    "nft.csv",
    "nft_trades.csv",
}
FORBIDDEN_SUFFIXES = {".csv", ".joblib", ".pem", ".p12", ".pfx"}
SECRET_PATTERNS = {
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Google API key": re.compile(rb"AIza[0-9A-Za-z_-]{35}"),
    "GitHub token": re.compile(rb"gh[opsu]_[0-9A-Za-z]{20,}"),
}


def validate_bundle(bundle: Path) -> list[Path]:
    if not bundle.is_dir() or not (bundle / "index.html").is_file():
        raise ValueError(f"{bundle} must be a built Vite directory containing index.html")
    paths = sorted(bundle.rglob("*"))
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"symbolic links are not permitted in the bundle: {path.relative_to(bundle)}")
    files = [path for path in paths if path.is_file()]
    for path in files:
        relative = path.relative_to(bundle)
        if any(part in {"data", "artifacts", "models", ".agents"} for part in relative.parts):
            raise ValueError(f"forbidden bundle path: {relative}")
        if (
            path.name in FORBIDDEN_NAMES
            or path.name.startswith(".env")
            or (path.name.startswith("CODEX_") and path.suffix.casefold() == ".md")
            or path.suffix.casefold() in FORBIDDEN_SUFFIXES
        ):
            raise ValueError(f"forbidden bundle file: {relative}")
        content = path.read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                raise ValueError(f"possible {label} in bundle file: {relative}")
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    files = validate_bundle(args.bundle.resolve())
    print(f"Deployment bundle validation: PASS ({len(files)} files checked)")


if __name__ == "__main__":
    main()
