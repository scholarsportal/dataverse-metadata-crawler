"""Utility functions for dvmeta CLI."""

from contextlib import contextmanager

from rich.progress import Progress, SpinnerColumn


@contextmanager
def spinner():
    """Spinner function."""
    with Progress(SpinnerColumn(), transient=True) as progress:
        progress.add_task("", total=None)
        yield
