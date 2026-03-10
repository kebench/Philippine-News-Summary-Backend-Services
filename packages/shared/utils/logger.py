import logging
import os


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured for Lambda/local environments."""
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())

    # Set root logger level directly — basicConfig is a no-op after first call
    logging.getLogger().setLevel(log_level)
    print(f"Logging initialized at {log_level} level for {name}")  # Print to console immediately for visibility
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger