"""Defines the sarfile header."""

import itertools
import math
import struct
from dataclasses import dataclass
from typing import BinaryIO


@dataclass
class Header:
    """Defines the sarfile header.

    The header is structured as follows:

    - 1 byte: The int type used to encode the file lengths (1, 2, 4, or 8).
    - 1 byte: The int type used to encode the name lengths (1, 2, 4, or 8).
    - 8 bytes: The number of files.
    - N * (1, 2, 4, 8) bytes: The file lengths, encoded using the number of
        bytes specified above.
    - N * (1, 2, 4, 8) bytes: The name lengths, encoded using the number of
        bytes specified above.
    - N bytes: The names, encoded as UTF-8.

    The "header" actually comes at the end of the file, so that we can easily
    append to the file. Once we've loaded the header into memory, we can
    efficiently seek to the start of the file and read the data, or we can
    shard the header to read the data in parallel.

    Attributes:
        files: A list of tuples, where the first element is the file path and
            the second element is the number of bytes in the file.
        init_offset: The initial offset of the header. This is used when
            sharding the header.
    """

    files: list[tuple[str, int]]
    init_offset: int = 0

    def encode(self) -> bytes:
        """Encodes the header to bytes.

        Returns:
            The encoded header.
        """
        file_lengths = [num_bytes for _, num_bytes in self.files]
        names_bytes = [file_path.encode("utf-8") for file_path, _ in self.files]
        names_bytes_lengths = [len(n) for n in names_bytes]

        def get_byte_enc_and_dtype(n: int) -> tuple[int, str]:
            if n < 2**8:
                return 1, "B"
            elif n < 2**16:
                return 2, "H"
            elif n < 2**32:
                return 4, "I"
            else:
                return 8, "Q"

        file_lengths_dtype_int, file_lengths_dtype = get_byte_enc_and_dtype(max(file_lengths))
        name_lengths_dtype_int, name_lengths_dtype = get_byte_enc_and_dtype(max(names_bytes_lengths))

        return b"".join(
            [
                struct.pack("B", file_lengths_dtype_int),
                struct.pack("B", name_lengths_dtype_int),
                struct.pack("Q", len(self.files)),
                struct.pack(f"<{len(file_lengths)}{file_lengths_dtype}", *file_lengths),
                struct.pack(f"<{len(names_bytes)}{name_lengths_dtype}", *names_bytes_lengths),
                *names_bytes,
            ],
        )

    def write(self, fp: BinaryIO) -> None:
        encoded = self.encode()
        fp.write(struct.pack("Q", len(encoded)))
        fp.write(encoded)

    @classmethod
    def decode(cls, b: bytes) -> "Header":
        """Decodes the header from the given bytes.

        Args:
            b: The bytes to decode.

        Returns:
            The decoded header.
        """

        def get_dtype_from_int(n: int) -> str:
            if n == 1:
                return "B"
            elif n == 2:
                return "H"
            elif n == 4:
                return "I"
            elif n == 8:
                return "Q"
            else:
                raise ValueError(f"Invalid dtype int: {n}")

        (file_lengths_dtype_int, name_lengths_dtype_int), b = struct.unpack("BB", b[:2]), b[2:]
        file_lengths_dtype = get_dtype_from_int(file_lengths_dtype_int)
        name_lengths_dtype = get_dtype_from_int(name_lengths_dtype_int)

        (num_files,), b = struct.unpack("Q", b[:8]), b[8:]

        fl_bytes = num_files * struct.calcsize(file_lengths_dtype)
        nl_bytes = num_files * struct.calcsize(name_lengths_dtype)
        file_lengths, b = struct.unpack(f"<{num_files}{file_lengths_dtype}", b[:fl_bytes]), b[fl_bytes:]
        names_bytes_lengths, b = struct.unpack(f"<{num_files}{name_lengths_dtype}", b[:nl_bytes]), b[nl_bytes:]

        names = []
        for name_bytes_length in names_bytes_lengths:
            name_bytes, b = b[:name_bytes_length], b[name_bytes_length:]
            names.append(name_bytes.decode("utf-8"))

        assert len(b) == 0, f"Bytes left over: {len(b)}"

        return cls(list(zip(names, file_lengths)))

    @classmethod
    def read(cls, fp: BinaryIO) -> tuple["Header", int]:
        """Reads the header from the open file pointer.

        Args:
            fp: The open file pointer.

        Returns:
            The header and the number of bytes read.
        """
        (num_bytes,) = struct.unpack("Q", fp.read(8))
        return cls.decode(fp.read(num_bytes)), num_bytes

    def shard(self, shard_id: int, total_shards: int) -> "Header":
        """Shards the header.

        Args:
            shard_id: The shard ID.
            total_shards: The total number of shards.

        Returns:
            A new header objet, which is a subset of the original header.
        """
        num_files = len(self.files)
        num_files_per_shard = math.ceil(num_files / total_shards)
        start = shard_id * num_files_per_shard
        end = min((shard_id + 1) * num_files_per_shard, num_files)
        shard_offset = sum(num_bytes for _, num_bytes in self.files[:start])
        return Header(self.files[start:end], self.init_offset + shard_offset)

    def _offsets(self, header_size: int) -> list[int]:
        return [
            offset + header_size + self.init_offset
            for offset in itertools.accumulate((num_bytes for _, num_bytes in self.files), initial=0)
        ]
