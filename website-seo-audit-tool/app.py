"""
app.py - Flask Backend Application (Phase 4)
--------------------------------------------
College Semester Project: Website Broken Link & SEO Health Audit Tool

Provides REST API endpoints for:
1. Health & status verification (GET /, GET /api/health)
2. Initiating on-demand SEO & Broken Link Audits (POST /api/audit)
3. Retrieving detailed audit results (GET /api/audit/<audit_id>)
4. Retrieving audit scan history (GET /api/history, GET /api/audits)
5. Deleting audit records (DELETE /api/audit/<audit_id>)

Integrates Phase 1 (Crawler, Link Checker), Phase 2 (SEO Analyzer, Score Calculator),
and Phase 3 (SQLite Database Layer).
"""

import os
import time
from urllib.parse import urlparse
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify, send_from_directory

# Base directory for serving existing static HTML and CSS files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Core module imports from existing Phase 1 & Phase 2 implementations
from core.crawler import WebCrawler
from core.link_checker import LinkChecker
from core.seo_analyzer import SEOAnalyzer
from core.score_calculator import ScoreCalculator

# Database layer from existing Phase 3 implementation
import database

# Initialize Flask application
app = Flask(__name__)

# Initialize SQLite database schema on startup
database.initialize_database()


@app.after_request
def add_cors_headers(response):
    """
    Enable Cross-Origin Resource Sharing (CORS) headers on all responses
    to allow smooth frontend communication across local servers/ports.
    """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


# -----------------------------------------------------------------------------
# PHASE 5A: FRONTEND ROUTES & CSS SERVING
# -----------------------------------------------------------------------------

