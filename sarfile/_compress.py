"""Defines utility functions for compressing a folder to a sarfile."""

import shutil
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


def compress(
    input_dir: str | Path,
    output_path: str | Path,
    only_extensions: Collection[str] | None = None,
    exclude_extensions: Collection[str] | None = None,
) -> None:
    """Compresses a given folder to a streamable dataset (SDS).

    Args:
        input_dir: The directory to compress.
        output_path: The root directory to write the shards to.
        only_extensions: If not None, only files with these extensions will be
            included.
        exclude_extensions: If not None, files with these extensions will be
            excluded.
    """
    only_extension_set = set(only_extensions) if only_extensions is not None else None
    exclude_extension_set = set(exclude_extensions) if exclude_extensions is not None else None
    input_dir, output_path = Path(input_dir).resolve(), Path(output_path).resolve()

    # Compresses each of the files.
    file_paths = _get_files_to_compress(input_dir, only_extension_set, exclude_extension_set)
    header = Header(file_paths)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    with open(output_path, "wb") as f:
        # Writes the header.
        f.write(MAGIC)
        header.write(f)

        # Writes each of the files.
        for file_path, _ in file_paths:
            with open(input_dir / file_path, "rb") as f_in:
                shutil.copyfileobj(f_in, f)
