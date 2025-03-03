from lzma import CHECK_CRC32
from os import fsync
from pathlib import Path

from pycpio.header import HEADER_NEW, CPIOHeader
from pycpio.errors import UnavailableCompression
from zenlib.logging import loggify
from zenlib.util import colorize


@loggify
class CPIOWriter:
    """
    Takes a list of CPIOData objects, gets their bytes representation, then appends a trailer before writing them to a file.
    Compresses the data if compression is specified.
    """

    def __init__(
        self,
        cpio_entries: list,
        output_file: Path,
        structure=None,
        compression=False,
        compression_level=10,
        xz_crc=CHECK_CRC32,
        *args,
        **kwargs,
    ):
        self.cpio_entries = cpio_entries
        self.output_file = Path(output_file)

        self.structure = structure if structure is not None else HEADER_NEW

        self.compression = compression or False
        self.compression_level = compression_level or 10
        if isinstance(compression, str):
            compression = compression.lower()
            if compression == "true":
                compression = True
            elif compression == "false":
                compression = False
            self.compression = compression

        self.xz_crc = xz_crc

    def __bytes__(self):
        """Creates a bytes representation of the CPIOData objects."""
        cpio_bytes = bytes(self.cpio_entries)
        trailer = CPIOHeader(structure=self.structure, name="TRAILER!!!", logger=self.logger)
        self.logger.debug("Building trailer: %s" % trailer)
        cpio_bytes += bytes(trailer)
        return cpio_bytes

    def compress(self, data):
        """Attempts to compress the data using the specified compression type."""
        compression_kwargs = {}
        compression_args = ()
        if self.compression == "xz" or self.compression is True:
            compression_module = "lzma.compress"
            compression_kwargs["check"] = self.xz_crc
        elif self.compression == "zstd":
            compression_module = "zstandard.compress"
            compression_args = (self.compression_level,)
        elif self.compression is not False:
            raise UnavailableCompression("Compression type not supported: %s" % self.compression)
        else:
            self.logger.info("No compression specified, writing uncompressed data.")
            return data

        try:
            if "." in compression_module:
                module, func = compression_module.rsplit(".", 1)
            else:
                module, func = compression_module, "compress"

            compressor = getattr(__import__(module), func)
            self.logger.debug("Compressing data with: %s" % compression_module)
        except ImportError as e:
            raise UnavailableCompression("Failed to import compression module: %s" % compression_module) from e

        self.logger.info(
            "[%s] Compressing the CPIO data, original size: %.2f MiB" % (self.compression.upper(), len(data) / (2**20))
        )
        data = compressor(data, *compression_args, **compression_kwargs)

        return data

    def write(self, safe_write=True):
        """Writes the CPIOData objects to the output file."""
        self.logger.debug("Writing to: %s" % self.output_file)
        data = self.compress(bytes(self))
        with open(self.output_file, "wb") as f:
            f.write(data)
            if safe_write:
                # Flush the file to ensure all data is written, then fsync to ensure it's written to disk.
                f.flush()
                fsync(f.fileno())
            else:
                self.logger.warning("File not fsynced, data may not be written to disk: %s" % self.output_file)

        self.logger.info("Wrote %.2f MiB to: %s" % (len(data) / (2**20), colorize(self.output_file, "green")))
