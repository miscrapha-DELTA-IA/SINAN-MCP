#!/usr/bin/env python3
"""Validate and build a synthetic-only Agent Plugins portable ZIP.

PRE-FLIGHT ONLY: no website calls, credentials, automatic upload, or publication.
The OpenAI directory rejects trial/demo-only plugins; a syntactically valid
archive is not evidence of eligibility, verified publisher, or review approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "plugin-package"
EXPECTED_MCP = "https://sinan-mcp-public-preview.onrender.com/mcp"
SITE = "https://sinan-mcp-public-preview.onrender.com"
AUTHOR = "Raphael Múcio Teixeira Cabral de Pina Bulhões Di Giorgio"
EMAIL = "miscrapha@gmail.com"
FILE_NAMES = ("plugin.json", "mcp.json", "assets/icon.svg")
ICON_MIN_SIZE = 48
# Stable metadata for reproducible byte-for-byte archives.
ZIP_TIME = (2026, 11, 5, 0, 0, 0)


class PackageError(ValueError):
    """An invalid or unsafe artifact must not be packed."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise PackageError(reason)


def is_https_url(value: object, *, hostname: str | None = None) -> bool:
    if not isinstance(value, str):
        return False
    parts = urlsplit(value)
    return (parts.scheme == "https" and bool(parts.hostname) and not parts.username
            and not parts.password and not parts.query and not parts.fragment
            and not any(c.isspace() for c in value)
            and (hostname is None or parts.hostname == hostname))


