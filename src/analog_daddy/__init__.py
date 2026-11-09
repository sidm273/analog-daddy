"""Top-level package for Analog Daddy."""

from importlib.metadata import version

from analog_daddy.config import DefaultConfig

__version__ = version("analog-daddy")

__all__ = [
    "DefaultConfig",
    "__version__",
]
