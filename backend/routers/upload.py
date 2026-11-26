"""
routers/upload.py
─────────────────
POST /api/upload          – accept and validate a ZIP, return project tree
GET  /api/project/{id}/file?path=... – return read-only file content
"""

import logging
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from models.upload import FileContentResponse, UploadResponse
from services.upload_service import (
    MAX_ZIP_SIZE_BYTES,
    get_file_content,
    process_upload,
)

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/zip",
    "application/x-zip-compressed",
    "application/x-zip",
    "multipart/x-zip",
    "application/octet-stream",   # some browsers send this for .zip
}


@router.post("/api/upload", response_model=UploadResponse)
async def upload_project(file: UploadFile = File(...)):
    """
    Accept a .zip file, validate it, extract it safely into an isolated
    temp directory, and return a hierarchical project summary.
    """
    # --- Extension check ---------------------------------------------------
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Only .zip files are accepted.",
        )

    # --- Read file into memory (bounded by MAX_ZIP_SIZE_BYTES + 1 byte) ----
    max_read = MAX_ZIP_SIZE_BYTES + 1
    zip_bytes = await file.read(max_read)

    if len(zip_bytes) > MAX_ZIP_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {MAX_ZIP_SIZE_BYTES // (1024 * 1024)} MB limit.",
        )

    if len(zip_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # --- Delegate to service layer -----------------------------------------
    try:
        result = process_upload(zip_bytes, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during upload processing")
        raise HTTPException(status_code=500, detail="Internal error processing upload.")

    return result


@router.get("/api/project/{project_id}/file", response_model=FileContentResponse)
async def get_project_file(
    project_id: str,
    path: str = Query(..., description="Relative path of the file within the project"),
):
    """
    Return read-only file contents (with line numbers) for a file inside an
    already-uploaded project.  The path is strictly validated to stay inside
    the project directory (zip-slip / traversal safe).
    """
    try:
        data = get_file_content(project_id, path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except IOError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return FileContentResponse(**data)
