from __future__ import annotations

import re
import unicodedata
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory


DetectorFactory.seed = 42


_EMOJI_PATTERN = re.compile(
    "[\U0001F600-\U0001F64F]|"  # emoticons
    "[\U0001F300-\U0001F5FF]|"  # symbols & pictographs
    "[\U0001F680-\U0001F6FF]|"  # transport & map
    "[\U0001F1E0-\U0001F1FF]|"  # flags
    "[\u2600-\u26FF]|"          # misc symbols
    "[\u2700-\u27BF]",          # dingbats
    flags=re.UNICODE,
)


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.extract()
    text = soup.get_text(separator="\n")
    return text


def strip_emojis(text: str) -> str:
    return _EMOJI_PATTERN.sub("", text)


def normalize_text(text: str, *, is_html: bool = False) -> tuple[str, str]:
    """Return (clean_text, language_code). Handles HTML stripping, emoji removal, quote threading.
    Quote threading: collapse more than 3 consecutive '>' to '>>>' and trim excess spaces.
    """
    if is_html:
        text = html_to_text(text)
    # Normalize newlines and whitespace
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Simplify quote threading
    text = re.sub(r"^>\s*>\s*>\s*>+", ">>>", text, flags=re.MULTILINE)
    # Remove emojis
    text = strip_emojis(text)
    # Collapse excessive whitespace
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    try:
        lang = detect(text) if text else "unknown"
    except Exception:
        lang = "unknown"
    return text, lang
