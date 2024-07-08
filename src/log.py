import logging
import sys


class MultiLineFormatter(logging.Formatter):
    """Multi-line formatter from https://stackoverflow.com/a/66855071/1749551"""

    def get_header_length(self, record):
        """Get the header length of a given record."""
        return len(
            super().format(
                logging.LogRecord(
                    name=record.name,
                    level=record.levelno,
                    pathname=record.pathname,
                    lineno=record.lineno,
                    msg="",
                    args=(),
                    exc_info=None,
                )
            )
        )

    def format(self, record):
        """Format a record with added indentation."""
        indent = " " * self.get_header_length(record)
        head, *trailing = super().format(record).splitlines(True)
        return head + "".join(indent + line for line in trailing)


def get_logger(debug=False):
    formatter = MultiLineFormatter(
        fmt="%(asctime)-8s %(levelname)3s %(message)s", datefmt="%H:%M:%S"
    )
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(formatter)

    logger = logging.Logger(__name__)
    level = logging.DEBUG if debug else logging.INFO
    logger.addHandler(log_handler)
    logger.setLevel(level)

    return logger
