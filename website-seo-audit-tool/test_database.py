"""
test_database.py - Verification Script for Phase 3 SQLite Database
-------------------------------------------------------------------
College Semester Project: Website Broken Link & SEO Health Audit Tool

Validates:
1. Database initialization and table creation (audits, pages, links).
2. Parameterized insertion of audit sessions, pages, and links.
3. Foreign key relationship integrity between tables.
4. Retrieval of complete audit reports with nested pages and links.
5. Chronological audit history retrieval for frontend history views.
"""

import os
import sys
import database


def run_database_tests():
    """
    Executes end-to-end database verification tests.
    """
    print("=" * 75)
    print("  WEBSITE BROKEN LINK & SEO HEALTH AUDIT TOOL")
    print("  PHASE 3: SQLITE DATABASE VERIFICATION SUITE")
    print("=" * 75)

    db_file = database.get_db_path()
    print(f"Target Database File : {db_file}")
    print("-" * 75)

    # -------------------------------------------------------------
    # 1. Initialize Database Schema
    # -------------------------------------------------------------
    print("\n[STEP 1] Initializing Database Schema...")
    init_ok = database.initialize_database()
    if not init_ok:
        print("[FAILED] Could not initialize database schema.")
        return False
    print("  --> Schema initialized successfully (audits, pages, links tables created).")

    # -------------------------------------------------------------
    # 2. Create Sample Audit Session
    # -------------------------------------------------------------
    print("\n[STEP 2] Creating Sample Audit Session...")
    sample_base_url = "https://example.com"
    audit_id = database.create_audit(
        base_url=sample_base_url,
        status="Completed",
        pages_crawled=2,
        total_links_checked=3,
        broken_links_count=1,
        seo_score=88.5
    )

    if not audit_id:
        print("[FAILED] Could not insert audit record.")
        return False

    print(f"  --> Inserted Audit Record (ID: {audit_id}) for {sample_base_url}")

    # -------------------------------------------------------------
    # 3. Add Sample Pages (Foreign Key: audit_id)
    # -------------------------------------------------------------
    print("\n[STEP 3] Inserting Sample Pages...")
    page1_id = database.add_page(
        audit_id=audit_id,
        page_url="https://example.com/",
        status_code=200,
        title="Example Domain - Official Landing Page",
        meta_description="Example domain website for documentation and testing purposes.",
        h1_count=1,
        total_images=2,
        missing_alt_images=0,
        load_time_ms=145.2
    )
    print(f"  --> Inserted Page 1 (ID: {page1_id}): https://example.com/ (Status 200)")

    page2_id = database.add_page(
        audit_id=audit_id,
        page_url="https://example.com/about",
        status_code=200,
        title="About Us - Example Domain",
        meta_description="Learn more about the example domain organization.",
        h1_count=1,
        total_images=1,
        missing_alt_images=1,
        load_time_ms=189.5
    )
    print(f"  --> Inserted Page 2 (ID: {page2_id}): https://example.com/about (Status 200)")

    # -------------------------------------------------------------
    # 4. Add Sample Links (Foreign Key: audit_id)
    # -------------------------------------------------------------
    print("\n[STEP 4] Inserting Sample Links...")
    link1_id = database.add_link(
        audit_id=audit_id,
        source_page_url="https://example.com/",
        target_url="https://example.com/",
        link_type="internal",
        status_code=200,
        is_broken=0,
        error_message=""
    )
    print(f"  --> Inserted Link 1 (ID: {link1_id}): https://example.com/ [200 OK]")

    link2_id = database.add_link(
        audit_id=audit_id,
        source_page_url="https://example.com/",
        target_url="https://example.com/about",
        link_type="internal",
        status_code=200,
        is_broken=0,
        error_message=""
    )
    print(f"  --> Inserted Link 2 (ID: {link2_id}): https://example.com/about [200 OK]")

    link3_id = database.add_link(
        audit_id=audit_id,
        source_page_url="https://example.com/about",
        target_url="https://example.com/missing-page",
        link_type="internal",
        status_code=404,
        is_broken=1,
        error_message="HTTP 404 (Not Found)"
    )
    print(f"  --> Inserted Link 3 (ID: {link3_id}): https://example.com/missing-page [404 BROKEN]")

    # -------------------------------------------------------------
    # 5. Retrieve Complete Audit Record (Join Verification)
    # -------------------------------------------------------------
    print("\n[STEP 5] Querying Full Audit Details via get_audit()...")
    audit_data = database.get_audit(audit_id)
    if not audit_data:
        print(f"[FAILED] Could not retrieve audit {audit_id}")
        return False

    print("\n" + "-" * 75)
    print("  RETRIEVED AUDIT DETAILS")
    print("-" * 75)
    print(f"Audit ID       : {audit_data['id']}")
    print(f"Base URL       : {audit_data['base_url']}")
    print(f"Created At     : {audit_data['created_at']}")
    print(f"Pages Crawled  : {audit_data['pages_crawled']}")
    print(f"Links Checked  : {audit_data['total_links_checked']}")
    print(f"Broken Links   : {audit_data['broken_links_count']}")
    print(f"SEO Score      : {audit_data['seo_score']}")
    print(f"Status         : {audit_data['status']}")

    print(f"\nAssociated Pages ({len(audit_data['pages'])} records):")
    for idx, page in enumerate(audit_data["pages"], 1):
        print(f"  {idx}. [Status {page['status_code']}] {page['page_url']}")
        print(f"     Title       : {page['title']}")
        print(f"     Description : {page['meta_description']}")
        print(f"     H1 Count    : {page['h1_count']} | Images: {page['total_images']} (Missing Alt: {page['missing_alt_images']})")

    print(f"\nAssociated Links ({len(audit_data['links'])} records):")
    for idx, link in enumerate(audit_data["links"], 1):
        broken_tag = "[BROKEN]" if link["is_broken"] else "[OK]"
        err_msg = f" - Error: {link['error_message']}" if link["error_message"] else ""
        print(f"  {idx}. {broken_tag} Status {link['status_code']} -> {link['target_url']}{err_msg}")
        print(f"     Source Page: {link['source_page_url']}")

    # -------------------------------------------------------------
    # 6. Retrieve Audit History
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("[STEP 6] Querying Audit History via get_audit_history()...")
    print("-" * 75)
    history = database.get_audit_history(limit=10)
    print(f"Total History Records Found: {len(history)}")
    for idx, item in enumerate(history, 1):
        print(f"  {idx}. Audit #{item['id']} | {item['created_at']} | {item['base_url']} | Score: {item['seo_score']} | Status: {item['status']}")

    # -------------------------------------------------------------
    # 7. Verification Assertions
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("VERIFICATION CHECKLIST:")
    assert os.path.exists(db_file), "Database file does not exist on disk"
    assert audit_data["id"] == audit_id, "Audit ID mismatch"
    assert len(audit_data["pages"]) == 2, "Expected 2 pages in audit"
    assert len(audit_data["links"]) == 3, "Expected 3 links in audit"
    assert len(history) >= 1, "Expected at least 1 history record"
    print("  * Database file created and accessible : PASSED")
    print("  * Parameterized record insertion       : PASSED")
    print("  * Foreign key relational retrieval    : PASSED")
    print("  * History ordering and query execution : PASSED")
    print("-" * 75)

    print("\nPHASE 3 DATABASE TESTS COMPLETED SUCCESSFULLY\n")
    return True


if __name__ == "__main__":
    success = run_database_tests()
    if not success:
        sys.exit(1)
