"""
crawler.py - Website Crawler Component (Phase 1)
-------------------------------------------------
Performs Breadth-First Search (BFS) crawling on a target website to:
1. Traverse internal pages within the same domain.
2. Extract all hyperlinks (<a href="...">) from HTML pages.
3. Normalize URLs and filter out non-crawlable resources (images, PDFs, mailto, etc.).
4. Collect discovered links for broken-link checking and SEO analysis.
"""

from collections import deque
from urllib.parse import urlparse, urljoin, urldefrag
import requests


# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup

# Common non-HTML static file extensions to ignore during page crawling
NON_HTML_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp",
    ".css", ".js", ".pdf", ".zip", ".tar", ".gz", ".rar", ".7z",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".wmv",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".xml", ".json", ".txt", ".csv"
)

# Schemes to ignore
IGNORED_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "#")

# Default User-Agent header for HTTP requests
DEFAULT_USER_AGENT = "SEOHealthAuditor/1.0 (+http://localhost; Academic Project Crawler)"


class WebCrawler:
    """
    Beginner-friendly BFS Web Crawler for extracting internal pages
    and collecting all discovered hyperlinks.
    """

    def __init__(self, start_url, max_pages=20, timeout=10, user_agent=None):
        """
        Initialize the crawler with configuration parameters.

        :param start_url: Starting URL to crawl (e.g. 'https://example.com')
        :param max_pages: Maximum number of internal pages to crawl (default: 20)
        :param timeout: HTTP request timeout in seconds (default: 10)
        :param user_agent: Custom User-Agent string (optional)
        """
        self.raw_start_url = start_url.strip() if start_url else ""
        self.start_url = self.normalize_url(self.raw_start_url)
        self.max_pages = max_pages
        self.timeout = timeout
        self.user_agent = user_agent or DEFAULT_USER_AGENT

        # Extract base domain from start URL for same-domain checking
        parsed = urlparse(self.start_url)
        self.base_domain = parsed.netloc.lower()
        self.base_scheme = parsed.scheme.lower() or "http"

        # Request headers
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    @staticmethod
    def normalize_url(url, default_scheme="http"):
        """
        Normalize a given URL:
        - Strip surrounding whitespace.
        - Ensure valid scheme (http/https) without corrupting protocol-relative or custom schemes.
        - Remove fragments (#section).
        - Return clean absolute URL string.
        """
        if not url:
            return ""

        url = url.strip()

        # Handle protocol-relative URLs (e.g. //example.com/path)
        if url.startswith("//"):
            url = f"{default_scheme}:{url}"
        else:
            parsed = urlparse(url)
            # If no scheme is present (e.g. 'example.com/about')
            if not parsed.scheme:
                url = f"{default_scheme}://" + url.lstrip("/")

        # Remove fragment (#section) from the URL
        url_without_fragment, _ = urldefrag(url)
        return url_without_fragment.strip()

    def is_same_domain(self, url):
        """
        Check if the URL belongs to the same domain as the starting URL.
        Handles www and non-www variants gracefully across Python versions.
        """
        if not url:
            return False

        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        # Direct domain match
        if netloc == self.base_domain:
            return True

        # Normalize www.example.com and example.com matching (Python <3.9 safe)
        base_clean = self.base_domain[4:] if self.base_domain.startswith("www.") else self.base_domain
        netloc_clean = netloc[4:] if netloc.startswith("www.") else netloc
        return netloc_clean == base_clean

    @staticmethod
    def is_crawlable_page(url):
        """
        Check if the URL appears to be an HTML page rather than
        a static resource (image, script, stylesheet, pdf, etc.).
        """
        if not url:
            return False

        parsed = urlparse(url)
        path = parsed.path.lower()

        # Check against non-HTML extensions
        for ext in NON_HTML_EXTENSIONS:
            if path.endswith(ext):
                return False

        return True

    def extract_links_from_html(self, html_content, page_url):
        """
        Parse HTML and extract all valid hyperlinks (<a href="...">).
        Converts relative links to absolute URLs and filters out
        special schemes like mailto:, tel:, javascript:.
        """
        discovered_links = []

        if not html_content:
            return discovered_links

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            anchor_tags = soup.find_all("a", href=True)

            for tag in anchor_tags:
                href = tag.get("href", "").strip()

                # Skip empty hrefs
                if not href or href == "#":
                    continue

                # Skip ignored schemes
                if any(href.lower().startswith(scheme) for scheme in IGNORED_SCHEMES):
                    continue

                # Convert relative URL to absolute URL
                absolute_url = urljoin(page_url, href)

                # Normalize (strip fragment #)
                clean_url = self.normalize_url(absolute_url, default_scheme=self.base_scheme)

                # Validate scheme is http or https
                if clean_url.startswith("http://") or clean_url.startswith("https://"):
                    discovered_links.append(clean_url)

        except Exception as e:
            # Defensive logging if parsing fails
            print(f"[Crawler Warning] HTML parsing error on {page_url}: {e}")

        return discovered_links

    def fetch_page(self, url):
        """
        Fetch a page using requests with defensive error handling.

        :return: (response_text, status_code, content_type, final_url, error_message)
        """
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )

            content_type = response.headers.get("Content-Type", "").lower()
            status_code = response.status_code
            final_url = response.url

            error_message = None
            if status_code >= 400:
                error_message = f"HTTP {status_code}"

            return response.text, status_code, content_type, final_url, error_message

        except requests.exceptions.Timeout:
            return None, None, "", url, "Request Timeout (10s limit exceeded)"
        except requests.exceptions.ConnectionError:
            return None, None, "", url, "Connection Error (Failed to reach server)"
        except requests.exceptions.TooManyRedirects:
            return None, None, "", url, "Too Many Redirects"
        except requests.exceptions.RequestException as e:
            return None, None, "", url, f"Request Exception: {e}"
        except Exception as e:
            return None, None, "", url, f"Unexpected Error: {e}"

    def crawl(self):
        """
        Execute Breadth-First Search (BFS) crawl up to max_pages.

        :return: Structured crawl results dictionary:
        {
            "start_url": str,
            "base_domain": str,
            "total_pages_crawled": int,
            "crawled_pages": list of dicts,
            "all_discovered_links": list of unique URLs
        }
        """
        # Data structures for BFS
        queue = deque([self.start_url])     # FIFO queue for BFS traversal
        visited = set([self.start_url])     # Tracks visited & enqueued URLs to prevent loops
        crawled_pages = []                  # Detailed results per crawled page
        all_discovered_links = set()        # All unique links discovered across all pages

        print(f"[Crawler] Starting BFS crawl for: {self.start_url} (Max pages: {self.max_pages})")

        while queue and len(crawled_pages) < self.max_pages:
            current_url = queue.popleft()
            print(f"[Crawler] ({len(crawled_pages) + 1}/{self.max_pages}) Crawling: {current_url}")

            # Fetch page content
            html_content, status_code, content_type, final_url, error_message = self.fetch_page(current_url)

            page_links = []
            is_success = (status_code == 200)

            # If page was successfully fetched and is HTML, extract links
            if is_success and ("text/html" in content_type or not content_type):
                # Ensure the final URL after redirects is still on the same domain before crawling child links
                if self.is_same_domain(final_url):
                    # Use final_url as base to properly resolve relative links on redirected pages
                    page_links = self.extract_links_from_html(html_content, final_url)

                    for link in page_links:
                        all_discovered_links.add(link)

                        # Enqueue if internal page, crawlable resource, not yet visited, and within limit
                        if (self.is_same_domain(link) and
                                self.is_crawlable_page(link) and
                                link not in visited):
                            visited.add(link)
                            queue.append(link)

            # Record page crawl result
            page_record = {
                "url": current_url,
                "final_url": final_url,
                "status_code": status_code,
                "is_success": is_success,
                "content_type": content_type,
                "links_found_count": len(page_links),
                "discovered_links": page_links,
                "error_message": error_message
            }
            crawled_pages.append(page_record)

        print(f"[Crawler] Crawl complete. Crawled {len(crawled_pages)} pages, discovered {len(all_discovered_links)} unique links.")

        return {
            "start_url": self.start_url,
            "base_domain": self.base_domain,
            "total_pages_crawled": len(crawled_pages),
            "crawled_pages": crawled_pages,
            "all_discovered_links": sorted(list(all_discovered_links))
        }
