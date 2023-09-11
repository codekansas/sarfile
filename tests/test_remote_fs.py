"""Tests SAR files on remote file systems."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

import sarfile


@pytest.mark.skip(reason="This test accesses AWS and shouldn't be run on CI, run using CLI instead.")
def test_streaming_from_aws(tmp_path: Path) -> None:
    try:
        from smart_open import open
    except ImportError:
        raise ImportError("smart_open is required to run this test.")

    (input_dir := tmp_path / "files").mkdir()
    for i in range(100):
        (input_dir / f"file{i}.txt").write_text(f"file{i}")

    output_path = tmp_path / "test_files.sar"
    sarfile.pack_files(out=output_path, root=input_dir)

    # Gets the S3 key for the file upload.
    if "S3_DATA_BUCKET" not in os.environ:
        raise KeyError("S3_DATA_BUCKET environment variable not set.")
    bucket = os.environ["S3_DATA_BUCKET"]
    s3_key = f"s3://{bucket}/test/{output_path.name}"

    # Uploads the file to S3 using smart_open.
    with open(output_path, "rb") as fin, open(s3_key, "wb") as fout:
        shutil.copyfileobj(fin, fout)

    # Access the file on S3 using smart_open.
    sar = sarfile.open(s3_key)
    assert len(sar) == 100
    for i in [0, 99, 12]:
        decoded = sar[i].read().decode()
        assert decoded == sar.names[i][:-len(".txt")]


if __name__ == "__main__":
    # python tests/test_remote_fs.py
    test_streaming_from_aws(Path(tempfile.mkdtemp(suffix="_sarfile_test")))
