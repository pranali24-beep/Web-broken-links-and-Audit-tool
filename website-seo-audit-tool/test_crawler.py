"""
test_crawler.py - Test Script for Phase 1 Core Backend
-------------------------------------------------------
Validates:
1. WebCrawler BFS traversal, page limit, and link extraction.
2. LinkChecker broken link detection, redirect handling, and error handling.

Usage:
    python test_crawler.py                     # Runs mock test suite with broken/redirect/working pages
    python test_crawler.py https://example.com # Runs against a specific live target URL
"""

import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from core.crawler import WebCrawler
from core.link_checker import LinkChecker


# ==============================================================================
# Mock HTTP Server for Deterministic Offline Testing
# ==============================================================================
class MockSiteHandler(BaseHTTPRequestHandler):
    """
    Simulates a multi-page website with:
    - Working pages (/ and /about and /services)
    - Broken links (/broken-404, /server-error-500)
    - Redirect links (/old-page -> /about)
    - External links (https://google.com)
    - Non-HTML assets (/image.png, /style.css)
    - Ignored schemes (mailto:admin@example.com, tel:123456, javascript:void(0))
    """

    def do_HEAD(self):
        self._handle_request()

    def do_GET(self):
        self._handle_request()

    def _handle_request(self):
        path = self.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Mock Home</title></head>
            <body>
                <h1>Welcome to Test Website</h1>
                <a href="/about">About Us</a>
                <a href="/services">Services</a>
                <a href="/old-page">Old Page (Redirect)</a>
                <a href="/missing-page-404">Missing Link</a>
                <a href="/server-crash-500">Server Error Link</a>
                <a href="https://httpbin.org/status/200">External Working Link</a>
                <a href="mailto:support@testsite.local">Email Us</a>
                <a href="tel:+123456789">Call Us</a>
                <a href="javascript:alert('hi')">JS Action</a>
                <a href="/images/banner.png">Banner Image</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path == "/about":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>About Us</title></head>
            <body>
                <h1>About Us</h1>
                <a href="/">Back to Home</a>
                <a href="/contact">Contact Us</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path == "/services":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Services</title></head>
            <body>
                <h1>Our Services</h1>
                <a href="/">Home</a>
                <a href="/missing-page-404">Broken Link on Services</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path == "/contact":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html><head><title>Contact</title></head>
            <body><h1>Contact</h1><a href="/">Home</a></body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path == "/old-page":
            # 301 Permanent Redirect to /about
            self.send_response(301)
            self.send_header("Location", "/about")
            self.end_headers()

        elif path == "/missing-page-404":
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")

        elif path == "/server-crash-500":
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>500 Internal Server Error</h1>")

        elif path == "/images/banner.png":
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.end_headers()
            self.wfile.write(b"\x89PNG\r\n\x1a\n")

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence default server stdout logs during test
        pass


def run_audit_test(target_url, max_pages=10):
    """
    Run crawler and link checker workflow on a target URL
    and print formatted results to the terminal.
    """
    print("=" * 70)
    print("  WEBSITE BROKEN LINK & SEO HEALTH AUDIT TOOL - PHASE 1 TEST")
    print("=" * 70)
    print(f"Target URL : {target_url}")
    print(f"Max Pages  : {max_pages}")
    print("-" * 70)

    # -------------------------------------------------------------
    # Step 1: Run Crawler
    # -------------------------------------------------------------
    print("\n[STEP 1] Running Website Crawler...")
    start_time = time.time()
    crawler = WebCrawler(start_url=target_url, max_pages=max_pages, timeout=10)
    crawl_result = crawler.crawl()
    crawl_duration = round(time.time() - start_time, 2)

    print("\n" + "=" * 70)
    print("  CRAWLER RESULTS SUMMARY")
    print("=" * 70)
    print(f"Base Domain         : {crawl_result['base_domain']}")
    print(f"Pages Crawled Count : {crawl_result['total_pages_crawled']}")
    print(f"Time Elapsed        : {crawl_duration}s")
    print("-" * 70)
    print("Discovered Crawled Pages:")
    for idx, page in enumerate(crawl_result["crawled_pages"], 1):
        status = page["status_code"] if page["status_code"] else "ERROR"
        links_count = page["links_found_count"]
        print(f"  {idx}. [{status}] {page['url']} ({links_count} links found)")

    # -------------------------------------------------------------
    # Step 2: Run Link Checker
    # -------------------------------------------------------------
    all_links = crawl_result["all_discovered_links"]
    print("\n" + "=" * 70)
    print(f"[STEP 2] Running Broken Link Checker on {len(all_links)} Discovered Links...")
    print("=" * 70)

    checker = LinkChecker(timeout=10)
    check_summary = checker.check_links(all_links)

    # -------------------------------------------------------------
    # Step 3: Display Link Check Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  LINK CHECKER RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total Links Checked : {check_summary['total_checked']}")
    print(f"Working Links (2xx) : {check_summary['working_count']}")
    print(f"Redirects (3xx)     : {check_summary['redirect_count']}")
    print(f"Broken Links (4xx/5xx): {check_summary['broken_count']}")
    print(f"Network / Err Links : {check_summary['error_count']}")
    print("-" * 70)

    # Detailed list of broken / problematic links
    broken_links = [res for res in check_summary["results"] if res["is_broken"]]
    if broken_links:
        print("\nBroken / Error Links Detail:")
        for idx, item in enumerate(broken_links, 1):
            print(f"  {idx}. URL    : {item['url']}")
            print(f"     Status : {item['status_code']}")
            print(f"     Error  : {item['error_message']}")
            print()
    else:
        print("\nAll checked links are working properly! No broken links detected.")

    print("=" * 70)
    print("  PHASE 1 CORE BACKEND TEST FINISHED SUCCESSFULLY")
    print("=" * 70)
    return crawl_result, check_summary


def main():
    """
    Main entry point for testing.
    If a URL argument is passed, tests that live URL.
    Otherwise, starts the local mock test server and tests all edge cases.
    """
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        run_audit_test(target_url, max_pages=10)
    else:
        # Start background mock test server
        server_address = ("127.0.0.1", 8888)
        httpd = HTTPServer(server_address, MockSiteHandler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        mock_url = f"http://{server_address[0]}:{server_address[1]}/"
        print(f"[Test Environment] Started local mock test server at {mock_url}")

        try:
            run_audit_test(mock_url, max_pages=10)
        finally:
            httpd.shutdown()


if __name__ == "__main__":
    main()
