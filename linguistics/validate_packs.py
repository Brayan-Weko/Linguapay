"""Validation script for LinguaPay language packs against lang-pack.schema.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schema" / "lang-pack.schema.json"
PACKS_DIR = ROOT / "packs"


def validate_pack(pack_path: Path, schema: dict) -> list[str]:
    errors: list[str] = []
    with pack_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if jsonschema is not None:
        validator = jsonschema.Draft202012Validator(schema)
        for err in validator.iter_errors(data):
            loc = ".".join(str(p) for p in err.path) or "<root>"
            errors.append(f"[{pack_path.name}] Schema error at {loc}: {err.message}")
    else:
        for req in schema.get("required", []):
            if req not in data:
                errors.append(f"[{pack_path.name}] Missing required top-level key: {req}")

    # Semantic checks: duplicate IDs and template placeholder preservation
    seen_ids: set[str] = set()
    for entry in data.get("entries", []):
        eid = entry.get("id", "")
        if eid in seen_ids:
            errors.append(f"[{pack_path.name}] Duplicate entry id: {eid}")
        seen_ids.add(eid)
        if entry.get("validation_status") == "CERTIFIED" and not entry.get("validated_by"):
            errors.append(f"[{pack_path.name}] Entry {eid} is CERTIFIED but validated_by is null")

    for tpl in data.get("templates", []):
        tid = tpl.get("id", "")
        target = tpl.get("target_template", "")
        for tok in tpl.get("required_tokens", []):
            if tok not in target:
                errors.append(f"[{pack_path.name}] Template {tid} missing token {tok} in target_template")

    return errors


def main() -> int:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    pack_files = sorted(PACKS_DIR.glob("*.json"))
    if not pack_files:
        print("No language packs found in", PACKS_DIR)
        return 1

    all_errors: list[str] = []
    for pack_file in pack_files:
        errs = validate_pack(pack_file, schema)
        with pack_file.open("r", encoding="utf-8") as f:
            pdata = json.load(f)
        entries = pdata.get("entries", [])
        certified = sum(1 for e in entries if e.get("validation_status") == "CERTIFIED")
        print(
            f"- {pack_file.name}: {len(entries)} entries "
            f"({certified} CERTIFIED, {len(entries) - certified} pending review), "
            f"{len(pdata.get('templates', []))} templates"
        )
        all_errors.extend(errs)

    if all_errors:
        print("\nValidation FAILED:")
        for e in all_errors:
            print("  ERROR:", e)
        return 1

    print("\nAll language packs passed schema and semantic checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

