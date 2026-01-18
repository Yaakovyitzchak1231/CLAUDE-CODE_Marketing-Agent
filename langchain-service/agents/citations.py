"""
Citation Tracking and Validation System

Ensures all factual claims from agents are backed by verifiable sources.
"""

import re
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict

logger = structlog.get_logger()


@dataclass
class Citation:
    """Represents a single citation for a factual claim"""
    claim: str
    source_url: str
    source_title: Optional[str] = None
    accessed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CitationTracker:
    """
    Tracks and validates citations for agent outputs.

    Ensures that all factual claims have verifiable sources.
    """

    # Patterns to identify factual claims that need citations
    FACTUAL_CLAIM_PATTERNS = [
        r'\d+%',  # Percentages
        r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|trillion|M|B|K))?',  # Dollar amounts
        r'(?:market size|revenue|growth rate|market share)\s*(?:is|was|of|at)\s*[\d$%]',  # Market metrics
        r'(?:according to|based on|research shows|studies indicate|data suggests)',  # Attribution phrases
        r'(?:in (?:20\d{2}|\d{4}))',  # Year references
        r'(?:\d+(?:\.\d+)?\s*(?:million|billion|trillion))',  # Large numbers
        r'(?:ranked|leading|top|largest|fastest)',  # Ranking claims
    ]

    def __init__(self):
        self.citations: List[Citation] = []
        self.uncited_claims: List[str] = []

    def add_citation(
        self,
        claim: str,
        source_url: str,
        source_title: Optional[str] = None,
        confidence: float = 1.0
    ) -> Citation:
        """Add a citation for a factual claim"""
        citation = Citation(
            claim=claim,
            source_url=source_url,
            source_title=source_title,
            confidence=confidence
        )
        self.citations.append(citation)
        logger.info("citation_added", claim=claim[:50], source=source_url)
        return citation

    def extract_citations_from_response(self, response_text: str) -> List[Citation]:
        """
        Extract citations from a response that includes inline citations.

        Looks for patterns like:
        - [Source: URL]
        - (Source: URL)
        - Citation: URL
        """
        citations = []

        # Pattern for inline citations [Source: title - URL] or (Source: URL)
        citation_patterns = [
            r'\[(?:Source|Citation|Ref):\s*([^\]]+?)\s*-\s*(https?://[^\]\s]+)\]',
            r'\((?:Source|Citation|Ref):\s*(https?://[^\)\s]+)\)',
            r'(?:Source|Citation|Ref):\s*(https?://\S+)',
            r'\[(https?://[^\]\s]+)\]',
        ]

        for pattern in citation_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:
                        title, url = match
                        citation = Citation(
                            claim="Extracted from response",
                            source_url=url,
                            source_title=title
                        )
                    else:
                        citation = Citation(
                            claim="Extracted from response",
                            source_url=match[0]
                        )
                else:
                    citation = Citation(
                        claim="Extracted from response",
                        source_url=match
                    )
                citations.append(citation)

        self.citations.extend(citations)
        return citations

    def validate_response(self, response_text: str) -> Dict[str, Any]:
        """
        Validate that a response has proper citations for factual claims.

        Returns validation result with warnings for uncited claims.
        """
        # Find factual claims in response
        factual_claims = self._find_factual_claims(response_text)

        # Extract any citations present
        found_citations = self.extract_citations_from_response(response_text)

        # Check if response has a sources section
        has_sources_section = bool(re.search(
            r'(?:sources?|references?|citations?):\s*\n',
            response_text,
            re.IGNORECASE
        ))

        # Identify uncited claims (claims without nearby citations)
        uncited = self._find_uncited_claims(response_text, factual_claims)
        self.uncited_claims.extend(uncited)

        is_valid = len(found_citations) > 0 or has_sources_section

        validation_result = {
            "is_valid": is_valid,
            "total_factual_claims": len(factual_claims),
            "cited_count": len(found_citations),
            "uncited_claims": uncited[:5],  # Limit to first 5
            "has_sources_section": has_sources_section,
            "warnings": []
        }

        if not is_valid:
            validation_result["warnings"].append(
                "Response contains factual claims without citations"
            )

        if len(uncited) > 3:
            validation_result["warnings"].append(
                f"Found {len(uncited)} uncited factual claims"
            )

        logger.info(
            "response_validated",
            is_valid=is_valid,
            citations_found=len(found_citations),
            uncited_claims=len(uncited)
        )

        return validation_result

    def _find_factual_claims(self, text: str) -> List[str]:
        """Find potential factual claims in text"""
        claims = []

        for pattern in self.FACTUAL_CLAIM_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            # Get surrounding context for each match
            for match in matches:
                # Find the sentence containing the match
                sentence_pattern = r'[^.!?]*' + re.escape(match) + r'[^.!?]*[.!?]'
                sentences = re.findall(sentence_pattern, text, re.IGNORECASE)
                claims.extend(sentences[:1] if sentences else [match])

        return list(set(claims))  # Remove duplicates

    def _find_uncited_claims(
        self,
        text: str,
        claims: List[str]
    ) -> List[str]:
        """Find claims that don't have nearby citations"""
        uncited = []

        # Check each claim for nearby citation markers
        citation_markers = ['http', 'source:', 'ref:', 'citation:', '[', '(source']

        for claim in claims:
            claim_pos = text.lower().find(claim.lower()[:20])
            if claim_pos == -1:
                continue

            # Check for citations within 200 chars before or after
            context_start = max(0, claim_pos - 200)
            context_end = min(len(text), claim_pos + len(claim) + 200)
            context = text[context_start:context_end].lower()

            has_citation = any(marker in context for marker in citation_markers)
            if not has_citation:
                uncited.append(claim[:100] + "..." if len(claim) > 100 else claim)

        return uncited

    def get_citations(self) -> List[Dict[str, Any]]:
        """Get all tracked citations as dicts"""
        return [c.to_dict() for c in self.citations]

    def clear(self):
        """Clear all tracked citations"""
        self.citations = []
        self.uncited_claims = []


