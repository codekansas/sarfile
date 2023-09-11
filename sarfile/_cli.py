"""Command-line interface for interacting with sarfiles."""

import argparse
from pathlib import Path

from sarfile._sarfile import sarfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument("out_path", type=str, help="Path to the output SAR file.")
    parser.add_argument("in_path", type=str, help="Path to the input directory or TAR file to pack.")
    parser.add_argument("-o", "--only-extensions", type=str, nargs="+", help="Only pack files with these extensions.")
    parser.add_argument("-e", "--exclude-extensions", type=str, nargs="+", help="Exclude files with these extensions.")
    args = parser.parse_args()

    in_path, out_path = Path(args.in_path), Path(args.out_path)
    if in_path.suffix.lower() == ".sar":
        raise ValueError("Cannot pack a SAR file; did you mix up the input and output paths?")

    if in_path.suffix.lower() == ".tar":
        sarfile.pack_tar(out=out_path, tar=in_path)
    else:
        sarfile.pack_files(
            out=out_path,
            root_dir=in_path,
            only_extensions=args.only_extensions,
            exclude_extensions=args.exclude_extensions,
        )
    print(f"Done packing {in_path} to {out_path}.")

    # Double-check that we can open the packed file.
    sf = sarfile.open(out_path)
    print(f"Packed file has {len(sf)} item(s).")


if __name__ == "__main__":
    main()
