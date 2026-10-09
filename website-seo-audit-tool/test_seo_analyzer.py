"""
test_seo_analyzer.py - Test Script for Phase 2 (SEO Analyzer & Score Calculator)
--------------------------------------------------------------------------------
College Semester Project: Website Broken Link & SEO Health Audit Tool

Validates:
1. SEOAnalyzer: Title tag, meta description, H1 count, and image alt text analysis.
2. ScoreCalculator: 0-100 scoring algorithm, deductions tracking, and rating categorization.
"""

from core.seo_analyzer import SEOAnalyzer
from core.score_calculator import ScoreCalculator


# ==============================================================================
# Sample HTML Test Cases
# ==============================================================================

# TEST 1: Good Page (Well-optimized On-Page SEO)
# - Title: 44 characters (Within recommended 30-60)
# - Meta Description: 124 characters (Within recommended 70-160)
# - H1: Exactly 1 heading
# - Images: 2 images, both with valid alt attributes
GOOD_HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Modern Web Development &amp; SEO Best Practices</title>
    <meta name="description" content="Discover comprehensive guides and industry tips on building high-performance, SEO-optimized web applications with Python.">
</head>
<body>
    <header>
        <h1>Complete Guide to Web Performance and SEO</h1>
    </header>
    <main>
        <p>Optimizing web pages ensures better search rankings and user accessibility.</p>
        <img src="/assets/seo-diagram.png" alt="Detailed diagram illustrating on-page SEO best practices">
        <img src="/assets/chart.png" alt="Performance growth benchmark chart">
    </main>
</body>
</html>
"""

# TEST 2: Bad Page (Poorly-optimized / Problematic Page)
# - Title: Missing (<title> is absent)
# - Meta Description: Missing
# - H1: 0 (No <h1> tag present)
# - Images: 3 images with NO alt text
# - Extra issue: <h2> used without primary <h1>
BAD_HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <!-- Missing title tag completely -->
    <!-- Missing meta description -->
</head>
<body>
    <div>
        <h2>Welcome to Our Unoptimized Sample Site</h2>
        <p>This page violates multiple on-page SEO best practices.</p>
        <img src="/banner.jpg">
        <img src="/logo.png" alt="">
        <img src="/icon.svg">
    </div>
</body>
</html>
"""


def run_seo_test(test_name, url, html_content):
    """
    Runs SEOAnalyzer and ScoreCalculator against a given HTML string
    and prints formatted analysis results.
    """
    print("=" * 75)
    print(f"  {test_name.upper()}")
    print("=" * 75)
    print(f"Target URL : {url}")
    print("-" * 75)

    analyzer = SEOAnalyzer()
    seo_result = analyzer.analyze(url, html_content)
    score_result = ScoreCalculator.calculate_score(seo_result)

    # Display Extracted Metrics
    title_display = seo_result["title"] if seo_result["title"] else "[MISSING / NONE]"
    meta_display = seo_result["meta_description"] if seo_result["meta_description"] else "[MISSING / NONE]"

    print("EXTRACTED SEO METRICS:")
    print(f"  * Page Title            : {title_display}")
    print(f"    - Title Length        : {seo_result['title_length']} characters")
    print(f"  * Meta Description      : {meta_display}")
    print(f"    - Description Length  : {seo_result['meta_description_length']} characters")
    print(f"  * H1 Heading Count      : {seo_result['h1_count']}")
    print(f"  * Total Images Found    : {seo_result['total_images']}")
    print(f"  * Images Missing Alt    : {seo_result['missing_alt_images']}")
    print("-" * 75)

    # Display Detected Issues
    print("DETECTED SEO ISSUES:")
    if seo_result["issues"]:
        for idx, issue in enumerate(seo_result["issues"], 1):
            print(f"  {idx}. [ISSUE] {issue}")
    else:
        print("  None. Page meets all evaluated on-page SEO criteria!")
    print("-" * 75)

    # Display Score, Rating & Deductions
    print("HEALTH SCORE & RATING:")
    print(f"  * Overall SEO Score     : {score_result['score']} / 100")
    print(f"  * Health Rating         : {score_result['rating']}")

    if score_result["deductions"]:
        print("\n  Point Deductions Applied:")
        for idx, d in enumerate(score_result["deductions"], 1):
            print(f"    {idx}. {d['reason']} ({d['penalty']} pts)")
    else:
        print("  Point Deductions Applied: None (Full 100 points awarded)")

    print("=" * 75 + "\n")
    return seo_result, score_result


def main():
    """
    Main test runner for Phase 2 SEO Analyzer and Score Calculator.
    """
    print("\n" + "#" * 75)
    print("  WEBSITE BROKEN LINK & SEO HEALTH AUDIT TOOL")
    print("  PHASE 2: SEO ANALYZER & SCORE CALCULATOR TEST SUITE")
    print("#" * 75 + "\n")

    # Run Test 1: Good Page
    good_seo, good_score = run_seo_test(
        test_name="Test 1: Good SEO Page (Optimized)",
        url="https://example.com/optimized-page",
        html_content=GOOD_HTML_PAGE
    )

    # Run Test 2: Bad Page
    bad_seo, bad_score = run_seo_test(
        test_name="Test 2: Bad SEO Page (Unoptimized / Multiple Issues)",
        url="https://example.com/unoptimized-page",
        html_content=BAD_HTML_PAGE
    )

    # Verification Assertions
    print("-" * 75)
    print("VERIFICATION CHECKLIST:")
    test1_passed = (good_score["score"] >= 90 and len(good_seo["issues"]) == 0)
    test2_passed = (bad_score["score"] < 50 and len(bad_seo["issues"]) >= 4)

    print(f"  * Test 1 (Good Page) high score & zero issues : {'PASSED' if test1_passed else 'FAILED'} (Score: {good_score['score']})")
    print(f"  * Test 2 (Bad Page) penalty & issue detection : {'PASSED' if test2_passed else 'FAILED'} (Score: {bad_score['score']})")
    print("-" * 75)

    if test1_passed and test2_passed:
        print("\nALL PHASE 2 TESTS COMPLETED SUCCESSFULLY!\n")
    else:
        print("\nPHASE 2 TESTS FAILED SOME VERIFICATION CHECKS.\n")


if __name__ == "__main__":
    main()
