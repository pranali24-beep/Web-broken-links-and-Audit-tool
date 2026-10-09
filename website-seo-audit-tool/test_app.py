"""
test_app.py - Phase 4 Flask Backend Verification Suite
------------------------------------------------------
College Semester Project: Website Broken Link & SEO Health Audit Tool

Validates:
1. Root (GET /) and Health Check (GET /api/health) endpoints.
2. Input validation for POST /api/audit (missing URL, invalid schemes).
3. End-to-end Audit workflow execution (crawling, SEO analysis, link checking, DB persistence).
4. Audit result retrieval via GET /api/audit/<audit_id> (both existing and 404 not found).
5. Audit history retrieval via GET /api/history.
6. Audit deletion via DELETE /api/audit/<audit_id>.
"""

import sys
import json
from app import app
import database


def run_flask_backend_tests():
    """
    Executes end-to-end verification of all Phase 4 Flask API endpoints.
    """
    print("=" * 75)
    print("  WEBSITE BROKEN LINK & SEO HEALTH AUDIT TOOL")
    print("  PHASE 4: FLASK BACKEND VERIFICATION SUITE")
    print("=" * 75)

    client = app.test_client()

    # -------------------------------------------------------------
    # 1. Frontend Pages, CSS & Health Endpoints (Phase 5A)
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Frontend Pages, CSS Serving & Health Endpoints...")
    
    # 1.1 Root / & /index.html
    res_root = client.get("/")
    assert res_root.status_code == 200, f"Expected 200 for GET /, got {res_root.status_code}"
    assert b"SEO Health Auditor" in res_root.data, "Root endpoint did not return index.html content"
    print("  * GET /                  : PASSED (Status 200 -> index.html served)")

    res_index = client.get("/index.html")
    assert res_index.status_code == 200, f"Expected 200 for GET /index.html, got {res_index.status_code}"
    assert b"SEO Health Auditor" in res_index.data
    assert b'id="audit-form"' in res_index.data, "audit-form ID missing in index.html"
    assert b'id="target-url"' in res_index.data, "target-url ID missing in index.html"
    assert b'id="submit-btn"' in res_index.data, "submit-btn ID missing in index.html"
    assert b'id="audit-feedback"' in res_index.data, "audit-feedback element missing in index.html"
    assert b'/api/audit' in res_index.data, "POST /api/audit integration missing in index.html"
    assert b'/audit-results.html?audit_id=' in res_index.data, "audit_id redirect logic missing in index.html"
    print("  * GET /index.html (Form) : PASSED (Phase 5B Form & API integration verified)")

    # 1.2 Audit Results Page
    res_audit_page = client.get("/audit-results.html")
    assert res_audit_page.status_code == 200, f"Expected 200 for GET /audit-results.html, got {res_audit_page.status_code}"
    assert b"Audit Report" in res_audit_page.data
    print("  * GET /audit-results.html: PASSED (Status 200 -> audit-results.html served)")

    # 1.3 History Page
    res_hist_page = client.get("/history.html")
    assert res_hist_page.status_code == 200, f"Expected 200 for GET /history.html, got {res_hist_page.status_code}"
    assert b"Audit History" in res_hist_page.data
    print("  * GET /history.html      : PASSED (Status 200 -> history.html served)")

    # 1.4 About Page
    res_about_page = client.get("/about.html")
    assert res_about_page.status_code == 200, f"Expected 200 for GET /about.html, got {res_about_page.status_code}"
    assert b"About Project" in res_about_page.data
    print("  * GET /about.html        : PASSED (Status 200 -> about.html served)")

    # 1.5 CSS Serving
    res_css = client.get("/css/style.css")
    assert res_css.status_code == 200, f"Expected 200 for GET /css/style.css, got {res_css.status_code}"
    assert len(res_css.data) > 0, "CSS file content is empty"
    print("  * GET /css/style.css     : PASSED (Status 200 -> css/style.css served)")

    # 1.6 Backend API Health Check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Expected 200 for GET /api/health, got {res_health.status_code}"
    health_json = res_health.get_json()
    assert health_json["status"] == "success", "Health endpoint status not success"
    assert "Website SEO Audit Tool backend is running" in health_json["message"]
    print(f"  * GET /api/health        : PASSED (Status {res_health.status_code}) -> {health_json['message']}")

    # -------------------------------------------------------------
    # 2. Input Validation (Error Handling)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Input Validation & Error Handling (POST /api/audit)...")

    # 2.1 Missing URL
    res_missing = client.post("/api/audit", json={})
    assert res_missing.status_code == 400, f"Expected 400 for missing URL, got {res_missing.status_code}"
    missing_json = res_missing.get_json()
    assert missing_json["status"] == "error"
    assert "URL is required" in missing_json["message"]
    print(f"  * Missing URL Validation : PASSED (400 Bad Request) -> {missing_json['message']}")

    # 2.2 Empty URL
    res_empty = client.post("/api/audit", json={"url": "   "})
    assert res_empty.status_code == 400, f"Expected 400 for empty URL, got {res_empty.status_code}"
    print("  * Empty String Validation: PASSED (400 Bad Request)")

    # 2.3 Invalid Scheme (e.g. ftp://)
    res_bad_scheme = client.post("/api/audit", json={"url": "ftp://example.com"})
    assert res_bad_scheme.status_code == 400, f"Expected 400 for unsupported scheme, got {res_bad_scheme.status_code}"
    bad_scheme_json = res_bad_scheme.get_json()
    assert bad_scheme_json["status"] == "error"
    print(f"  * Bad Scheme Validation  : PASSED (400 Bad Request) -> {bad_scheme_json['message']}")

    # -------------------------------------------------------------
    # 3. End-to-End Audit Execution (POST /api/audit)
    # -------------------------------------------------------------
    print("\n[TEST 3] Running End-to-End Audit via POST /api/audit...")
    target_url = "https://example.com"
    res_audit = client.post("/api/audit", json={"url": target_url, "max_pages": 2})
    assert res_audit.status_code == 200, f"Expected 200 for valid audit, got {res_audit.status_code}"
    audit_json = res_audit.get_json()

    assert audit_json["status"] == "success"
    assert "audit_id" in audit_json and audit_json["audit_id"] > 0
    assert audit_json["pages_crawled"] >= 1
    assert "seo_score" in audit_json
    created_audit_id = audit_json["audit_id"]

    print(f"  * Audit Created ID       : {created_audit_id}")
    print(f"  * Base URL               : {audit_json['base_url']}")
    print(f"  * Pages Crawled          : {audit_json['pages_crawled']}")
    print(f"  * Total Links Checked    : {audit_json['total_links_checked']}")
    print(f"  * Broken Links Count     : {audit_json['broken_links_count']}")
    print(f"  * SEO Score              : {audit_json['seo_score']}")
    print("  --> POST /api/audit End-to-End Execution: PASSED")

    # -------------------------------------------------------------
    # 4. Audit Details Query (GET /api/audit/<id>)
    # -------------------------------------------------------------
    print(f"\n[TEST 4] Querying Audit #{created_audit_id} Details (GET /api/audit/{created_audit_id})...")
    res_details = client.get(f"/api/audit/{created_audit_id}")
    assert res_details.status_code == 200, f"Expected 200 for GET audit details, got {res_details.status_code}"
    details_json = res_details.get_json()

    assert details_json["status"] == "success"
    data = details_json["data"]
    assert data["id"] == created_audit_id
    assert "pages" in data and isinstance(data["pages"], list)
    assert "links" in data and isinstance(data["links"], list)
    print(f"  * Audit Record ID        : {data['id']}")
    print(f"  * Nested Pages Attached  : {len(data['pages'])} page record(s)")
    print(f"  * Nested Links Attached  : {len(data['links'])} link record(s)")
    if data["pages"]:
        p0 = data["pages"][0]
        print(f"    - First Page Title     : '{p0['title']}' (Length: {len(p0['title'])})")
        print(f"    - First Page Status    : {p0['status_code']} (Load Time: {p0['load_time_ms']}ms)")
    print("  --> GET /api/audit/<id> : PASSED")

    # 4.1 Non-existent Audit (404)
    res_404 = client.get("/api/audit/9999999")
    assert res_404.status_code == 404, f"Expected 404 for non-existent audit, got {res_404.status_code}"
    print("  * 404 Not Found Handling : PASSED")

    # -------------------------------------------------------------
    # 5. Audit History Query (GET /api/history)
    # -------------------------------------------------------------
    print("\n[TEST 5] Querying History via GET /api/history...")
    res_hist = client.get("/api/history?limit=10")
    assert res_hist.status_code == 200, f"Expected 200 for GET /api/history, got {res_hist.status_code}"
    hist_json = res_hist.get_json()

    assert hist_json["status"] == "success"
    assert hist_json["count"] >= 1
    assert len(hist_json["history"]) >= 1
    print(f"  * History Items Returned : {hist_json['count']}")
    latest = hist_json["history"][0]
    print(f"  * Latest Audit Entry     : #{latest['id']} | {latest['created_at']} | {latest['base_url']} | Score: {latest['seo_score']}")
    print("  --> GET /api/history     : PASSED")

    # -------------------------------------------------------------
    # 6. Audit Deletion (DELETE /api/audit/<id>)
    # -------------------------------------------------------------
    print(f"\n[TEST 6] Deleting Audit #{created_audit_id} via DELETE /api/audit/{created_audit_id}...")
    res_del = client.delete(f"/api/audit/{created_audit_id}")
    assert res_del.status_code == 200, f"Expected 200 for DELETE, got {res_del.status_code}"
    del_json = res_del.get_json()
    assert del_json["status"] == "success"

    # Confirm deletion (should now return 404)
    res_after_del = client.get(f"/api/audit/{created_audit_id}")
    assert res_after_del.status_code == 404, "Deleted audit was still returned by GET"
    print(f"  * Deletion and Cascade   : PASSED (Verified #{created_audit_id} no longer exists)")

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 75)
    print("  ALL PHASE 4 FLASK BACKEND TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 75 + "\n")
    return True


if __name__ == "__main__":
    success = run_flask_backend_tests()
    if not success:
        sys.exit(1)
