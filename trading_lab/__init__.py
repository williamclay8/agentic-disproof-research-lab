"""Local development import shim for the src-layout trading_lab package."""

from pathlib import Path


_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "trading_lab"
__path__.append(str(_SRC_PACKAGE))
