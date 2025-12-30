# app/utils/cleaner.py

"""
HTML Cleaning Utilities
-----------------------
Provides helper functions for stripping HTML tags
and returning clean plain-text output.

Used by:
- meeting_service (for cleaning meeting topics / minutes)
"""

from bs4 import BeautifulSoup


def clean_html(text: str) -> str:
    """
    Extract plain text from HTML content.

    Args:
        text (str): Raw HTML or plain text.

    Returns:
        str: Cleaned plain text with HTML removed.
    """
    if not text:
        return ""

    # Ensure input is string
    if not isinstance(text, str):
        text = str(text)

    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text().strip()