# Citation requirement prompt additions for agents
CITATION_REQUIREMENTS_PROMPT = """
CITATION REQUIREMENTS (MANDATORY):
- ALL factual claims MUST include a source citation
- Use the format: [Source: Title - URL] for inline citations
- Include a "Sources:" section at the end of your response
- Acceptable sources: Government sites (.gov), academic (.edu), major publications, official company sites
- Do NOT make claims without verifiable sources
- If you cannot find a source for a claim, explicitly state "Unverified: " before the claim

Example citation format:
"The global AI market is expected to reach $190 billion by 2025 [Source: Grand View Research - https://grandviewresearch.com/industry-analysis/ai-market]"

Sources section example:
Sources:
1. Grand View Research - AI Market Report: https://grandviewresearch.com/industry-analysis/ai-market
2. Gartner - Technology Trends: https://gartner.com/technology-trends
"""


def enhance_prompt_with_citations(original_prompt: str) -> str:
    """Add citation requirements to an agent prompt"""
    return f"{original_prompt}\n\n{CITATION_REQUIREMENTS_PROMPT}"


def wrap_response_with_citations(
    response: Dict[str, Any],
    tracker: CitationTracker
) -> Dict[str, Any]:
    """
    Wrap an agent response with citation metadata.

    Validates citations and adds tracking information.
    """
    output_text = response.get("output", "")

    # Validate and extract citations
    validation = tracker.validate_response(output_text)

    # Add citation metadata to response
    enhanced_response = {
        **response,
        "citations": tracker.get_citations(),
        "citation_validation": validation,
        "is_verified": validation["is_valid"] and len(validation["uncited_claims"]) == 0
    }

    return enhanced_response
