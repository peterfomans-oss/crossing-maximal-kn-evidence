#!/usr/bin/env python3
"""Public-release checks with no third-party dependencies."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "README.zh-CN.md",
    "CLAIMS.md",
    "EVIDENCE_LEVELS.md",
    "REPRODUCE.md",
    "OPEN_OBLIGATIONS.md",
    "DATA_AND_PROVENANCE.md",
    "AI_ASSISTANCE.md",
    "AUTHORS.md",
    "THIRD_PARTY_NOTICES.md",
    "CONTRIBUTING.md",
    "CITATION.cff.template",
    "LICENSES/README.md",
    "proofs/README.md",
    "certificates/README.md",
    "computations/README.md",
    "solver/README.md",
    "audits/README.md",
    "research/README.md",
)

EXPECTED_SOLVER_RESULTS = {
    "computations/safe-no-prefix/k14/final-result.json":
        "32affac3edb48da546fc57a518fb8bca3d77b1f18adb69d10e584e7da9e4abad",
    "computations/safe-no-prefix/k15/final-result.json":
        "4c69c551566203434aca6297de0f0180682cfa8451d0f5ecda6f088c7f935233",
    "computations/safe-no-prefix/k16/final-result.json":
        "7fbb430aaba9761372840f08de315c3d8a7fcaf1781c69c8a64f079df116c5d3",
    "computations/safe-no-prefix/k17/final-result.json":
        "9c9abf7012053fa6f064f2d43233e11ec3f274fcb1003b900d6f4910664c5490",
    "computations/historical-prefix-k17/final-result.json":
        "04a2f88f98ef3d5303574928e273073eab16dad51ebe88175a8760e38b093105",
}

BANNED_SUFFIXES = {
    ".7z", ".a", ".dll", ".dylib", ".exe", ".gz", ".key", ".o",
    ".obj", ".pem", ".pyd", ".pyc", ".so", ".tar", ".zip",
}
BANNED_DIR_NAMES = {
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".venv", "node_modules", "venv", "w64devkit",
}
TEXT_SUFFIXES = {
    "", ".cff", ".gitignore", ".json", ".json0", ".md", ".py", ".template",
    ".txt", ".yaml", ".yml",
}

PRIVACY_PATTERNS = (
    ("Windows user-directory path", re.compile(
        r"(?i)\b[A-Z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\s\"']+"
    )),
    ("macOS user-directory path", re.compile(r"(?i)/" + r"Users/[^/\s\"']+")),
    ("Linux user-directory path", re.compile(r"(?i)/" + r"home/[^/\s\"']+")),
    ("GitHub-style access token", re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("AWS-style access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key block", re.compile(
        "-----BEGIN" + r"\s+(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    )),
)

SENSITIVE_JSON_KEYS = {
    "computername", "host_name", "hostname", "pid", "session_id",
    "session-id", "user_name", "username",
}
REDACTED_VALUES = {"", "[redacted]", "<redacted>", "redacted"}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_files() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(ROOT).parts
    )


def load_json(path: Path, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {relative(path)}: {exc}")
        return None


def check_sensitive_json_values(value: object, rel: str, errors: list[str], trail: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_trail = f"{trail}.{key}"
            if key.lower() in SENSITIVE_JSON_KEYS:
                allowed = child is None or (
                    isinstance(child, str) and child.strip().lower() in REDACTED_VALUES
                )
                if not allowed:
                    errors.append(f"unredacted private metadata in {rel} at {child_trail}")
            check_sensitive_json_values(child, rel, errors, child_trail)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            check_sensitive_json_values(child, rel, errors, f"{trail}[{index}]")


def check_result_record(rel_path: str, expected_hash: str, errors: list[str]) -> None:
    path = ROOT / rel_path
    if not path.is_file():
        errors.append(f"missing solver result: {rel_path}")
        return
    data = load_json(path, errors)
    if not isinstance(data, dict):
        return
    if data.get("result") != "UNSAT":
        errors.append(f"{rel_path}: expected result=UNSAT")
    if data.get("formula_sha256") != expected_hash:
        errors.append(f"{rel_path}: unexpected formula SHA-256")
    evidence = data.get("evidence")
    if not isinstance(evidence, dict):
        errors.append(f"{rel_path}: missing evidence object")
        return
    if evidence.get("verification_level") != "UNCERTIFIED_SOLVER_AUDIT":
        errors.append(f"{rel_path}: verification level must remain UNCERTIFIED_SOLVER_AUDIT")
    if evidence.get("claim_scope") != "HASHED_ENCODED_FORMULA_ONLY":
        errors.append(f"{rel_path}: claim scope must remain HASHED_ENCODED_FORMULA_ONLY")
    if evidence.get("independently_checkable_unsat_proof") is not False:
        errors.append(f"{rel_path}: must explicitly record absence of an independent UNSAT proof")


def check_tree(errors: list[str], warnings: list[str]) -> None:
    for required in REQUIRED_FILES:
        if not (ROOT / required).is_file():
            errors.append(f"missing required file: {required}")

    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if ".git" in rel.parts:
            continue
        if path.is_symlink():
            errors.append(f"symbolic link requires manual review: {rel.as_posix()}")
        lowered_parts = {part.lower() for part in rel.parts}
        blocked = lowered_parts & BANNED_DIR_NAMES
        if blocked:
            errors.append(f"forbidden generated/vendor directory: {rel.as_posix()}")
        if any(part.lower().startswith("cadical-rel-") for part in rel.parts):
            errors.append(f"bundled CaDiCaL source/build tree is not allowed: {rel.as_posix()}")

    for path in iter_files():
        rel = relative(path)
        if path.suffix.lower() in BANNED_SUFFIXES:
            errors.append(f"forbidden binary/archive/key file: {rel}")
            continue
        if path.stat().st_size > 20 * 1024 * 1024:
            warnings.append(f"large file needs manual review (>20 MiB): {rel}")
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != ".gitignore":
            warnings.append(f"unrecognized file type needs manual review: {rel}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            errors.append(f"non-UTF-8 public text file {rel}: {exc}")
            continue
        for label, pattern in PRIVACY_PATTERNS:
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{label} in {rel}:{line}")
        if path.suffix.lower() == ".py":
            try:
                ast.parse(text, filename=rel)
            except SyntaxError as exc:
                errors.append(f"Python syntax error in {rel}:{exc.lineno}: {exc.msg}")
        elif path.suffix.lower() == ".json":
            try:
                parsed = json.loads(text)
                check_sensitive_json_values(parsed, rel, errors)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON {rel}:{exc.lineno}: {exc.msg}")


def check_strict_release(errors: list[str]) -> None:
    license_path = ROOT / "LICENSE"
    if not license_path.is_file() or not license_path.read_text(encoding="utf-8").strip():
        errors.append("strict release requires a nonempty root LICENSE file")
    citation_path = ROOT / "CITATION.cff"
    if not citation_path.is_file():
        errors.append("strict release requires completed CITATION.cff")
    else:
        citation = citation_path.read_text(encoding="utf-8")
        placeholders = ("CHOOSE-", "OWNER/REPOSITORY", "YYYY-MM-DD")
        if any(token in citation for token in placeholders):
            errors.append("CITATION.cff still contains release placeholders")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-release",
        action="store_true",
        help="also require a chosen license and completed CITATION.cff",
    )
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    check_tree(errors, warnings)
    for rel_path, expected_hash in EXPECTED_SOLVER_RESULTS.items():
        check_result_record(rel_path, expected_hash, errors)
    if args.strict_release:
        check_strict_release(errors)
    elif not (ROOT / "LICENSE").exists():
        warnings.append("no public license selected; expected for this candidate, required before release")

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"release preflight: FAIL ({len(errors)} error(s))", file=sys.stderr)
        return 1
    print(f"release preflight: PASS ({len(iter_files())} files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
