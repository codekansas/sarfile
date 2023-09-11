# sarfile

Like tarfile, but streamable.

## What is this?

This repository implements a "streaming archive" file format for collecting multiple files into one. This is similar to the tar format, but it puts the information about all the files in the archive into a contiguous block at the end of the file. This makes it easier to do things like stream chunks of the file from S3 without having to download the entire file.

## Getting Started

Install the package using Pip:

```bash
pip install sarfile
```

Next, convert a tarfile to a sarfile:

```bash
tar2sar myfile.tar myfile.sar
```

Finally, the file can be used in your Python script:

```python
import sarfile

with sarfile.open("myfile.sar", "r") as f:
    for member in f.getmembers():
        print(member.name)
        print(f.extractfile(member).read())
```

This can be paired with `smart_open` to read from a file on S3:

```python
from smart_open import open
import sarfile

with sarfile.open(fileobj=open("s3://mybucket/file.sar"), "r") as f:
    # This loop will be much faster because all members are pulled from the
    # archive's index in a single request.
    for member in f.getmembers():
      print(member)
```