@app.route("/", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def serve_index():
    """
    Serve index.html landing and audit input page.
    """
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/audit-results.html", methods=["GET"])
def serve_audit_results():
    """
    Serve audit-results.html report page.
    """
    return send_from_directory(BASE_DIR, "audit-results.html")


@app.route("/history.html", methods=["GET"])
def serve_history_page():
    """
    Serve history.html audit history overview page.
    """
    return send_from_directory(BASE_DIR, "history.html")


@app.route("/about.html", methods=["GET"])
def serve_about_page():
    """
    Serve about.html project documentation and architecture page.
    """
    return send_from_directory(BASE_DIR, "about.html")


@app.route("/css/<path:filename>", methods=["GET"])
def serve_css(filename):
    """
    Serve CSS stylesheet files directly from the existing css/ directory.
    """
    return send_from_directory(os.path.join(BASE_DIR, "css"), filename)


@app.route("/assets/<path:filename>", methods=["GET"])
def serve_assets(filename):
    """
    Serve static assets (e.g. images, icons) directly from the assets/ directory.
    """
    return send_from_directory(os.path.join(BASE_DIR, "assets"), filename)


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Backend health check endpoint.
    """
    return jsonify({
        "status": "success",
        "message": "Website SEO Audit Tool backend is running"
    }), 200


# -----------------------------------------------------------------------------
# TASK 4 - 10: AUDIT EXECUTION API
# -----------------------------------------------------------------------------

@app.route("/api/audit", methods=["POST", "OPTIONS"])
def start_audit():
    """
    POST /api/audit
    Receives target website URL, executes BFS crawl, checks discovered links,
    analyzes on-page SEO metrics, computes health scores, stores everything in
    SQLite database, and returns summary response.
    """
    if request.method == "OPTIONS":
        return "", 200

    # Parse request payload (supports JSON and form-encoded data)
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    raw_url = data.get("url")

    # 1. Validate URL Presence
    if not raw_url or not str(raw_url).strip():
        return jsonify({
            "status": "error",
            "message": "URL is required"
        }), 400

    raw_url = str(raw_url).strip()

    # 2. Normalize and Validate URL Format
    normalized_url = WebCrawler.normalize_url(raw_url)
    parsed = urlparse(normalized_url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return jsonify({
            "status": "error",
            "message": "Invalid URL format. Please provide a valid HTTP or HTTPS URL (e.g., https://example.com)."
        }), 400

    # Optional max_pages parameter (defaults to 10)
    try:
        max_pages = int(data.get("max_pages", 10))
        max_pages = max(1, min(max_pages, 50))  # Bound between 1 and 50
    except (ValueError, TypeError):
        max_pages = 10

    print(f"\n[API /api/audit] Starting audit for: {normalized_url} (Max pages: {max_pages})")

    # -------------------------------------------------------------------------
    # TASK 5: CRAWLER EXECUTION (core/crawler.py)
    # -------------------------------------------------------------------------
    crawler = WebCrawler(start_url=normalized_url, max_pages=max_pages, timeout=10)
    crawl_result = crawler.crawl()

    crawled_pages = crawl_result.get("crawled_pages", [])
    all_discovered_links = crawl_result.get("all_discovered_links", [])

    # -------------------------------------------------------------------------
    # TASK 7 & 8: SEO ANALYSIS & SCORE CALCULATION
    # (core/seo_analyzer.py & core/score_calculator.py)
    # -------------------------------------------------------------------------
    seo_analyzer = SEOAnalyzer()
    processed_pages = []
    page_scores = []

    # Map discovered links to their source page URL for relational tracking
    link_source_map = {}

    for page in crawled_pages:
        page_url = page["url"]
        
        # Track discovered links for link checking source mapping
        for child_link in page.get("discovered_links", []):
            if child_link not in link_source_map:
                link_source_map[child_link] = page_url

        # Fetch page HTML and measure latency
        fetch_start = time.time()
        html_content, status_code, content_type, final_url, err_msg = crawler.fetch_page(page_url)
        load_time_ms = round((time.time() - fetch_start) * 1000, 2)

        effective_status = status_code if status_code is not None else (page.get("status_code") or 0)

        # Run on-page SEO analyzer
        seo_metrics = seo_analyzer.analyze(page_url, html_content or "")
        score_info = ScoreCalculator.calculate_score(seo_metrics)
        page_score = score_info.get("score", 0)
        page_scores.append(page_score)

        processed_pages.append({
            "page_url": page_url,
            "status_code": effective_status,
            "title": seo_metrics.get("title", ""),
            "meta_description": seo_metrics.get("meta_description", ""),
            "h1_count": seo_metrics.get("h1_count", 0),
            "total_images": seo_metrics.get("total_images", 0),
            "missing_alt_images": seo_metrics.get("missing_alt_images", 0),
            "load_time_ms": load_time_ms,
            "seo_score": page_score,
            "issues": seo_metrics.get("issues", [])
        })

    # Overall SEO Health Score (average across crawled pages)
    if page_scores:
        overall_seo_score = round(sum(page_scores) / len(page_scores), 1)
    else:
        overall_seo_score = 0.0

    # -------------------------------------------------------------------------
    # TASK 6: LINK CHECKER EXECUTION (core/link_checker.py)
    # -------------------------------------------------------------------------
    link_checker = LinkChecker(timeout=10)
    checked_summary = link_checker.check_links(all_discovered_links)
    
    processed_links = []
    broken_count = 0

    for item in checked_summary.get("results", []):
        target_url = item["url"]
        source_url = link_source_map.get(target_url, normalized_url)
        is_internal = crawler.is_same_domain(target_url)
        link_type = "internal" if is_internal else "external"
        is_broken = 1 if item.get("is_broken") else 0
        if is_broken:
            broken_count += 1

        processed_links.append({
            "source_page_url": source_url,
            "target_url": target_url,
            "link_type": link_type,
            "status_code": item.get("status_code"),
            "is_broken": is_broken,
            "error_message": item.get("error_message") or ""
        })

    # -------------------------------------------------------------------------
    # TASK 9: SAVE TO SQLITE DATABASE (database.py)
    # -------------------------------------------------------------------------
    audit_id = database.create_audit(
        base_url=normalized_url,
        status="Completed",
        pages_crawled=len(processed_pages),
        total_links_checked=len(processed_links),
        broken_links_count=broken_count,
        seo_score=overall_seo_score
    )

    if not audit_id:
        return jsonify({
            "status": "error",
            "message": "Failed to save audit record to SQLite database."
        }), 500

    # Save crawled pages
    for p in processed_pages:
        database.add_page(
            audit_id=audit_id,
            page_url=p["page_url"],
            status_code=p["status_code"],
            title=p["title"],
            meta_description=p["meta_description"],
            h1_count=p["h1_count"],
            total_images=p["total_images"],
            missing_alt_images=p["missing_alt_images"],
            load_time_ms=p["load_time_ms"]
        )

    # Save checked links
    for l in processed_links:
        database.add_link(
            audit_id=audit_id,
            target_url=l["target_url"],
            source_page_url=l["source_page_url"],
            link_type=l["link_type"],
            status_code=l["status_code"],
            is_broken=l["is_broken"],
            error_message=l["error_message"]
        )

    print(f"[API /api/audit] Audit #{audit_id} completed: {len(processed_pages)} pages, {len(processed_links)} links, Score: {overall_seo_score}")

    # -------------------------------------------------------------------------
    # TASK 10: API RESPONSE
    # -------------------------------------------------------------------------
    return jsonify({
        "status": "success",
        "audit_id": audit_id,
        "base_url": normalized_url,
        "pages_crawled": len(processed_pages),
        "total_links_checked": len(processed_links),
        "broken_links_count": broken_count,
        "seo_score": overall_seo_score,
        "message": "Audit completed successfully"
    }), 200


# -----------------------------------------------------------------------------
# TASK 11: AUDIT RESULT & HISTORY APIS
# -----------------------------------------------------------------------------

@app.route("/api/audit/<int:audit_id>", methods=["GET"])
def get_audit_details(audit_id):
    """
    GET /api/audit/<audit_id>
    Retrieves full audit report including crawled pages and checked links.
    """
    audit_data = database.get_audit(audit_id)
    if not audit_data:
        return jsonify({
            "status": "error",
            "message": f"Audit with ID {audit_id} not found"
        }), 404

    return jsonify({
        "status": "success",
        "data": audit_data
    }), 200


@app.route("/api/history", methods=["GET"])
@app.route("/api/audits", methods=["GET"])
def get_history():
    """
    GET /api/history (or GET /api/audits)
    Retrieves chronological audit history list.
    Supports optional ?limit=query parameter (default: 50).
    """
    limit = request.args.get("limit", 50)
    try:
        limit = int(limit)
        limit = max(1, min(limit, 200))
    except (ValueError, TypeError):
        limit = 50

    history = database.get_audit_history(limit=limit)
    return jsonify({
        "status": "success",
        "count": len(history),
        "history": history
    }), 200


@app.route("/api/audit/<int:audit_id>", methods=["DELETE"])
def remove_audit(audit_id):
    """
    DELETE /api/audit/<audit_id>
    Deletes an audit session and cascades to associated pages and links.
    """
    deleted = database.delete_audit(audit_id)
    if not deleted:
        return jsonify({
            "status": "error",
            "message": f"Audit with ID {audit_id} not found"
        }), 404

    return jsonify({
        "status": "success",
        "message": f"Audit #{audit_id} deleted successfully"
    }), 200


# -----------------------------------------------------------------------------
# APPLICATION ENTRYPOINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Website Broken Link & SEO Health Audit Tool - Backend")
    print("  Server starting on http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
