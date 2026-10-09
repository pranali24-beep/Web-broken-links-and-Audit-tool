"""
seo_analyzer.py - On-Page SEO Analyzer Component (Phase 2)
----------------------------------------------------------
College Semester Project: Website Broken Link & SEO Health Audit Tool

Analyzes HTML pages using BeautifulSoup for essential on-page SEO metrics:
1. Title Tag: Presence and recommended length (30-60 characters).
2. Meta Description: Presence and recommended length (70-160 characters).
3. H1 Headings: Ensures exactly one primary heading exists.
4. Image Alt Attributes: Audits images for accessibility and SEO alt tags.
5. Issues List: Collects human-readable SEO improvement suggestions.
"""

import re
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup


class SEOAnalyzer:
    """
    Beginner-friendly On-Page SEO Analyzer.
    Parses HTML content and extracts key SEO metrics and issues.
    """

    def __init__(self):
        # Recommended SEO length boundaries
        self.TITLE_MIN_LENGTH = 30
        self.TITLE_MAX_LENGTH = 60
        self.META_DESC_MIN_LENGTH = 70
        self.META_DESC_MAX_LENGTH = 160

    def analyze(self, url, html_content):
        """
        Analyze a webpage's HTML content for on-page SEO best practices.

        :param url: The URL of the page being analyzed
        :param html_content: Raw HTML string
        :return: Dictionary containing structured SEO audit results
        """
        # Default empty result if HTML content is missing or invalid
        if not html_content or not isinstance(html_content, str):
            return {
                "url": url or "",
                "title": "",
                "title_length": 0,
                "meta_description": "",
                "meta_description_length": 0,
                "h1_count": 0,
                "total_images": 0,
                "missing_alt_images": 0,
                "issues": ["Empty or invalid HTML content received"]
            }

        try:
            soup = BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            return {
                "url": url or "",
                "title": "",
                "title_length": 0,
                "meta_description": "",
                "meta_description_length": 0,
                "h1_count": 0,
                "total_images": 0,
                "missing_alt_images": 0,
                "issues": [f"HTML parsing error: {e}"]
            }

        issues = []

        # -------------------------------------------------------------
        # 1. Page Title Analysis
        # -------------------------------------------------------------
        title_tag = soup.find("title")
        title = ""
        if title_tag and title_tag.string:
            title = title_tag.get_text().strip()

        title_length = len(title)

        if not title:
            issues.append("Missing page title")
        elif title_length < self.TITLE_MIN_LENGTH:
            issues.append(f"Page title is too short ({title_length} chars, recommended: {self.TITLE_MIN_LENGTH}-{self.TITLE_MAX_LENGTH})")
        elif title_length > self.TITLE_MAX_LENGTH:
            issues.append(f"Page title is too long ({title_length} chars, recommended: {self.TITLE_MIN_LENGTH}-{self.TITLE_MAX_LENGTH})")

        # -------------------------------------------------------------
        # 2. Meta Description Analysis
        # -------------------------------------------------------------
        # Case-insensitive lookup for <meta name="description" content="...">
        meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        meta_description = ""
        if meta_desc_tag and meta_desc_tag.get("content"):
            meta_description = meta_desc_tag.get("content", "").strip()

        meta_desc_length = len(meta_description)

        if not meta_description:
            issues.append("Missing meta description")
        elif meta_desc_length < self.META_DESC_MIN_LENGTH:
            issues.append(f"Meta description is too short ({meta_desc_length} chars, recommended: {self.META_DESC_MIN_LENGTH}-{self.META_DESC_MAX_LENGTH})")
        elif meta_desc_length > self.META_DESC_MAX_LENGTH:
            issues.append(f"Meta description is too long ({meta_desc_length} chars, recommended: {self.META_DESC_MIN_LENGTH}-{self.META_DESC_MAX_LENGTH})")

        # -------------------------------------------------------------
        # 3. H1 Headings Analysis
        # -------------------------------------------------------------
        h1_tags = soup.find_all("h1")
        h1_count = len(h1_tags)

        if h1_count == 0:
            issues.append("Missing H1 heading")
        elif h1_count > 1:
            issues.append(f"Multiple H1 headings found ({h1_count} found, recommended: exactly 1)")

        # -------------------------------------------------------------
        # 4. Images and Alt Attributes Analysis
        # -------------------------------------------------------------
        img_tags = soup.find_all("img")
        total_images = len(img_tags)
        missing_alt_images = 0

        for img in img_tags:
            alt_text = img.get("alt")
            # If alt attribute is absent or only contains whitespace
            if alt_text is None or not alt_text.strip():
                missing_alt_images += 1

        if missing_alt_images > 0:
            issues.append(f"{missing_alt_images} image(s) missing alt text")

        # -------------------------------------------------------------
        # 5. Return Structured Results
        # -------------------------------------------------------------
        return {
            "url": url,
            "title": title,
            "title_length": title_length,
            "meta_description": meta_description,
            "meta_description_length": meta_desc_length,
            "h1_count": h1_count,
            "total_images": total_images,
            "missing_alt_images": missing_alt_images,
            "issues": issues
        }
