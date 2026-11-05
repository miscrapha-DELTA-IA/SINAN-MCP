"""Offline, standard-library-only checks for the portable distribution package."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
from zipfile import ZipFile

import pytest

from scripts import build_public_plugin_zip as package


def test_portable_manifest_and_synthetic_remote_scope():
    info = package.validate()
    assert info["name"] == "sinan-reference-lab"
    assert info["version"] == "0.1.0"
    assert info["endpoint"] == "https://sinan-mcp-public-preview.onrender.com/mcp"
    assert info["ready_for_directory_submission"] is False
    assert info["positive_cases"] == 5
    assert info["negative_cases"] == 3
    assert info["files"] == ["plugin.json", "mcp.json", "assets/icon.svg"]


def test_zip_is_deterministic_and_contains_only_expected_members(tmp_path):
    first, second = tmp_path / "one.zip", tmp_path / "two.zip"
    one = package.build(first)
    two = package.build(second)
    assert one["sha256"] == two["sha256"]
    assert one["zip_bytes"] < 100 * 1024 * 1024
    with ZipFile(first) as archive:
        assert archive.namelist() == ["plugin.json", "mcp.json", "assets/icon.svg"]
        assert archive.testzip() is None
        plugin = json.loads(archive.read("plugin.json"))
        mcp = json.loads(archive.read("mcp.json"))
        assert plugin["author"]["email"] == "miscrapha@gmail.com"
        assert mcp["mcpServers"]["sinan-reference"]["url"] == package.EXPECTED_MCP
        assert not any(n.startswith("/") or ".." in Path(n).parts for n in archive.namelist())


def copy_package(tmp_path):
    root = tmp_path / "package"
    shutil.copytree(package.PACKAGE, root)
    return root


def test_rejects_real_data_endpoint_or_local_commands(tmp_path):
    root = copy_package(tmp_path)
    mcp_path = root / "mcp.json"
    mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
    server = mcp["mcpServers"]["sinan-reference"]
    server["url"] = "https://health-data.invalid/mcp"
    mcp_path.write_text(json.dumps(mcp), encoding="utf-8")
    with pytest.raises(package.PackageError, match="synthetic-only URL"):
        package.validate(root)
    server["url"] = package.EXPECTED_MCP
    server["command"] = "python -m sinan_mcp.server"
    mcp_path.write_text(json.dumps(mcp), encoding="utf-8")
    with pytest.raises(package.PackageError, match="local commands"):
        package.validate(root)


def test_rejects_changed_identity_and_fake_video(tmp_path):
    root = copy_package(tmp_path)
    manifest_path = root / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["author"]["email"] = "unverified@example.invalid"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(package.PackageError, match="publisher identity"):
        package.validate(root)
    manifest["author"]["email"] = package.EMAIL
    manifest["extensions"]["com.openai"]["review"]["demo_recording_url"] = "https://example.com/video"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(package.PackageError, match="fabricated"):
        package.validate(root)


def test_rejects_fake_official_url_or_unreferenced_script(tmp_path):
    root = copy_package(tmp_path)
    manifest_path = root / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["extensions"]["com.openai"]["interface"]["websiteURL"] = "https://gov.br.invalid/sinan"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(package.PackageError, match="public HTTPS listing"):
        package.validate(root)
    manifest["extensions"]["com.openai"]["interface"]["websiteURL"] = package.SITE + "/sobre"
    manifest["extensions"]["com.openai"]["hooks"] = "./hooks/start.sh"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(package.PackageError, match="hooks"):
        package.validate(root)


def test_no_extra_archive_files_or_secret_headers():
    p = json.loads((package.PACKAGE / "plugin.json").read_text(encoding="utf-8"))
    m = json.loads((package.PACKAGE / "mcp.json").read_text(encoding="utf-8"))
    assert "apps" not in p["extensions"]["com.openai"]
    assert "hooks" not in p["extensions"]["com.openai"]
    assert "skills" not in p
    assert len(m["mcpServers"]) == 1
    server = next(iter(m["mcpServers"].values()))
    assert not any(k in server for k in ("headers", "token", "clientSecret", "env", "command"))
