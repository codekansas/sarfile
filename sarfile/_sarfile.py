"""Defines the main sarfile API."""

import struct
from contextlib import contextmanager
from pathlib import Path
from types import TracebackType
from typing import BinaryIO, ContextManager, Literal, Union

from ._constants import MAGIC, PRE_HEADER_SIZE
from ._header import Header

Mode = Literal["r", "w"]


class sarfile:  # noqa: N801
    def __init__(self, fp: Union[str, Path, BinaryIO], mode: Mode = "r") -> None:
        self._fp: BinaryIO | None = None
        self._was_opened = False
        self._mode = mode
        self._header = self._read_header() if mode == "r" else None

    def _read_header(self) -> Header:
        with self._open_file() as fp:
            init_bytes = fp.read(PRE_HEADER_SIZE)
            if init_bytes[:len(MAGIC)] != MAGIC:
                raise IOError("Invalid magic number; this is not a sarfile.")
            header_num_bytes = struct.unpack("Q", init_bytes[len(MAGIC):])[0]
            header_bytes = fp.read(header_num_bytes)
            return Header.decode(header_bytes)

    @contextmanager
    def _open_file(self, fp: Union[str, Path, BinaryIO], mode: Mode) -> ContextManager[BinaryIO]:
        if isinstance(fp, (str, Path)):
            try:
                fpi = open(fp, "rb")
                yield fpi
            finally:
                fpi.close()
        else:
            assert fp.readable(), "File pointer is not readable."
            return fp

    def __enter__(self) -> "sarfile":
        return self

    def __exit__(self, _t: type[BaseException] | None, _e: BaseException | None, _tr: TracebackType | None) -> None:
        self.close()

    def open(self) -> None:
        """Opens the file pointer.

        If a file pointer was passed, this does nothing. However, if a string
        or path was passed, this will open the specified file in the given
        mode (read or write).

        Raises:
            IOError: If the file pointer is already open.
        """
        if self._fp is not None:
            raise IOError("File pointer is open.")
        self._fp, self._was_opened = self._open_file(self._fp, self._mode)

    def close(self) -> None:
        """Closes the file pointer.

        If a file pointer was passed, this does nothing. However, if a string
        or path was passed, this will close the file pointer.

        Raises:
            IOError: If the file pointer is already closed.
        """
        if self._fp is None:
            raise IOError("File pointer is closed.")
        if self._was_opened:
            self._fp.close()
        self._fp = None
