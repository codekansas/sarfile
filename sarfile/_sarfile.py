"""Defines the main sarfile API."""

import struct
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator, Union, Collection, Optional
import functools
from ._constants import MAGIC, PRE_HEADER_SIZE
from ._header import Header

StrPath = Union[str, Path]
StrPathIO = Union[str, Path, BinaryIO]


class sarfile:  # noqa: N801
    def __init__(self, fp: StrPathIO) -> None:
        self._fp = fp
        self._was_opened = False
        self._header = self._read_header()

    def _read_header(self) -> Header:
        with self._open_file() as fp:
            init_bytes = fp.read(PRE_HEADER_SIZE)
            if init_bytes[: len(MAGIC)] != MAGIC:
                raise IOError("Invalid magic number; this is not a sarfile.")
            header_num_bytes = struct.unpack("Q", init_bytes[len(MAGIC) :])[0]
            header_bytes = fp.read(header_num_bytes)
            return Header.decode(header_bytes)

    @contextmanager
    def _open_file(self) -> Iterator[BinaryIO]:
        if isinstance(self._fp, (str, Path)):
            try:
                fpi = open(self._fp, "rb")
                yield fpi
            finally:
                fpi.close()
        else:
            assert self._fp.readable(), "File pointer is not readable."
            return self._fp

    @functools.cached_property
    def names(self) -> list[str]:
        return [name for _, name in self._header.files]

    def extract(self, name: str) -> BinaryIO:
        raise NotImplementedError

    @classmethod
    def open(cls, fp: StrPathIO) -> "sarfile":
        return cls(fp)

    @classmethod
    def pack_files(
        cls,
        files: Optional[Collection[StrPath]] = None,
        root_dir: Optional[StrPath] = None,
        only_extensions: Optional[Collection[str]] = None,
        exclude_extensions: Optional[Collection[str]] = None,
    ) -> None:
        """Packs a collection of files into a sarfile.

        Args:
            files: A collection of files to pack. Mutually exclusive with
                ``root_dir``.
            root_dir: The root directory to iteratively search for files to
                pack. Mutually exclusive with ``files``.
            only_extensions: If not None, only files with these extensions
                will be included.
            exclude_extensions: If not None, files with these extensions
                will be excluded.
        """
        if (root_dir is None) == (files is None):
            raise ValueError("Exactly one of `root_dir` or `files` must be specified.")

        if root_dir is not None:
            root_dir = Path(root_dir)
            files_with_sizes = _get_files_to_pack(root_dir, only_extensions, exclude_extensions)
        elif files is not None:
            files_with_sizes = _get_file_sizes(files)
        else:
            assert False
