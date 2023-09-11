__version__ = "0.1.3"

from ._sarfile import sarfile

# Defines some API functions as stand-alone.
pack_files = sarfile.pack_files
pack_tar = sarfile.pack_tar
open = sarfile.open
