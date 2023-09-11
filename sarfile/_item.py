"""Defines the BinaryIO interface for a sarfile item."""

from types import TracebackType
from typing import Any, BinaryIO, Iterator


class TarItem(BinaryIO):
    def __init__(self, name: str, num_bytes: int, fp: BinaryIO) -> None:
        assert fp.readable()

        self._name = name
        self._num_bytes = num_bytes
        self._start = fp.tell()
        self._end = self._start + num_bytes
        self._fp = fp
        self._closed = False

    @property
    def mode(self) -> str:
        return "rb"

    @property
    def name(self) -> str:
        return self._name

    @property
    def closed(self) -> bool:
        return self._fp.closed

    def close(self) -> None:
        self._fp.close()

    def fileno(self) -> int:
        return self._fp.fileno()

    def flush(self) -> None:
        self._fp.flush()

    def isatty(self) -> bool:
        return self._fp.isatty()

    def readable(self) -> bool:
        return self._fp.readable()

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            return self._fp.read(self._end - self._fp.tell())
        else:
            if self._fp.tell() + n > self._end:
                raise ValueError("Read size is larger than the file size.")
            return self._fp.read(n)

    def readline(self, limt: int = -1) -> bytes:
        raise NotImplementedError("Reading lines is not supported for tar items.")

    def readlines(self, hint: int = -1) -> list[bytes]:
        raise NotImplementedError("Reading lines is not supported for tar items.")

    def seek(self, offset: int, whence: int = 0) -> int:
        match whence:
            case 0:
                if offset < 0:
                    raise ValueError("Negative seek position is not allowed.")
                if offset >= self._num_bytes:
                    raise ValueError("Seek position is past the end of the file.")
                return self._fp.seek(self._start + offset, whence)
            case 1:
                if offset < 0:
                    raise ValueError("Negative seek position is not allowed.")
                if self._fp.tell() + offset >= self._end:
                    raise ValueError("Seek position is past the end of the file.")
                return self._fp.seek(offset, whence)
            case 2:
                if offset > 0:
                    raise ValueError("Positive seek position is not allowed.")
                if self._fp.tell() + offset < self._start:
                    raise ValueError("Seek position is past the end of the file.")
                return self._fp.seek(self._start + self._num_bytes + offset, whence)
            case _:
                raise ValueError("Invalid whence value.")

    def seekable(self) -> bool:
        return self._fp.seekable()

    def tell(self) -> int:
        return self._fp.tell() - self._start

    def truncate(self, size: int | None = None) -> int:
        raise NotImplementedError("Truncating is not supported for tar items.")

    def writable(self) -> bool:
        return False

    def write(self, s: Any) -> int:  # noqa: ANN401
        raise NotImplementedError("Writing is not supported for tar items.")

    def writelines(self, lines: Any) -> None:  # noqa: ANN401
        raise NotImplementedError("Writing is not supported for tar items.")

    def __enter__(self) -> "BinaryIO":
        return self

    def __exit__(self, _t: type[BaseException] | None, _e: BaseException | None, _tr: TracebackType | None) -> None:
        self.close()

    def __iter__(self) -> Iterator[bytes]:
        raise NotImplementedError("Iterating is not supported for tar items.")

    def __next__(self) -> bytes:
        raise NotImplementedError("Iterating is not supported for tar items.")
