"""Tests packing SAR files."""

import tarfile
from pathlib import Path

import sarfile


def test_pack_files(tmpdir: Path) -> None:
    # Writes some random files to the directory.
    (root_dir := Path(tmpdir / "files")).mkdir()
    for i in range(10):
        with open(tmpdir / "files" / f"file{i}.txt", "w") as fp:
            fp.write(f"Hello from {i}!")

    # Packs the files.
    out_path = Path(tmpdir / "out.sar")
    sarfile.pack_files(out=out_path, root_dir=root_dir)

    # Loads the packed file.
    sar = sarfile.open(out_path)

    # Tests reading the file contents.
    assert len(sar) == 10
    for i in range(10):
        with sar[f"file{i}.txt"] as (_, num_bytes, fpi):
            assert fpi.read(num_bytes).decode() == f"Hello from {i}!"


def test_pack_tar(tmpdir: Path) -> None:
    # Writes some random files to the directory.
    (root_dir := Path(tmpdir / "files")).mkdir()
    for i in range(10):
        with open(tmpdir / "files" / f"file{i}.txt", "w") as fp:
            fp.write(f"Hello from {i}!")

    # Packs to a tar file.
    out_path_tar = Path(tmpdir / "out.tar")
    with tarfile.open(out_path_tar, mode="w") as tar:
        for file_path in root_dir.rglob("*"):
            tar.add(file_path, arcname=file_path.relative_to(root_dir))

    # Packs tar file to a sar file.
    out_path = Path(tmpdir / "out.sar")
    sarfile.pack_tar(out=out_path, tar=out_path_tar)

    # Loads the packed file.
    sar = sarfile.open(out_path)

    # Tests reading the file contents.
    assert len(sar) == 10
    for i in range(10):
        with sar[f"file{i}.txt"] as (_, num_bytes, fpi):
            assert fpi.read(num_bytes).decode() == f"Hello from {i}!"
