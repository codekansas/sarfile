# mypy: disable-error-code="import"
"""Defines the main sarfile API."""

import functools
import shutil
import struct
import tarfile
import warnings
from pathlib import Path
from typing import Any, BinaryIO, Callable, Collection, Iterable, TypeVar

from ._compress import get_file_sizes, get_files_to_pack
from ._constants import MAGIC, PRE_HEADER_SIZE
from ._header import Header
from ._item import TarItem

# Use `tqdm` for showing progress bar when packing files if available.
try:
    import tqdm
except ImportError:
    tqdm = None  # type: ignore[assignment]

# Patch `open` with `smart_open.open` if available.
try:
    from smart_open import open
except ImportError:
    pass

StrPath = str | Path
StrPathIO = str | Path | BinaryIO

T = TypeVar("T")


def _maybe_tqdm(iterable: Iterable[T], **kwargs: Any) -> Iterable[T]:  # noqa: ANN401
    if tqdm is None:
        warnings.warn("tqdm is not installed, so no progress bar will be shown.")
        return iterable
    else:
        return tqdm.tqdm(iterable, **kwargs)


def _maybe_open_sar_read(fp: StrPathIO) -> BinaryIO:
    if isinstance(fp, (str, Path)):
        fpi = open(fp, "rb")
        return fpi
    assert fp.readable(), "File pointer is not readable"
    return fp


def _maybe_open_sar_write(fp: StrPathIO) -> BinaryIO:
    if isinstance(fp, (str, Path)):
        if Path(fp).suffix.lower() != ".sar":
            warnings.warn(f"File name {fp} does not end with `.sar`")
        Path(fp).parent.mkdir(exist_ok=True, parents=True)
        fpi = open(fp, "wb")
        return fpi
    assert fp.writable(), "File pointer mode is not writable"
    return fp


def _maybe_tar_open(fp: StrPathIO, mode: str = "r") -> tarfile.TarFile:
    if isinstance(fp, (str, Path)):
        return tarfile.open(name=fp, mode=mode)
    return tarfile.open(fileobj=fp, mode=mode)


class sarfile:  # noqa: N801
    def __init__(self, fp: StrPathIO) -> None:
        self._fp = fp
        self._header, header_num_bytes = self._read_header()
        self._offsets = self._header._offsets(PRE_HEADER_SIZE + header_num_bytes)

    def _read_header(self) -> tuple[Header, int]:
        with _maybe_open_sar_read(self._fp) as fp:
            if fp.tell() != 0:
                raise ValueError("File pointer must be at the beginning of the file.")
            init_bytes = fp.read(PRE_HEADER_SIZE)
            if init_bytes[: len(MAGIC)] != MAGIC:
                raise IOError("Invalid magic number; this is not a sarfile.")
            header_num_bytes = struct.unpack("Q", init_bytes[len(MAGIC) :])[0]
            header_bytes = fp.read(header_num_bytes)
            return Header.decode(header_bytes), header_num_bytes

    @functools.cached_property
    def names(self) -> list[str]:
        return [name for name, _ in self._header.files]

    @functools.cached_property
    def name_index(self) -> dict[str, int]:
        return {name: i for i, name in enumerate(self.names)}

    def extract(self, name: str) -> BinaryIO:
        raise NotImplementedError

    @classmethod
    def open(cls, fp: StrPathIO) -> "sarfile":
        return cls(fp)

    def __len__(self) -> int:
        return len(self._header.files)

    def __getitem__(self, index: int | str) -> TarItem:
        fp = _maybe_open_sar_read(self._fp)
        if isinstance(index, str):
            index = self.name_index[index]
        name, num_bytes = self._header.files[index]
        fp.seek(self._offsets[index])
        return TarItem(name, num_bytes, fp)

    @classmethod
    def pack_files(
        cls,
        *,
        out: StrPathIO,
        files: Collection[StrPath] | None = None,
        root_dir: StrPath | None = None,
        only_extensions: Collection[str] | None = None,
        exclude_extensions: Collection[str] | None = None,
    ) -> None:
        """Packs a collection of files into a sarfile.

        Args:
            out: The output sarfile to write.
            files: A collection of files to pack. Mutually exclusive with
                ``root_dir``.
            root_dir: The root directory to iteratively search for files to
                pack. Mutually exclusive with ``files``.
            only_extensions: If not None, only files with these extensions
                will be included.
            exclude_extensions: If not None, files with these extensions
                will be excluded.

        Raises:
            ValueError: If both ``files`` and ``root_dir`` are specified, or
                neither are specified, or if no files are found.
        """
        if (root_dir is None) == (files is None):
            raise ValueError("Exactly one of `root_dir` or `files` must be specified.")

        # Gets the file sizes and common prefix directory.
        if root_dir is not None:
            root_dir = Path(root_dir)
            common_prefix, files_with_sizes = get_files_to_pack(root_dir, only_extensions, exclude_extensions)
        elif files is not None:
            common_prefix, files_with_sizes = get_file_sizes(files, only_extensions, exclude_extensions)
        else:
            assert False

        if not files_with_sizes:
            raise ValueError("No files to pack.")

        # Writes all the files to the output sarfile.
        header = Header(files_with_sizes)
        files_iter = _maybe_tqdm(files_with_sizes, desc="Packing files")
        with _maybe_open_sar_write(out) as fpo:
            fpo.write(MAGIC)
            header.write(fpo)
            for file_path, _ in files_iter:
                with open(common_prefix / file_path, "rb") as fpi:
                    shutil.copyfileobj(fpi, fpo)

    @classmethod
    def pack_tar(
        cls,
        *,
        out: StrPathIO,
        tar: StrPathIO,
        include_file: Callable[[str], bool] = lambda _: True,
    ) -> None:
        """Packs a tarfile into a sarfile.

        Args:
            out: The output sarfile to write.
            tar: The tarfile to pack.
            include_file: A function that takes a file name and returns whether
                to include it in the sarfile.
        """
        with _maybe_tar_open(tar) as fpi, _maybe_open_sar_write(out) as fpo:
            files_with_sizes = list(
                filter(
                    lambda i: i[1] > 0,
                    ((m.name, m.size) for m in fpi.getmembers() if include_file(m.name)),
                )
            )
            header = Header(files_with_sizes)
            files_iter = _maybe_tqdm(files_with_sizes, desc="Packing files")
            fpo.write(MAGIC)
            header.write(fpo)
            for file_path, _ in files_iter:
                try:
                    assert (stream := fpi.extractfile(file_path)) is not None
                    shutil.copyfileobj(stream, fpo)  # type: ignore[misc]
                except Exception as e:
                    raise RuntimeError(f"Failed to extract file `{file_path}`.") from e
