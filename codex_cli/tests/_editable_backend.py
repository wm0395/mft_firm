from __future__ import annotations

import base64
import csv
import hashlib
import io
import tomllib
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "codex_cli"


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, object] | None = None,
    metadata_directory: str | None = None,
) -> str:
    return _build_archive(Path(wheel_directory), editable=False)


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, object] | None = None,
    metadata_directory: str | None = None,
) -> str:
    return _build_archive(Path(wheel_directory), editable=True)


def get_requires_for_build_wheel(config_settings: dict[str, object] | None = None) -> list[str]:
    return []


def get_requires_for_build_editable(config_settings: dict[str, object] | None = None) -> list[str]:
    return []


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict[str, object] | None = None,
) -> str:
    return _prepare_metadata(Path(metadata_directory))


def prepare_metadata_for_build_editable(
    metadata_directory: str,
    config_settings: dict[str, object] | None = None,
) -> str:
    return _prepare_metadata(Path(metadata_directory))


def _build_archive(wheel_directory: Path, editable: bool) -> str:
    wheel_directory.mkdir(parents=True, exist_ok=True)
    name = _wheel_name()
    records: list[tuple[str, bytes]] = []
    dist_info = _dist_info_dir()
    with zipfile.ZipFile(wheel_directory / name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_name, data in _wheel_entries(editable, dist_info):
            archive.writestr(archive_name, data)
            records.append((archive_name, data))
        archive.writestr(f"{dist_info}/RECORD", _record_contents(records, dist_info))
    return name


def _prepare_metadata(metadata_directory: Path) -> str:
    dist_info = metadata_directory / _dist_info_dir()
    dist_info.mkdir(parents=True, exist_ok=True)
    for name, data in _dist_info_files().items():
        (dist_info / name).write_text(data.decode("utf-8"), encoding="utf-8")
    return dist_info.name


def _wheel_entries(editable: bool, dist_info: str) -> list[tuple[str, bytes]]:
    entries = list(_package_entries())
    if editable:
        entries.append(("mft_codex_cli_editable.pth", f"{PROJECT_ROOT}\n".encode("utf-8")))
    else:
        entries.extend(_source_entries())
    for name, data in _dist_info_files().items():
        entries.append((f"{dist_info}/{name}", data))
    return entries


def _package_entries() -> list[tuple[str, bytes]]:
    entries: list[tuple[str, bytes]] = []
    for path in PACKAGE_ROOT.rglob("*"):
        if _skip_path(path):
            continue
        archive_name = Path("codex_cli", path.relative_to(PACKAGE_ROOT)).as_posix()
        entries.append((archive_name, path.read_bytes()))
    return entries


def _source_entries() -> list[tuple[str, bytes]]:
    entries: list[tuple[str, bytes]] = []
    root_cli = PROJECT_ROOT / "cli.py"
    if root_cli.exists():
        entries.append(("cli.py", root_cli.read_bytes()))
    return entries


def _skip_path(path: Path) -> bool:
    return not path.is_file() or "__pycache__" in path.parts


def _dist_info_files() -> dict[str, bytes]:
    return {
        "METADATA": _metadata_text().encode("utf-8"),
        "WHEEL": _wheel_text().encode("utf-8"),
        "entry_points.txt": _entry_points_text().encode("utf-8"),
    }


def _metadata_text() -> str:
    project = _project_table()
    return "\n".join(
        (
            "Metadata-Version: 2.1",
            f"Name: {project['name']}",
            f"Version: {project['version']}",
            f"Summary: {project['description']}",
            "",
        )
    )


def _wheel_text() -> str:
    return "\n".join(
        (
            "Wheel-Version: 1.0",
            "Generator: codex_cli.tests._editable_backend",
            "Root-Is-Purelib: true",
            "Tag: py3-none-any",
            "",
        )
    )


def _entry_points_text() -> str:
    return "[console_scripts]\nai_code = codex_cli.cli:main\n"


def _record_contents(records: list[tuple[str, bytes]], dist_info: str) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for path, data in records:
        writer.writerow((path, _hash_text(data), len(data)))
    writer.writerow((f"{dist_info}/RECORD", "", ""))
    return buffer.getvalue()


def _hash_text(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"sha256={encoded}"


def _wheel_name() -> str:
    project = _project_table()
    dist = _normalized_name(project["name"])
    version = project["version"]
    return f"{dist}-{version}-py3-none-any.whl"


def _dist_info_dir() -> str:
    project = _project_table()
    dist = _normalized_name(project["name"])
    version = project["version"]
    return f"{dist}-{version}.dist-info"


def _normalized_name(name: str) -> str:
    return name.replace("-", "_")


def _project_table() -> dict[str, str]:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    return {
        "name": str(project["name"]),
        "version": str(project["version"]),
        "description": str(project["description"]),
    }
