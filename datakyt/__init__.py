"""datakyt: equipment accounting for employees, equipment, furniture and licenses."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("datakyt")
except PackageNotFoundError:  # pragma: no cover - only when running from a bare checkout
    __version__ = "0.0.0"
