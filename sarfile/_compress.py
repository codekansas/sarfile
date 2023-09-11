"""Defines utility functions for compressing a folder to a sarfile."""

import os
from pathlib import Path
from typing import Collection


def _include_file(
    file: str | Path,
    only_extensions: Collection[str] | None,
    exclude_extensions: Collection[str] | None,
) -> bool:
    if not os.path.isfile(file):
        return False
    if only_extensions is not None and Path(file).suffix not in only_extensions:
        return False
    if exclude_extensions is not None and Path(file).suffix in exclude_extensions:
        return False
    return True


def get_files_to_pack(
    root_dir: str | Path,
    only_extensions: Collection[str] | None = None,
    exclude_extensions: Collection[str] | None = None,
) -> tuple[Path, list[tuple[str, int]]]:
    root_dir = Path(root_dir)
    file_chunks: list[tuple[str, int]] = []
    only_extension_set = set() if only_extensions is None else set(only_extensions)
    exclude_extension_set = set() if exclude_extensions is None else set(exclude_extensions)
    for file_path in root_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if only_extensions is not None and file_path.suffix not in only_extension_set:
            continue
        if exclude_extensions is not None and file_path.suffix in exclude_extension_set:
            continue
        num_bytes = file_path.stat().st_size
        file_chunks.append((str(file_path.relative_to(root_dir)), num_bytes))
    return root_dir, sorted(file_chunks)


def get_file_sizes(
    files: Collection[str | Path],
    only_extensions: Collection[str] | None = None,
    exclude_extensions: Collection[str] | None = None,
) -> tuple[Path, list[tuple[str, int]]]:
    files = [str(file) for file in files if _include_file(file, only_extensions, exclude_extensions)]
    common_prefix = Path(os.path.dirname(os.path.commonprefix(files)))
    file_paths = [Path(file).relative_to(common_prefix) for file in files]
    return common_prefix, [(str(file), file.stat().st_size) for file in file_paths]