def validate(package: Path = PACKAGE) -> dict:
    require(package.is_dir(), "Missing plugin-package/ directory")
    require(all((package / rel).is_file() for rel in FILE_NAMES),
            "Missing a required portable manifest/icon asset")
    manifest = json.loads((package / "plugin.json").read_text(encoding="utf-8"))
    mcp = json.loads((package / "mcp.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "docs/public-mcp-contract-v1.json").read_text(encoding="utf-8"))
    require(manifest.get("$schema") == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "Invalid portable plugin schema")
    require(mcp.get("$schema") == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
            "Invalid portable MCP schema")
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", manifest.get("name", "")) is not None,
            "Invalid portable plugin name")
    require(len(manifest["name"]) <= 64, "Plugin name too long")
    require(re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")) is not None,
            "Missing semantic package version")
    author = manifest.get("author", {})
    require(author.get("name") == AUTHOR and author.get("email") == EMAIL,
            "Unauthorized publisher identity or support contact")
    require(is_https_url(author.get("url")), "Invalid publisher URL")
    require(is_https_url(manifest.get("homepage")), "Invalid homepage")
    require(manifest.get("license") == "MIT", "Unexpected source license")
    require(contract.get("nature") == "synthetic-only" and contract.get("live_data_available") is False,
            "Source contract is no longer strictly synthetic")
    require(contract.get("patient_records_available") is False and contract.get("supports_arbitrary_sql") is False,
            "Unsafe public source contract")

    extensions = manifest.get("extensions", {}).get("com.openai", {})
    info = extensions.get("interface", {})
    for key, limit in (("displayName", 30), ("shortDescription", 30),
                       ("longDescription", 4000), ("developerName", 80)):
        require(isinstance(info.get(key), str) and 0 < len(info[key]) <= limit,
                f"Invalid listing field: {key}")
    require(info["developerName"] == AUTHOR, "Publisher identity mismatch")
    for field, route in (("websiteURL", "/sobre"), ("supportURL", "/suporte"),
                         ("privacyPolicyURL", "/privacidade"),
                         ("termsOfServiceURL", "/termos")):
        value = info.get(field)
        require(is_https_url(value, hostname="sinan-mcp-public-preview.onrender.com"),
                f"Invalid public HTTPS listing URL {field}")
        require(value == SITE + route and len(value) <= 1024,
                f"Unexpected {field} destination")
    require(info.get("category") == "Developer Tools", "Check category in the publication portal")
    require(isinstance(info.get("capabilities"), list) and 0 < len(info["capabilities"]) <= 20,
            "Invalid capabilities")
    require(isinstance(info.get("defaultPrompt"), list) and len(info["defaultPrompt"]) <= 3,
            "Invalid default prompts")
    require(all(isinstance(p, str) and 0 < len(p) <= 128 for p in info["defaultPrompt"]),
            "A default prompt is over 128 chars")

    for visual in ("logo", "composerIcon"):
        value = info.get(visual)
        require(value == "./assets/icon.svg", f"{visual} references an unknown file")
    svg = ET.fromstring((package / "assets/icon.svg").read_text(encoding="utf-8"))
    require(svg.tag == "{http://www.w3.org/2000/svg}svg", "Invalid SVG root")
    require(int(svg.attrib.get("width", "0")) >= ICON_MIN_SIZE
            and int(svg.attrib.get("height", "0")) >= ICON_MIN_SIZE,
            "Icon is smaller than 48x48")
    require(svg.attrib.get("viewBox") == "0 0 256 256", "Icon must have a square viewBox")

    servers = mcp.get("mcpServers")
    require(isinstance(servers, dict) and set(servers) == {"sinan-reference"},
            "Exactly one specific public MCP server is allowed")
    server = servers["sinan-reference"]
    require(server.get("type") == "streamable-http" and server.get("url") == EXPECTED_MCP,
            "Public MCP endpoint must be the deployed synthetic-only URL")
    require(server.get("extensions", {}).get("com.openai", {}).get("auth", {}).get("type") == "none",
            "Anonymous mode only allowed for the synthetic public preview")
    require(not any(key in server for key in ("headers", "env", "command", "args", "clientSecret", "token")),
            "No secret-bearing headers, local commands or tokens in a portable remote MCP")
    require("apps" not in extensions and "hooks" not in extensions,
            "Desktop hooks / apps are not eligible for public ZIP submission")

    review = extensions.get("review", {})
    cases = review.get("test_cases", {})
    positive, negative = cases.get("positive", []), cases.get("negative", [])
    require(len(positive) == 5 and len(negative) == 3,
            "Review draft must list exactly 5 positive and 3 negative tests")
    allowed = set(contract["public_tools"])
    for case in positive:
        require(all(isinstance(case.get(k), str) and case[k].strip()
                    for k in ("description", "prompt", "tools_triggered", "expected_behavior")),
                "Positive case has incomplete review metadata")
        used = {x.strip() for x in case["tools_triggered"].split(",")}
        require(used.issubset(allowed), "A review case calls a tool absent from synthetic public contract")
    for case in negative:
        require(all(isinstance(case.get(k), str) and case[k].strip()
                    for k in ("description", "prompt")),
                "Negative case has incomplete review metadata")
    require("demo_recording_url" not in review,
            "Do not publish a fabricated or unverified review video link")
    require(review.get("commerce") is False, "No commerce in the public demo")
    require(not any((package / name).exists() for name in ("skills", "hooks", ".app.json", ".mcp.json")),
            "This draft must contain only a portable remote MCP, with no local plugins or skills")

    return {"name":manifest["name"], "version":manifest["version"],
            "files":list(FILE_NAMES), "positive_cases":len(positive),
            "negative_cases":len(negative), "endpoint":EXPECTED_MCP,
            "ready_for_directory_submission":False}


def build(destination: Path, package: Path = PACKAGE) -> dict:
    details = validate(package)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w") as archive:
        for name in FILE_NAMES:
            data = (package / name).read_bytes()
            entry = ZipInfo(name, date_time=ZIP_TIME)
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, data, compress_type=ZIP_DEFLATED, compresslevel=9)
    with ZipFile(destination, "r") as archive:
        require(tuple(archive.namelist()) == FILE_NAMES, "Archive member structure mismatch")
        require(archive.testzip() is None, "ZIP CRC failed")
    details["zip_path"] = str(destination)
    details["zip_bytes"] = destination.stat().st_size
    details["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
    return details


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Only validate package; do not write a ZIP")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "dist" / "sinan-reference-lab-preflight-0.1.0.zip")
    args = parser.parse_args()
    try:
        result = validate() if args.check else build(args.out)
    except (PackageError, ValueError, KeyError, OSError, ET.ParseError) as exc:
        print("FAILED PRE-FLIGHT:", str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("PRE-FLIGHT ONLY: do not submit for directory review until eligibility, "
          "domain ownership, verified identity and real video evidence are complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
