"""Defines utility functions for compressing a folder to a sarfile."""

import shutil
from typing import Union
from pathlib import Path
from typing import Collection

from sarfile._constants import MAGIC
from sarfile._header import Header


def _get_files_to_compress(
    input_dir: Path,
    only_extension_set: set[str] | None,
    exclude_extension_set: set[str] | None,
) -> list[tuple[str, int]]:
    file_chunks: list[tuple[str, int]] = []
    for file_path in input_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if only_extension_set is not None and file_path.suffix not in only_extension_set:
            continue
        if exclude_extension_set is not None and file_path.suffix in exclude_extension_set:
            continue
        num_bytes = file_path.stat().st_size
        file_chunks.append((str(file_path.relative_to(input_dir)), num_bytes))
    return sorted(file_chunks)


def _get_files_to_compress(
    input_dir: Path,
    only_extension_set: set[str] | None,
    exclude_extension_set: set[str] | None,
) -> list[tuple[str, int]]:
    file_chunks: list[tuple[str, int]] = []
    for file_path in input_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if only_extension_set is not None and file_path.suffix not in only_extension_set:
            continue
        if exclude_extension_set is not None and file_path.suffix in exclude_extension_set:
            continue
        num_bytes = file_path.stat().st_size
        file_chunks.append((str(file_path.relative_to(input_dir)), num_bytes))
    return sorted(file_chunks)


def _get_files_to_pack(root_dir: Union[str, Path]) -> list[tuple[Path, int]]:
    asdf


def _get_files_to_pack(root_dir):
    asdf
