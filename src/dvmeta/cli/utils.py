"""Utility functions for dvmeta CLI."""

from contextlib import contextmanager

from rich.progress import Progress, SpinnerColumn

_active = False  # ponytail: guards against nested Progress live displays; commands call each other and each wraps itself in spinner()


@contextmanager
def spinner():
    """Spinner function."""
    global _active
    if _active:
        yield
        return
    _active = True
    try:
        with Progress(SpinnerColumn(), transient=True) as progress:
            progress.add_task("", total=None)
            yield
    finally:
        _active = False
