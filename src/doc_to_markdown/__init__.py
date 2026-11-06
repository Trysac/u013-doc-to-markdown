"""Convert HTML and DOCX into safe Markdown using only the standard library."""

from __future__ import annotations

import logging

from .core import ConversionError, convert, docx_to_markdown, html_to_markdown

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ["ConversionError", "__version__", "convert", "docx_to_markdown", "html_to_markdown"]

__version__ = "0.1.0"
