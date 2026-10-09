"""
core package - Backend Core for Website Broken Link & SEO Health Audit Tool
----------------------------------------------------------------------------
Provides:
- WebCrawler: BFS crawler to traverse internal pages and extract hyperlinks.
- LinkChecker: Broken-link checker to validate URL HTTP statuses.
"""

from .crawler import WebCrawler
from .link_checker import LinkChecker

__all__ = ["WebCrawler", "LinkChecker"]
