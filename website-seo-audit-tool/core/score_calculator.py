"""
score_calculator.py - SEO Health Score Calculator (Phase 2)
-----------------------------------------------------------
College Semester Project: Website Broken Link & SEO Health Audit Tool

Calculates a 0–100 On-Page SEO Health Score based on standard audit rules:
- Starting Score: 100 points
- Deductions:
    - Missing title:                 -20 points
    - Title too short (<30 chars):    -5 points
    - Title too long (>60 chars):     -5 points
    - Missing meta description:      -15 points
    - Meta description short (<70):   -5 points
    - Meta description long (>160):   -5 points
    - Missing H1 heading (0 count):  -15 points
    - Multiple H1 headings (>1):      -5 points
    - Missing alt text per image:     -3 points each

Rating Scale:
    - 90–100 : Excellent
    - 75–89  : Good
    - 60–74  : Needs Improvement
    - 40–59  : Poor
    - 0–39   : Critical
"""


class ScoreCalculator:
    """
    Computes an overall SEO health score (0-100) and qualitative rating
    from the structured results of SEOAnalyzer.
    """

    # Scoring constants
    DEDUCTION_MISSING_TITLE = 20
    DEDUCTION_TITLE_TOO_SHORT = 5
    DEDUCTION_TITLE_TOO_LONG = 5

    DEDUCTION_MISSING_META_DESC = 15
    DEDUCTION_META_DESC_TOO_SHORT = 5
    DEDUCTION_META_DESC_TOO_LONG = 5

    DEDUCTION_MISSING_H1 = 15
    DEDUCTION_MULTIPLE_H1 = 5

    DEDUCTION_PER_MISSING_ALT = 3

    @classmethod
    def calculate_score(cls, seo_data):
        """
        Calculate the SEO health score given the output dictionary from SEOAnalyzer.

        :param seo_data: dict with keys: 'title', 'title_length', 'meta_description',
                         'meta_description_length', 'h1_count', 'total_images',
                         'missing_alt_images', 'issues'
        :return: dict with 'score' (int 0-100), 'rating' (str), and 'deductions' (list of dicts)
        """
        if not isinstance(seo_data, dict):
            return {
                "score": 0,
                "rating": "Critical",
                "deductions": [{"reason": "Invalid or missing SEO analysis data", "penalty": -100}]
            }

        score = 100
        deductions = []

        title = seo_data.get("title", "")
        title_length = seo_data.get("title_length", len(title))

        meta_desc = seo_data.get("meta_description", "")
        meta_desc_length = seo_data.get("meta_description_length", len(meta_desc))

        h1_count = seo_data.get("h1_count", 0)
        missing_alt = seo_data.get("missing_alt_images", 0)

        # -------------------------------------------------------------
        # 1. Title Evaluation
        # -------------------------------------------------------------
        if not title:
            score -= cls.DEDUCTION_MISSING_TITLE
            deductions.append({
                "reason": "Missing page title",
                "penalty": -cls.DEDUCTION_MISSING_TITLE
            })
        elif title_length < 30:
            score -= cls.DEDUCTION_TITLE_TOO_SHORT
            deductions.append({
                "reason": f"Page title is too short ({title_length} chars, min recommended 30)",
                "penalty": -cls.DEDUCTION_TITLE_TOO_SHORT
            })
        elif title_length > 60:
            score -= cls.DEDUCTION_TITLE_TOO_LONG
            deductions.append({
                "reason": f"Page title is too long ({title_length} chars, max recommended 60)",
                "penalty": -cls.DEDUCTION_TITLE_TOO_LONG
            })

        # -------------------------------------------------------------
        # 2. Meta Description Evaluation
        # -------------------------------------------------------------
        if not meta_desc:
            score -= cls.DEDUCTION_MISSING_META_DESC
            deductions.append({
                "reason": "Missing meta description",
                "penalty": -cls.DEDUCTION_MISSING_META_DESC
            })
        elif meta_desc_length < 70:
            score -= cls.DEDUCTION_META_DESC_TOO_SHORT
            deductions.append({
                "reason": f"Meta description is too short ({meta_desc_length} chars, min recommended 70)",
                "penalty": -cls.DEDUCTION_META_DESC_TOO_SHORT
            })
        elif meta_desc_length > 160:
            score -= cls.DEDUCTION_META_DESC_TOO_LONG
            deductions.append({
                "reason": f"Meta description is too long ({meta_desc_length} chars, max recommended 160)",
                "penalty": -cls.DEDUCTION_META_DESC_TOO_LONG
            })

        # -------------------------------------------------------------
        # 3. H1 Heading Evaluation
        # -------------------------------------------------------------
        if h1_count == 0:
            score -= cls.DEDUCTION_MISSING_H1
            deductions.append({
                "reason": "Missing H1 heading",
                "penalty": -cls.DEDUCTION_MISSING_H1
            })
        elif h1_count > 1:
            score -= cls.DEDUCTION_MULTIPLE_H1
            deductions.append({
                "reason": f"Multiple H1 headings found ({h1_count} found, recommended exactly 1)",
                "penalty": -cls.DEDUCTION_MULTIPLE_H1
            })

        # -------------------------------------------------------------
        # 4. Image Alt Attribute Evaluation
        # -------------------------------------------------------------
        if missing_alt > 0:
            alt_penalty = missing_alt * cls.DEDUCTION_PER_MISSING_ALT
            score -= alt_penalty
            deductions.append({
                "reason": f"{missing_alt} image(s) missing alt text (-{cls.DEDUCTION_PER_MISSING_ALT} per image)",
                "penalty": -alt_penalty
            })

        # -------------------------------------------------------------
        # 5. Score Boundary Clamping (0–100)
        # -------------------------------------------------------------
        final_score = max(0, min(100, score))

        # -------------------------------------------------------------
        # 6. Qualitative Rating
        # -------------------------------------------------------------
        if final_score >= 90:
            rating = "Excellent"
        elif final_score >= 75:
            rating = "Good"
        elif final_score >= 60:
            rating = "Needs Improvement"
        elif final_score >= 40:
            rating = "Poor"
        else:
            rating = "Critical"

        return {
            "score": final_score,
            "rating": rating,
            "deductions": deductions
        }


def calculate_seo_score(seo_data):
    """
    Convenience function to compute SEO health score from analyzer results.
    """
    return ScoreCalculator.calculate_score(seo_data)
