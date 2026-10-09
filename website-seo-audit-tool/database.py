"""
database.py - SQLite Database Management Layer (Phase 3)
--------------------------------------------------------
College Semester Project: Website Broken Link & SEO Health Audit Tool

Provides database operations for storing and retrieving:
1. Audits: High-level scan session details and overall scores.
2. Pages: Individual crawled URLs with on-page SEO metrics.
3. Links: Discovered hyperlinks with HTTP status codes and broken link flags.

Uses Python's standard `sqlite3` module with parameterized queries.
"""

import os
import sqlite3
from datetime import datetime

# Default database file path (located in website-seo-audit-tool project root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "audit_database.db")


def get_db_path(db_path=None):
    """
    Returns the absolute path to the SQLite database file.
    """
    return db_path or DEFAULT_DB_PATH


def get_connection(db_path=None):
    """
    Creates and returns a connection to the SQLite database.
    Configures row_factory to sqlite3.Row for dictionary-like column access
    and enables foreign key constraint enforcement.
    """
    path = get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def close_connection(conn):
    """
    Safely closes a database connection if open.
    """
    if conn:
        try:
            conn.close()
        except Exception:
            pass


def initialize_database(db_path=None):
    """
    Initializes the database schema with three core tables:
    - audits: audit overview and summary metrics
    - pages: crawled page details and SEO stats
    - links: extracted hyperlinks and status codes
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # 1. Audits Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            pages_crawled INTEGER DEFAULT 0,
            total_links_checked INTEGER DEFAULT 0,
            broken_links_count INTEGER DEFAULT 0,
            seo_score REAL DEFAULT 0,
            status TEXT DEFAULT 'In Progress'
        );
        """)

        # 2. Pages Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_id INTEGER NOT NULL,
            page_url TEXT NOT NULL,
            status_code INTEGER,
            title TEXT,
            meta_description TEXT,
            h1_count INTEGER DEFAULT 0,
            total_images INTEGER DEFAULT 0,
            missing_alt_images INTEGER DEFAULT 0,
            load_time_ms REAL DEFAULT 0.0,
            FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
        );
        """)

        # 3. Links Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_id INTEGER NOT NULL,
            source_page_url TEXT,
            target_url TEXT NOT NULL,
            link_type TEXT DEFAULT 'internal',
            status_code INTEGER,
            is_broken INTEGER DEFAULT 0,
            error_message TEXT,
            FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
        );
        """)

        conn.commit()
        return True

    except sqlite3.Error as e:
        print(f"[Database Error] Schema initialization failed: {e}")
        conn.rollback()
        return False

    finally:
        close_connection(conn)


