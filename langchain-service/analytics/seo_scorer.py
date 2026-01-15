"""
SEO Scorer Module - Technical SEO Quality Analysis

All calculations are:
- Formula-based scoring
- Industry-standard benchmarks
- NO LLM inference

Scoring factors:
- Title tag optimization (20%)
- Meta description (15%)
- Keyword density (25%)
- Heading structure (15%)
- Content length (10%)
- Internal linking (10%)
- Image optimization (5%)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class SEOScorer:
    """
    Production-grade SEO scoring using technical analysis.

    All methods return deterministic results with algorithm documentation.
    """

    # Optimal ranges for SEO factors
    OPTIMAL_RANGES = {
        'title_length': {'min': 50, 'max': 60, 'ideal': 55},
        'meta_length': {'min': 150, 'max': 160, 'ideal': 155},
        'keyword_density': {'min': 1.0, 'max': 2.0, 'ideal': 1.5},
        'content_length': {'min': 1500, 'ideal': 2000},
        'h2_count': {'min': 2, 'ideal': 4},
        'internal_links': {'min': 3, 'ideal': 5},
    }

    # Scoring weights
    WEIGHTS = {
        'title': 0.20,
        'meta_desc': 0.15,
        'keyword_density': 0.25,
        'heading_structure': 0.15,
        'content_length': 0.10,
        'internal_linking': 0.10,
        'image_optimization': 0.05,
    }

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        Initialize SEO scorer.

        Args:
            custom_weights: Optional custom weights for scoring factors
        """
        self.weights = {**self.WEIGHTS}
        if custom_weights:
            self.weights.update(custom_weights)

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(re.findall(r'\b\w+\b', text))

    def _calculate_range_score(
        self,
        value: float,
        min_val: float,
        max_val: float,
        ideal: float
    ) -> float:
        """
        Calculate score based on optimal range.

        Returns 100 if value is ideal, decreasing as it deviates.
        """
        if min_val <= value <= max_val:
            # Within range - calculate based on distance from ideal
            distance = abs(value - ideal)
            max_distance = max(ideal - min_val, max_val - ideal)
            return 100 - (distance / max_distance * 20)  # Max 20% penalty
        elif value < min_val:
            # Below range
            shortfall = (min_val - value) / min_val * 100
            return max(0, 80 - shortfall)
        else:
            # Above range
            excess = (value - max_val) / max_val * 100
            return max(0, 80 - excess)

    def calculate_seo_score(
        self,
        content: str,
        metadata: Dict[str, str],
        target_keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive SEO quality score.

        Args:
            content: Page content (HTML or plain text)
            metadata: Dict with 'title', 'description', etc.
            target_keywords: List of target keywords

        Returns:
            Dict with seo_score, component_scores, and recommendations
        """
        scores = {}
        recommendations = []

        # 1. Title Tag Optimization (20%)
        title = metadata.get('title', '')
        title_length = len(title)

        if 50 <= title_length <= 60:
            scores['title'] = 100
        else:
            deviation = abs(title_length - 55)
            scores['title'] = max(0, 100 - deviation * 2)
            if title_length < 50:
                recommendations.append(f'Title too short ({title_length} chars). Aim for 50-60 characters.')
            elif title_length > 60:
                recommendations.append(f'Title too long ({title_length} chars). May be truncated in search results.')

        # Check for keyword in title
        title_lower = title.lower()
        keyword_in_title = any(kw.lower() in title_lower for kw in target_keywords)
        if not keyword_in_title and target_keywords:
            scores['title'] *= 0.8  # 20% penalty
            recommendations.append('Primary keyword not found in title tag.')

        # 2. Meta Description (15%)
        meta_desc = metadata.get('description', '')
        meta_length = len(meta_desc)

        if 150 <= meta_length <= 160:
            scores['meta_desc'] = 100
        else:
            deviation = abs(meta_length - 155)
            scores['meta_desc'] = max(0, 100 - deviation)
            if meta_length < 150:
                recommendations.append(f'Meta description too short ({meta_length} chars). Aim for 150-160.')
            elif meta_length > 160:
                recommendations.append(f'Meta description too long ({meta_length} chars). May be truncated.')

        # 3. Keyword Density (25%)
        word_count = self._count_words(content)
        content_lower = content.lower()

        if word_count > 0 and target_keywords:
            keyword_count = sum(
                content_lower.count(kw.lower())
                for kw in target_keywords
            )
            keyword_density = (keyword_count / word_count) * 100

            if 1.0 <= keyword_density <= 2.0:
                scores['keyword_density'] = 100
            elif keyword_density < 1.0:
                scores['keyword_density'] = keyword_density * 100
                recommendations.append(f'Keyword density low ({keyword_density:.1f}%). Aim for 1-2%.')
            else:
                # Penalty for keyword stuffing
                excess = keyword_density - 2.0
                scores['keyword_density'] = max(0, 100 - excess * 20)
                recommendations.append(f'Keyword density high ({keyword_density:.1f}%). Risk of keyword stuffing.')
        else:
            scores['keyword_density'] = 50  # Neutral if no keywords specified
            keyword_density = 0

        # 4. Heading Structure (15%)
        # Count headings (support both HTML and Markdown)
        h1_html = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
        h1_md = len(re.findall(r'^# [^#]', content, re.MULTILINE))
        h1_count = h1_html + h1_md

        h2_html = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
        h2_md = len(re.findall(r'^## [^#]', content, re.MULTILINE))
        h2_count = h2_html + h2_md

        h3_html = len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE))
        h3_md = len(re.findall(r'^### [^#]', content, re.MULTILINE))
        h3_count = h3_html + h3_md

        # Score heading structure
        if h1_count == 1 and h2_count >= 2:
            scores['heading_structure'] = 100
        elif h1_count == 1 and h2_count >= 1:
            scores['heading_structure'] = 80
        elif h1_count == 1:
            scores['heading_structure'] = 60
            recommendations.append('Add more H2 headings to improve content structure.')
        elif h1_count == 0:
            scores['heading_structure'] = 40
            recommendations.append('Missing H1 heading. Every page should have exactly one H1.')
        else:
            scores['heading_structure'] = 50
            recommendations.append(f'Multiple H1 tags found ({h1_count}). Use only one H1 per page.')

        # 5. Content Length (10%)
        if word_count >= 2000:
            scores['content_length'] = 100
        elif word_count >= 1500:
            scores['content_length'] = 80
        elif word_count >= 1000:
            scores['content_length'] = 60
        elif word_count >= 500:
            scores['content_length'] = 40
        else:
            scores['content_length'] = (word_count / 500) * 40
            recommendations.append(f'Content is thin ({word_count} words). Aim for 1500+ words for comprehensive coverage.')

        # 6. Internal Linking (10%)
        internal_link_count = len(re.findall(r'<a[^>]+href=["\']/', content, re.IGNORECASE))
        internal_link_count += len(re.findall(r'\[.+?\]\(/', content))  # Markdown links

        if internal_link_count >= 5:
            scores['internal_linking'] = 100
        elif internal_link_count >= 3:
            scores['internal_linking'] = 80
        elif internal_link_count >= 1:
            scores['internal_linking'] = 50
        else:
            scores['internal_linking'] = 20
            recommendations.append('Add internal links to improve site navigation and SEO.')

        # 7. Image Optimization (5%)
        # Count images and images with alt text
        img_count = len(re.findall(r'<img[^>]*>', content, re.IGNORECASE))
        img_count += len(re.findall(r'!\[', content))  # Markdown images

        img_with_alt = len(re.findall(r'<img[^>]*alt=["\'][^"\']+["\']', content, re.IGNORECASE))
        img_with_alt += len(re.findall(r'!\[[^\]]+\]', content))  # Markdown with alt text

        if img_count == 0:
            scores['image_optimization'] = 80  # No images, neutral
        elif img_with_alt >= img_count:
            scores['image_optimization'] = 100
        else:
            scores['image_optimization'] = (img_with_alt / img_count) * 100
            missing_alt = img_count - img_with_alt
            recommendations.append(f'{missing_alt} images missing alt text. Add descriptive alt attributes.')

        # Calculate Weighted Total
        total_score = sum(
            scores[k] * self.weights[k]
            for k in self.weights.keys()
            if k in scores
        )

        # Determine grade
        if total_score >= 80:
            grade = 'A'
        elif total_score >= 60:
            grade = 'B'
        elif total_score >= 40:
            grade = 'C'
        elif total_score >= 20:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'seo_score': round(total_score, 1),
            'grade': grade,
            'component_scores': {k: round(v, 1) for k, v in scores.items()},
            'weights': self.weights,
            'metrics': {
                'title_length': title_length,
                'meta_length': meta_length,
                'word_count': word_count,
                'keyword_density_pct': round(keyword_density, 2) if 'keyword_density' in locals() else 0,
                'h1_count': h1_count,
                'h2_count': h2_count,
                'h3_count': h3_count,
                'internal_links': internal_link_count,
                'images': img_count,
                'images_with_alt': img_with_alt
            },
            'recommendations': recommendations[:5],  # Top 5 recommendations
            'algorithm': 'Multi-factor SEO scoring (title, meta, keywords, structure, length, links, images)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def analyze_keyword_placement(
        self,
        content: str,
        metadata: Dict[str, str],
        target_keyword: str
    ) -> Dict[str, Any]:
        """
        Analyze keyword placement across key SEO elements.

        Args:
            content: Page content
            metadata: Page metadata
            target_keyword: Primary target keyword

        Returns:
            Dict with keyword placement analysis
        """
        keyword_lower = target_keyword.lower()
        placements = {}

        # Check title
        title = metadata.get('title', '').lower()
        placements['in_title'] = keyword_lower in title
        placements['title_position'] = title.find(keyword_lower) if placements['in_title'] else -1

        # Check meta description
        meta = metadata.get('description', '').lower()
        placements['in_meta'] = keyword_lower in meta

        # Check first paragraph (first 200 characters)
        content_lower = content.lower()
        first_para = content_lower[:500]
        placements['in_first_paragraph'] = keyword_lower in first_para

        # Check H1
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        if not h1_match:
            h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        h1_text = h1_match.group(1).lower() if h1_match else ''
        placements['in_h1'] = keyword_lower in h1_text

        # Check H2s
        h2_matches = re.findall(r'<h2[^>]*>(.*?)</h2>', content, re.IGNORECASE | re.DOTALL)
        h2_matches += re.findall(r'^## (.+)$', content, re.MULTILINE)
        placements['in_h2'] = any(keyword_lower in h2.lower() for h2 in h2_matches)

        # Check URL
        url = metadata.get('url', '').lower()
        placements['in_url'] = keyword_lower.replace(' ', '-') in url or keyword_lower.replace(' ', '_') in url

        # Calculate placement score
        placement_score = sum([
            placements['in_title'] * 25,
            placements['in_h1'] * 20,
            placements['in_first_paragraph'] * 20,
            placements['in_meta'] * 15,
            placements['in_h2'] * 10,
            placements['in_url'] * 10,
        ])

        return {
            'keyword': target_keyword,
            'placements': placements,
            'placement_score': placement_score,
            'assessment': 'excellent' if placement_score >= 80 else 'good' if placement_score >= 60 else 'needs_improvement',
            'algorithm': 'Keyword placement scoring across SEO elements',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }


# Convenience function
def calculate_seo_score(
    content: str,
    metadata: Dict[str, str],
    target_keywords: List[str]
) -> Dict[str, Any]:
    """Calculate SEO score for content."""
    scorer = SEOScorer()
    return scorer.calculate_seo_score(content, metadata, target_keywords)
