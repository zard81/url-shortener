"""URL Shortener — Core logic."""
import hashlib
import json
import string
import random
import time
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


@dataclass
class ShortURL:
    code: str
    original_url: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    clicks: int = 0
    custom: bool = False
    expires_at: Optional[str] = None
    last_clicked: Optional[str] = None


class URLStore:
    """Persistent JSON-based URL storage."""

    def __init__(self, filepath: str = "urls.json"):
        self.filepath = Path(filepath)
        self.urls: dict[str, ShortURL] = {}
        self._load()

    def _load(self):
        if self.filepath.exists():
            data = json.loads(self.filepath.read_text())
            for code, info in data.items():
                self.urls[code] = ShortURL(code=code, **info)

    def save(self):
        data = {code: asdict(url) for code, url in self.urls.items()}
        self.filepath.write_text(json.dumps(data, indent=2))

    def add(self, url: str, custom_code: str = None, expires_hours: int = None) -> ShortURL:
        if custom_code:
            if custom_code in self.urls:
                raise ValueError(f"Code '{custom_code}' already taken")
            code = custom_code
        else:
            code = self._generate_code(url)

        expires = None
        if expires_hours:
            from datetime import timedelta
            expires = (datetime.now() + timedelta(hours=expires_hours)).isoformat()

        short = ShortURL(code=code, original_url=url, custom=bool(custom_code), expires_at=expires)
        self.urls[code] = short
        self.save()
        return short

    def get(self, code: str) -> Optional[ShortURL]:
        url = self.urls.get(code)
        if url and url.expires_at:
            if datetime.now().isoformat() > url.expires_at:
                del self.urls[code]
                self.save()
                return None
        return url

    def click(self, code: str) -> Optional[ShortURL]:
        url = self.get(code)
        if url:
            url.clicks += 1
            url.last_clicked = datetime.now().isoformat()
            self.save()
        return url

    def delete(self, code: str) -> bool:
        if code in self.urls:
            del self.urls[code]
            self.save()
            return True
        return False

    def stats(self) -> dict:
        total = len(self.urls)
        total_clicks = sum(u.clicks for u in self.urls.values())
        top = sorted(self.urls.values(), key=lambda u: u.clicks, reverse=True)[:5]
        return {
            "total_urls": total,
            "total_clicks": total_clicks,
            "top_urls": [{"code": u.code, "url": u.original_url, "clicks": u.clicks} for u in top],
        }

    def _generate_code(self, url: str, length: int = 6) -> str:
        chars = string.ascii_letters + string.digits
        for _ in range(100):
            code = "".join(random.choices(chars, k=length))
            if code not in self.urls:
                return code
        # Fallback: hash-based
        return hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()[:length]


def validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False
