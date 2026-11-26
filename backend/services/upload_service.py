"""
upload_service.py
─────────────────
Handles safe ZIP extraction, file-tree scanning, and read-only file content
retrieval.

Security guarantees
-------------------
* ZIP slip / path-traversal: Every member path is resolved against the target
  directory; members that resolve outside it are rejected immediately.
* Absolute / dotdot paths: Rejected before resolution.
* Max archive size: Enforced both by the router (Content-Length header) and by
  tracking cumulative uncompressed bytes during extraction (zip-bomb guard).
* No code is executed at any point.
* User files are never modified.
"""

import os
import uuid
import zipfile
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from models.upload import FileNode, UploadResponse

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

MAX_UNCOMPRESSED_BYTES = 150 * 1024 * 1024   # 150 MB safety ceiling (zip-bomb)
MAX_ZIP_SIZE_BYTES     = 25  * 1024 * 1024   # 25 MB compressed upload limit

SUPPORTED_EXTENSIONS: set[str] = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".html", ".css", ".java", ".c", ".cpp",
}

SKIP_DIRS: set[str] = {
    "node_modules", ".git", "__pycache__",
    "venv", ".venv", "dist", ".vite",
    "build", ".idea", ".vscode",
}

EXTENSION_LANGUAGE_MAP: Dict[str, str] = {
    ".py":   "Python",
    ".js":   "JavaScript",
    ".jsx":  "JavaScript (JSX)",
    ".ts":   "TypeScript",
    ".tsx":  "TypeScript (TSX)",
    ".html": "HTML",
    ".css":  "CSS",
    ".java": "Java",
    ".c":    "C",
    ".cpp":  "C++",
}

# Root for all extracted projects (relative to backend/ cwd)
TEMP_UPLOADS_ROOT = Path("temp_uploads")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_extract(zf: zipfile.ZipFile, target_dir: Path) -> None:
    """
    Extract all members of *zf* into *target_dir* while blocking:
      • absolute paths  (starts with "/" or drive letter)
      • path-traversal  (any component is "..")
      • zip bombs       (cumulative uncompressed size > MAX_UNCOMPRESSED_BYTES)
    """
    total_uncompressed = 0

    for member in zf.infolist():
        # --- reject dangerous member names ---------------------------------
        member_path = member.filename

        # Reject absolute and Windows absolute paths
        if os.path.isabs(member_path) or member_path.startswith(("/", "\\")):
            raise ValueError(f"Rejected: absolute path in archive: {member_path!r}")

        parts = Path(member_path).parts
        if ".." in parts:
            raise ValueError(f"Rejected: path traversal in archive: {member_path!r}")

        # --- zip-bomb guard ------------------------------------------------
        total_uncompressed += member.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise ValueError(
                f"Archive uncompressed size exceeds {MAX_UNCOMPRESSED_BYTES // (1024*1024)} MB – "
                "possible zip bomb rejected."
            )

        # --- resolve final destination and confirm it stays inside target --
        dest = (target_dir / member_path).resolve()
        if not str(dest).startswith(str(target_dir.resolve())):
            raise ValueError(
                f"Rejected: member {member_path!r} resolves outside target directory."
            )

        # --- extract safely ------------------------------------------------
        if member.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(dest, "wb") as dst:
                dst.write(src.read())


def _build_tree(
    directory: Path,
    root: Path,
    language_counts: Dict[str, int],
) -> Tuple[List[FileNode], int, int]:
    """
    Recursively scan *directory* (rooted at *root* for relative-path display).

    Returns
    -------
    nodes           : list of FileNode for this directory level
    total_files     : total file count under this node
    supported_count : count of files with SUPPORTED_EXTENSIONS
    """
    nodes: List[FileNode] = []
    total = 0
    supported = 0

    try:
        entries = sorted(directory.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    except PermissionError:
        return nodes, total, supported

    for entry in entries:
        rel = entry.relative_to(root).as_posix()

        if entry.is_dir():
            if entry.name in SKIP_DIRS:
                continue
            children, sub_total, sub_sup = _build_tree(entry, root, language_counts)
            nodes.append(FileNode(
                name=entry.name,
                path=rel,
                type="directory",
                children=children,
            ))
            total     += sub_total
            supported += sub_sup

        elif entry.is_file():
            total += 1
            ext = entry.suffix.lower()
            is_supported = ext in SUPPORTED_EXTENSIONS
            if is_supported:
                supported += 1
                lang = EXTENSION_LANGUAGE_MAP[ext]
                language_counts[lang] = language_counts.get(lang, 0) + 1

            nodes.append(FileNode(
                name=entry.name,
                path=rel,
                type="file",
                extension=ext if ext else None,
                supported=is_supported,
            ))

    return nodes, total, supported


# ── Public API ───────────────────────────────────────────────────────────────

def process_upload(zip_bytes: bytes, original_filename: str) -> UploadResponse:
    """
    Validate, extract and scan a ZIP archive.

    Parameters
    ----------
    zip_bytes         : raw bytes of the uploaded .zip file
    original_filename : original filename provided by the client

    Returns
    -------
    UploadResponse    : structured project info + file tree
    """
    if len(zip_bytes) > MAX_ZIP_SIZE_BYTES:
        raise ValueError(
            f"File too large. Maximum allowed size is {MAX_ZIP_SIZE_BYTES // (1024*1024)} MB."
        )

    # Derive project name from the filename (strip .zip)
    project_name = Path(original_filename).stem or "uploaded_project"
    project_id   = str(uuid.uuid4())

    target_dir = TEMP_UPLOADS_ROOT / project_id
    target_dir.mkdir(parents=True, exist_ok=True)

    # --- Validate it's actually a ZIP file ---------------------------------
    try:
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            _safe_extract(zf, target_dir)
    except zipfile.BadZipFile:
        raise ValueError("Uploaded file is not a valid ZIP archive.")

    logger.info("Extracted project '%s' (id=%s) to %s", project_name, project_id, target_dir)

    # --- Scan the extracted tree -------------------------------------------
    language_counts: Dict[str, int] = {}
    file_tree, total_files, supported_count = _build_tree(
        target_dir, target_dir, language_counts
    )

    return UploadResponse(
        project_id=project_id,
        project_name=project_name,
        total_files=total_files,
        supported_files_count=supported_count,
        language_breakdown=language_counts,
        file_tree=file_tree,
    )


def get_project_dir(project_id: str) -> Path:
    """Return the extraction directory for a known project_id."""
    return TEMP_UPLOADS_ROOT / project_id


def get_file_content(project_id: str, relative_path: str) -> Dict:
    """
    Read a source file from an extracted project.

    Security
    --------
    * Resolves the final path and ensures it is strictly inside the project dir.
    * Never executes or imports the file.
    * Returns lines as plain strings with line numbers.
    """
    project_dir = (TEMP_UPLOADS_ROOT / project_id).resolve()

    if not project_dir.exists():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    # Strip any leading slashes the client may have sent
    clean_path = relative_path.lstrip("/\\")
    if ".." in Path(clean_path).parts:
        raise PermissionError("Path traversal not allowed.")

    target = (project_dir / clean_path).resolve()

    if not str(target).startswith(str(project_dir)):
        raise PermissionError("Access denied: path resolves outside project directory.")

    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"File '{relative_path}' not found in project.")

    ext  = target.suffix.lower()
    lang = EXTENSION_LANGUAGE_MAP.get(ext, "plaintext")

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise IOError(f"Could not read file: {exc}") from exc

    lines = content.splitlines()

    return {
        "path":        clean_path,
        "language":    lang,
        "lines":       lines,
        "total_lines": len(lines),
    }
