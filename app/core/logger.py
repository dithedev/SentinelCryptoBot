import logging
import sys


def configure_logging(log_level: str = "INFO") -> None:
    """Configure application-wide structured console logging.

    The format is intentionally simple and readable for local development,
    Docker logs, and portfolio demonstration.
    """
    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Keep noisy third-party loggers under control.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
