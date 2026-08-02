import re
from urllib.parse import urlparse
from config import WHITELISTED_DOMAINS

URL_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|@[a-zA-Z0-9_]{5,32})", re.IGNORECASE
)


def contains_link(text: str) -> bool:
    if not text:
        return False
    return bool(URL_REGEX.search(text))


def contains_whitelisted_only(text: str) -> bool:
    urls = URL_REGEX.findall(text)
    if not urls:
        return True
    for url in urls:
        domain = url
        if url.startswith("http"):
            domain = urlparse(url).netloc
        domain = domain.replace("www.", "").lower()
        if not any(wd in domain for wd in WHITELISTED_DOMAINS):
            return False
    return True


def contains_banned_word(text: str, banned_words: list[str]) -> str | None:
    if not text:
        return None
    lowered = text.lower()
    for word in banned_words:
        if word and word in lowered:
            return word
    return None
