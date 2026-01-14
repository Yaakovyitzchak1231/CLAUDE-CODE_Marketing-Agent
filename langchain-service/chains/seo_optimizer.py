"""
SEO Optimization Chain
Sequential chain for optimizing content for search engines
"""

from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate
from typing import Dict, Any, Optional, List
import structlog
import re

logger = structlog.get_logger()


class SEOOptimizerChain:
    """
    Sequential chain for SEO content optimization

    Optimizations:
    - Keyword density and placement
    - Meta descriptions
    - Title tag optimization
    - Heading structure (H1, H2, H3)
    - Internal/external linking
    - Readability improvements
    - Image alt text suggestions
    - URL slug optimization
    """

    def __init__(self, llm):
        """
        Initialize SEO Optimizer Chain

        Args:
            llm: Language model instance
        """
        self.llm = llm
        self.chain = self._build_chain()

        logger.info("seo_optimizer_chain_initialized")

    def _build_chain(self) -> SequentialChain:
        """Build sequential SEO optimization chain"""

        # Step 1: Keyword Analysis
        keyword_analysis_prompt = PromptTemplate(
            input_variables=["content", "target_keywords"],
            template="""Analyze this content for keyword optimization:

Content:
{content}

Target Keywords: {target_keywords}

Analyze:
1. Current keyword density for each target keyword
2. Keyword placement (title, headings, first paragraph, throughout)
3. Semantic keyword variations used
4. Keyword stuffing risk assessment
5. Missing keyword opportunities

Provide keyword analysis with recommendations.

KEYWORD ANALYSIS:"""
        )

        keyword_chain = LLMChain(
            llm=self.llm,
            prompt=keyword_analysis_prompt,
            output_key="keyword_analysis"
        )

        # Step 2: Heading Structure Optimization
        heading_optimization_prompt = PromptTemplate(
            input_variables=["content", "keyword_analysis"],
            template="""Optimize the heading structure for SEO:

Content:
{content}

Keyword Analysis:
{keyword_analysis}

Optimize:
1. Ensure single H1 with primary keyword
2. Create descriptive H2s with secondary keywords
3. Add H3s for subsections
4. Ensure hierarchical structure
5. Make headings descriptive and keyword-rich

Provide optimized heading structure.

OPTIMIZED HEADINGS:"""
        )

        heading_chain = LLMChain(
            llm=self.llm,
            prompt=heading_optimization_prompt,
            output_key="heading_structure"
        )

        # Step 3: Meta Data Optimization
        metadata_prompt = PromptTemplate(
            input_variables=["content", "target_keywords"],
            template="""Create SEO-optimized meta data:

Content:
{content}

Target Keywords: {target_keywords}

Create:
1. Title tag (50-60 characters, includes primary keyword)
2. Meta description (150-160 characters, compelling, includes keywords)
3. URL slug (short, descriptive, keyword-rich, lowercase, hyphens)
4. Focus keyphrase (primary target keyword)

Format:
Title: [Your title]
Meta Description: [Your description]
URL Slug: [your-slug]
Focus Keyphrase: [primary keyword]

META DATA:"""
        )

        metadata_chain = LLMChain(
            llm=self.llm,
            prompt=metadata_prompt,
            output_key="meta_data"
        )

        # Step 4: Content Enhancement
        content_enhancement_prompt = PromptTemplate(
            input_variables=["content", "keyword_analysis", "heading_structure"],
            template="""Enhance content for SEO while maintaining quality:

Original Content:
{content}

Keyword Analysis:
{keyword_analysis}

Heading Structure:
{heading_structure}

Enhancements:
1. Add target keywords naturally in first paragraph
2. Include semantic keyword variations
3. Improve readability (shorter sentences, active voice)
4. Add transition words for flow
5. Include relevant internal/external linking opportunities
6. Ensure keyword distribution throughout content
7. Add compelling call-to-action

Provide enhanced content with natural keyword integration.

ENHANCED CONTENT:"""
        )

        content_enhancement_chain = LLMChain(
            llm=self.llm,
            prompt=content_enhancement_prompt,
            output_key="enhanced_content"
        )

        # Step 5: Link Strategy
        link_strategy_prompt = PromptTemplate(
            input_variables=["enhanced_content", "target_keywords"],
            template="""Develop internal and external linking strategy:

Content:
{enhanced_content}

Target Keywords: {target_keywords}

Recommend:
1. Internal linking opportunities (3-5 relevant internal links)
   - Suggest anchor text
   - Suggest target page topics
2. External linking opportunities (2-3 authoritative sources)
   - Suggest anchor text
   - Suggest resource types (studies, tools, guides)
3. Link placement strategy (where in content)

Format:
Internal Links:
- [Anchor Text] → [Target Page Topic]

External Links:
- [Anchor Text] → [Resource Type]

LINK STRATEGY:"""
        )

        link_strategy_chain = LLMChain(
            llm=self.llm,
            prompt=link_strategy_prompt,
            output_key="link_strategy"
        )

        # Step 6: Image Optimization Recommendations
        image_optimization_prompt = PromptTemplate(
            input_variables=["enhanced_content", "target_keywords"],
            template="""Recommend image optimization for SEO:

Content:
{enhanced_content}

Target Keywords: {target_keywords}

Recommend:
1. Number and placement of images
2. Alt text for each image (descriptive, includes keywords)
3. File naming conventions (descriptive, keyword-rich)
4. Image context within content
5. Featured image suggestion

Format for each image:
Image [N]: [Description]
Alt Text: [descriptive alt text with keyword]
File Name: [suggested-file-name.jpg]
Placement: [where in content]

IMAGE RECOMMENDATIONS:"""
        )

        image_optimization_chain = LLMChain(
            llm=self.llm,
            prompt=image_optimization_prompt,
            output_key="image_recommendations"
        )

        # Step 7: Final SEO Score and Recommendations
        final_score_prompt = PromptTemplate(
            input_variables=[
                "keyword_analysis",
                "heading_structure",
                "meta_data",
                "enhanced_content",
                "link_strategy",
                "image_recommendations"
            ],
            template="""Provide final SEO assessment and score:

Keyword Analysis:
{keyword_analysis}

Heading Structure:
{heading_structure}

Meta Data:
{meta_data}

Enhanced Content:
{enhanced_content}

Link Strategy:
{link_strategy}

Image Recommendations:
{image_recommendations}

Assess:
1. Overall SEO Score (0-100)
   - Keyword optimization (0-20)
   - Content quality (0-20)
   - Technical SEO (0-20)
   - User experience (0-20)
   - Link strategy (0-20)

2. Strengths (what's well optimized)
3. Weaknesses (what needs improvement)
4. Priority actions (top 3 recommendations)
5. Competitive assessment (vs. typical ranking content)

Format:
SEO SCORE: [X/100]

Breakdown:
- Keyword Optimization: [X/20]
- Content Quality: [X/20]
- Technical SEO: [X/20]
- User Experience: [X/20]
- Link Strategy: [X/20]

Strengths:
- [Strength 1]
- [Strength 2]

Weaknesses:
- [Weakness 1]
- [Weakness 2]

Priority Actions:
1. [Action 1]
2. [Action 2]
3. [Action 3]

FINAL ASSESSMENT:"""
        )

        final_score_chain = LLMChain(
            llm=self.llm,
            prompt=final_score_prompt,
            output_key="seo_score"
        )

        # Build sequential chain
        sequential_chain = SequentialChain(
            chains=[
                keyword_chain,
                heading_chain,
                metadata_chain,
                content_enhancement_chain,
                link_strategy_chain,
                image_optimization_chain,
                final_score_chain
            ],
            input_variables=["content", "target_keywords"],
            output_variables=[
                "keyword_analysis",
                "heading_structure",
                "meta_data",
                "enhanced_content",
                "link_strategy",
                "image_recommendations",
                "seo_score"
            ],
            verbose=True
        )

        return sequential_chain

    def optimize(
        self,
        content: str,
        target_keywords: Optional[List[str]] = None,
        primary_keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize content for SEO

        Args:
            content: Content to optimize
            target_keywords: List of target keywords
            primary_keyword: Primary focus keyword

        Returns:
            Dict with all optimization results
        """
        # Prepare target keywords
        if target_keywords is None:
            target_keywords = []

        if primary_keyword:
            keywords_str = f"{primary_keyword} (primary), " + ", ".join(target_keywords)
        else:
            keywords_str = ", ".join(target_keywords) if target_keywords else "auto-detect from content"

        logger.info(
            "optimizing_content_for_seo",
            content_length=len(content),
            keyword_count=len(target_keywords)
        )

        try:
            # Run optimization chain
            result = self.chain({
                "content": content,
                "target_keywords": keywords_str
            })

            # Add technical metrics
            technical_metrics = self._calculate_technical_metrics(content)

            result["technical_metrics"] = technical_metrics

            logger.info(
                "seo_optimization_complete",
                score=self._extract_score(result.get("seo_score", ""))
            )

            return result

        except Exception as e:
            logger.error("seo_optimization_error", error=str(e))
            return {
                "error": str(e),
                "enhanced_content": content  # Return original on error
            }

    def _calculate_technical_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate technical SEO metrics"""

        # Word count
        word_count = len(content.split())

        # Reading time (average 200 words per minute)
        reading_time = round(word_count / 200, 1)

        # Sentence count
        sentences = re.split(r'[.!?]+', content)
        sentence_count = len([s for s in sentences if s.strip()])

        # Average sentence length
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

        # Paragraph count
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)

        # Heading counts
        h1_count = len(re.findall(r'^#\s', content, re.MULTILINE))
        h2_count = len(re.findall(r'^##\s', content, re.MULTILINE))
        h3_count = len(re.findall(r'^###\s', content, re.MULTILINE))

        # Link counts
        internal_links = len(re.findall(r'\[.*?\]\((?!http)', content))
        external_links = len(re.findall(r'\[.*?\]\(http', content))

        # List counts
        bullet_lists = len(re.findall(r'^\s*[-*+]\s', content, re.MULTILINE))
        numbered_lists = len(re.findall(r'^\s*\d+\.\s', content, re.MULTILINE))

        return {
            "word_count": word_count,
            "reading_time_minutes": reading_time,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "paragraph_count": paragraph_count,
            "headings": {
                "h1": h1_count,
                "h2": h2_count,
                "h3": h3_count,
                "total": h1_count + h2_count + h3_count
            },
            "links": {
                "internal": internal_links,
                "external": external_links,
                "total": internal_links + external_links
            },
            "lists": {
                "bullet": bullet_lists,
                "numbered": numbered_lists,
                "total": bullet_lists + numbered_lists
            }
        }

    def _extract_score(self, seo_score_text: str) -> int:
        """Extract numeric score from SEO assessment"""
        match = re.search(r'SEO SCORE:\s*(\d+)', seo_score_text)
        if match:
            return int(match.group(1))
        return 0

    def quick_optimize(
        self,
        content: str,
        target_keyword: str
    ) -> Dict[str, Any]:
        """
        Quick SEO optimization (single keyword focus)

        Args:
            content: Content to optimize
            target_keyword: Primary keyword to optimize for

        Returns:
            Dict with optimization results
        """
        return self.optimize(
            content=content,
            primary_keyword=target_keyword,
            target_keywords=[]
        )


