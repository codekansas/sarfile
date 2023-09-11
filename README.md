# sarfile

Like tarfile, but streamable.

## What is this?

This repository implements a "streaming archive" file format for collecting multiple files into one. This is similar to the TAR format, but it puts the information about all the files in the archive into a contiguous block at the beginning of the file. This solves a couple problems:

1. Much faster startup times for large archives (we read the entire header into memory in one go)
2. Much friendlier to remote file systems (only one network request rather than a bunch), in combination with `smart_open`
3. Fast random access

The file size is the same as an uncompressed TAR file.

The downside is that once we've written a SAR file, we can't change it. Maybe future formats will support this, but for now, the recommended flow is to first generate a TAR file, then convert it using the builtin `sarpack` command line tool or the `sarfile.pack_tar` Python API.

Also, the file format only exists in this repository, although it's very simple to implement (see the `_header.py` documentation and the `sarfile` object for how to load items).

## Getting Started

Install the package using Pip:

```bash
pip install sarfile
```

Next, simply import the module:

```python
import sarfile
```

You can convert a tarfile to a sarfile using the Python API:

```python
sarfile.pack_tar(out="myfile.sar", tar="myfile.tar")
```

Alternatively, you can use the built-in command line tool:

```bash
sarpack myfile.sar myfile.tar
```

Finally, the file can be used in your Python script:

```python
f = sarfile.open("myfile.sar"):
print(f.names)
with f["myfile.txt"] as myfile:
    print(myfile.read())
```

If you have installed `smart_open`, then you can also read from S3 as follows:

```python
f = sarfile.open("myfile.sar")
print(f.names)
with f["myfile.txt"] as myfile:
    print(myfile.read())
```

The above code is much faster than reading a TAR file from S3, because we read the entire header into memory in one network request, rather than having to make a network request for each file in the archive. On subsequent accesses we also only download the part of the file we want to read.

## Requirements

This package is tested against Python 3.10. Although not required, it is a good idea to install `smart_open` to support reading from S3 or other remote file systems, and `tqdm` to show a progress bar when packing large files.
