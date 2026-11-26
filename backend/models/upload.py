from pydantic import BaseModel
from typing import Dict, List, Optional


class FileNode(BaseModel):
    name: str
    path: str                    # relative path from project root
    type: str                    # "file" or "directory"
    extension: Optional[str] = None
    supported: bool = False
    children: Optional[List["FileNode"]] = None  # only for directories

    model_config = {"populate_by_name": True}


FileNode.model_rebuild()         # required for self-referential model


class UploadResponse(BaseModel):
    project_id: str
    project_name: str
    total_files: int
    supported_files_count: int
    language_breakdown: Dict[str, int]
    file_tree: List[FileNode]


class FileContentResponse(BaseModel):
    path: str
    language: str
    lines: List[str]
    total_lines: int