def create_seo_optimizer(llm) -> SEOOptimizerChain:
    """
    Factory function to create SEO Optimizer Chain

    Args:
        llm: Language model instance

    Returns:
        SEOOptimizerChain instance
    """
    return SEOOptimizerChain(llm)


# Example usage
if __name__ == "__main__":
    from langchain_community.llms import Ollama

    # Initialize LLM
    llm = Ollama(model="llama3", base_url="http://localhost:11434")

    # Create optimizer
    optimizer = create_seo_optimizer(llm)

    # Sample content
    sample_content = """
    # Marketing Automation Benefits

    Marketing automation helps businesses save time and improve efficiency.
    It allows teams to focus on strategy while repetitive tasks are automated.

    ## Key Benefits

    Automation tools can handle email campaigns, social media posting, and lead nurturing.
    This frees up marketing teams to work on creative campaigns and strategic planning.

    ## Getting Started

    To implement marketing automation, first identify your repetitive tasks.
    Then choose a platform that fits your needs and budget.
    Finally, set up workflows and monitor performance.
    """

    # Optimize for SEO
    result = optimizer.optimize(
        content=sample_content,
        primary_keyword="marketing automation",
        target_keywords=["email automation", "lead nurturing", "marketing tools"]
    )

    print("\n=== SEO OPTIMIZATION RESULTS ===\n")
    print(f"Enhanced Content:\n{result['enhanced_content']}\n")
    print(f"Meta Data:\n{result['meta_data']}\n")
    print(f"SEO Score:\n{result['seo_score']}\n")
    print(f"Technical Metrics:\n{result['technical_metrics']}")
