"""
link_checker.py - Broken Link Checker Component (Phase 1)
---------------------------------------------------------
Validates HTTP status of discovered links to detect:
1. Working links (HTTP 200 OK, 2xx)
2. Redirects (HTTP 301, 302, 307, 308)
3. Broken links (HTTP 404, 410, 500, 502, 503, 504)
4. Network exceptions (Timeouts, Connection Errors, Invalid URLs)

Uses efficient HEAD requests first, with automatic fallback to GET.
"""

from urllib.parse import urlparse
import requests


# Default User-Agent header for HTTP requests
DEFAULT_USER_AGENT = "SEOHealthAuditor/1.0 (+http://localhost; Academic Link Checker)"


class LinkChecker:
    """
    Validates a list of target URLs to identify broken links,
    redirects, and working endpoints.
    """

    def __init__(self, timeout=10, user_agent=None):
        """
        Initialize the LinkChecker.

        :param timeout: HTTP request timeout in seconds (default: 10)
        :param user_agent: Custom User-Agent header string (optional)
        """
        self.timeout = timeout
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "*/*",
        }

    def check_single_link(self, url):
        """
        Check the status of a single URL.
        1. Attempts a lightweight HTTP HEAD request with redirects enabled.
        2. Falls back to HTTP GET (streamed) if HEAD returns 405/403/501 or fails.
        3. Returns a structured result dictionary.

        :param url: URL string to check
        :return: dict with url, status_code, is_broken, is_redirect, final_url, error_message
        """
        if not url:
            return {
                "url": url,
                "status_code": None,
                "is_broken": True,
                "is_redirect": False,
                "final_url": url,
                "error_message": "Empty or Null URL"
            }

        url = url.strip()

        # Validate URL scheme
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return {
                "url": url,
                "status_code": None,
                "is_broken": True,
                "is_redirect": False,
                "final_url": url,
                "error_message": f"Unsupported URL scheme: '{parsed.scheme}'"
            }

        response = None
        used_method = "HEAD"

        try:
            # Step 1: Try HEAD request first for fast header-only check
            response = requests.head(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )

            # Some web servers disallow HEAD (405 Method Not Allowed) or block it (403/501)
            # If so, fall back to GET
            if response.status_code in (403, 405, 501):
                used_method = "GET"
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                    stream=True  # Stream to avoid downloading large files into memory
                )

        except requests.exceptions.Timeout:
            return {
                "url": url,
                "status_code": None,
                "is_broken": True,
                "is_redirect": False,
                "final_url": url,
                "error_message": "Request Timeout (Server did not respond in time)"
            }

        except requests.exceptions.TooManyRedirects:
            return {
                "url": url,
                "status_code": None,
                "is_broken": True,
                "is_redirect": True,
                "final_url": url,
                "error_message": "Too Many Redirects (Redirect Loop Detected)"
            }

        except requests.exceptions.ConnectionError:
            # Fall back to GET if HEAD connection reset/failed before giving up
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                    stream=True
                )
            except requests.exceptions.RequestException as get_err:
                return {
                    "url": url,
                    "status_code": None,
                    "is_broken": True,
                    "is_redirect": False,
                    "final_url": url,
                    "error_message": "Connection Error (Domain not found or server refused connection)"
                }

        except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema) as e:
            return {
                "url": url,
                "status_code": None,
                "is_broken": True,
                "is_redirect": False,
                "final_url": url,
                "error_message": f"Invalid URL: {e}"
            }

        except requests.exceptions.RequestException as e:
            return {
                "url": url,
                "status_code": None,
                "is_broken": True,
                "is_redirect": False,
                "final_url": url,
                "error_message": f"HTTP Request Error: {e}"
            }

        except Exception as e:
            return {
                "url": url,
                "status_code": None,
                "is_broken": True,
                "is_redirect": False,
                "final_url": url,
                "error_message": f"Unexpected Error: {e}"
            }

        # Evaluate HTTP response
        status_code = response.status_code
        final_url = response.url
        is_redirect = len(response.history) > 0 or (300 <= status_code < 400)
        is_broken = status_code >= 400

        # Construct user-friendly error message if broken
        error_message = None
        if is_broken:
            if status_code == 404:
                error_message = "HTTP 404 (Not Found)"
            elif status_code == 410:
                error_message = "HTTP 410 (Gone)"
            elif status_code == 500:
                error_message = "HTTP 500 (Internal Server Error)"
            elif status_code == 502:
                error_message = "HTTP 502 (Bad Gateway)"
            elif status_code == 503:
                error_message = "HTTP 503 (Service Unavailable)"
            elif status_code == 504:
                error_message = "HTTP 504 (Gateway Timeout)"
            else:
                error_message = f"HTTP {status_code}"

        return {
            "url": url,
            "status_code": status_code,
            "is_broken": is_broken,
            "is_redirect": is_redirect,
            "final_url": final_url,
            "error_message": error_message
        }

    def check_links(self, urls):
        """
        Check a collection of URLs and return detailed results
        along with summary counts.

        :param urls: Iterable list or set of URL strings
        :return: dict with summary stats and results list
        """
        unique_urls = list(dict.fromkeys(urls))  # Preserves order while removing duplicates
        results = []

        working_count = 0
        redirect_count = 0
        broken_count = 0
        error_count = 0

        print(f"[LinkChecker] Checking {len(unique_urls)} unique links...")

        for idx, url in enumerate(unique_urls, 1):
            result = self.check_single_link(url)
            results.append(result)

            if result["is_broken"]:
                broken_count += 1
                if result["status_code"] is None:
                    error_count += 1
            else:
                working_count += 1

            if result["is_redirect"]:
                redirect_count += 1

            # Console progress update
            status_display = result["status_code"] if result["status_code"] else "ERROR"
            broken_flag = "[BROKEN]" if result["is_broken"] else "[OK]"
            redirect_flag = "[REDIRECT]" if result["is_redirect"] else ""
            print(f"  ({idx}/{len(unique_urls)}) {broken_flag}{redirect_flag} {url} -> {status_display}")

        print(f"[LinkChecker] Finished: {working_count} working, {redirect_count} redirects, {broken_count} broken ({error_count} network errors).")

        return {
            "total_checked": len(unique_urls),
            "working_count": working_count,
            "redirect_count": redirect_count,
            "broken_count": broken_count,
            "error_count": error_count,
            "results": results
        }