def create_audit(base_url, status="Completed", pages_crawled=0,
                 total_links_checked=0, broken_links_count=0, seo_score=0.0,
                 created_at=None, db_path=None):
    """
    Inserts a new audit session record and returns its generated audit_id.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if created_at is None:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        query = """
        INSERT INTO audits (
            base_url, created_at, pages_crawled, total_links_checked,
            broken_links_count, seo_score, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        cursor.execute(query, (
            base_url,
            created_at,
            pages_crawled,
            total_links_checked,
            broken_links_count,
            float(seo_score),
            status
        ))
        conn.commit()
        audit_id = cursor.lastrowid
        return audit_id

    except sqlite3.Error as e:
        print(f"[Database Error] Failed to create audit for {base_url}: {e}")
        conn.rollback()
        return None

    finally:
        close_connection(conn)


def update_audit(audit_id, pages_crawled=None, total_links_checked=None,
                 broken_links_count=None, seo_score=None, status=None,
                 db_path=None):
    """
    Updates summary metrics and status for an existing audit session.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    fields_to_update = []
    values = []

    if pages_crawled is not None:
        fields_to_update.append("pages_crawled = ?")
        values.append(int(pages_crawled))
    if total_links_checked is not None:
        fields_to_update.append("total_links_checked = ?")
        values.append(int(total_links_checked))
    if broken_links_count is not None:
        fields_to_update.append("broken_links_count = ?")
        values.append(int(broken_links_count))
    if seo_score is not None:
        fields_to_update.append("seo_score = ?")
        values.append(float(seo_score))
    if status is not None:
        fields_to_update.append("status = ?")
        values.append(str(status))

    if not fields_to_update:
        close_connection(conn)
        return False

    values.append(audit_id)
    query = f"UPDATE audits SET {', '.join(fields_to_update)} WHERE id = ?;"

    try:
        cursor.execute(query, tuple(values))
        conn.commit()
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"[Database Error] Failed to update audit {audit_id}: {e}")
        conn.rollback()
        return False

    finally:
        close_connection(conn)


def add_page(audit_id, page_url, status_code=200, title="",
             meta_description="", h1_count=0, total_images=0,
             missing_alt_images=0, load_time_ms=0.0, db_path=None):
    """
    Inserts a crawled page record associated with an audit session.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO pages (
            audit_id, page_url, status_code, title, meta_description,
            h1_count, total_images, missing_alt_images, load_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        cursor.execute(query, (
            audit_id,
            page_url,
            status_code,
            title or "",
            meta_description or "",
            int(h1_count),
            int(total_images),
            int(missing_alt_images),
            float(load_time_ms)
        ))
        conn.commit()
        page_id = cursor.lastrowid
        return page_id

    except sqlite3.Error as e:
        print(f"[Database Error] Failed to add page {page_url} to audit {audit_id}: {e}")
        conn.rollback()
        return None

    finally:
        close_connection(conn)


def add_link(audit_id, target_url, source_page_url="", link_type="internal",
             status_code=200, is_broken=0, error_message="", db_path=None):
    """
    Inserts a hyperlink verification record associated with an audit session.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO links (
            audit_id, source_page_url, target_url, link_type,
            status_code, is_broken, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        cursor.execute(query, (
            audit_id,
            source_page_url or "",
            target_url,
            link_type or "internal",
            status_code,
            1 if is_broken else 0,
            error_message or ""
        ))
        conn.commit()
        link_id = cursor.lastrowid
        return link_id

    except sqlite3.Error as e:
        print(f"[Database Error] Failed to add link {target_url} to audit {audit_id}: {e}")
        conn.rollback()
        return None

    finally:
        close_connection(conn)


def get_audit(audit_id, db_path=None):
    """
    Retrieves an audit record by ID along with its associated pages and links.
    Returns a structured dictionary, or None if not found.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Retrieve main audit record
        cursor.execute("SELECT * FROM audits WHERE id = ?;", (audit_id,))
        audit_row = cursor.fetchone()
        if not audit_row:
            return None

        audit_dict = dict(audit_row)

        # Retrieve associated pages
        cursor.execute("SELECT * FROM pages WHERE audit_id = ? ORDER BY id ASC;", (audit_id,))
        pages_rows = cursor.fetchall()
        audit_dict["pages"] = [dict(p) for p in pages_rows]

        # Retrieve associated links
        cursor.execute("SELECT * FROM links WHERE audit_id = ? ORDER BY id ASC;", (audit_id,))
        links_rows = cursor.fetchall()
        audit_dict["links"] = [dict(l) for l in links_rows]

        return audit_dict

    except sqlite3.Error as e:
        print(f"[Database Error] Failed to retrieve audit {audit_id}: {e}")
        return None

    finally:
        close_connection(conn)


def get_audit_history(limit=50, db_path=None):
    """
    Retrieves all audit summary records ordered by newest first (descending by id / created_at).
    Designed for easy display on the audit history page.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        query = "SELECT * FROM audits ORDER BY id DESC LIMIT ?;"
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except sqlite3.Error as e:
        print(f"[Database Error] Failed to retrieve audit history: {e}")
        return []

    finally:
        close_connection(conn)


def delete_audit(audit_id, db_path=None):
    """
    Deletes an audit record and cascades deletion to associated pages and links.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM audits WHERE id = ?;", (audit_id,))
        conn.commit()
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"[Database Error] Failed to delete audit {audit_id}: {e}")
        conn.rollback()
        return False

    finally:
        close_connection(conn)
