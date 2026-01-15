"""
Commercial Intelligence Tool - Data sources for non-regulated B2B industries

Targets industries like:
- Credit card processing / Merchant services
- ERTC/ERC claim buyouts
- Equipment leasing
- Factoring
- Payment processing

Uses FREE sources:
- Industry publications (PYMNTS, PaymentsJournal, The Green Sheet)
- IRS news releases
- Press releases (PR Newswire, BusinessWire)
- Job market indicators
- BBB/Review aggregators
"""

import requests
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from functools import lru_cache

logger = logging.getLogger(__name__)


class CommercialIntelTool:
    """Commercial intelligence for non-regulated B2B industries"""

    # Industry-specific publication sources
    INDUSTRY_SOURCES = {
        'payments': {
            'publications': [
                'pymnts.com',
                'paymentsjournal.com',
                'thegreensheet.com',
                'nilsonreport.com',
                'paymentssource.com'
            ],
            'keywords': ['merchant services', 'payment processing', 'credit card processing',
                        'POS system', 'interchange', 'acquiring']
        },
        'ertc': {
            'publications': [
                'irs.gov',
                'prnewswire.com',
                'businesswire.com',
                'journalofaccountancy.com'
            ],
            'keywords': ['ERTC', 'ERC', 'employee retention credit', 'IRS backlog',
                        'tax credit', 'payroll tax']
        },
        'factoring': {
            'publications': [
                'abfjournal.com',
                'sfnet.com',
                'businesswire.com'
            ],
            'keywords': ['invoice factoring', 'accounts receivable', 'asset-based lending',
                        'working capital']
        },
        'equipment_leasing': {
            'publications': [
                'elfaonline.org',
                'monitordaily.com',
                'leasingnews.org'
            ],
            'keywords': ['equipment leasing', 'equipment finance', 'lease financing']
        }
    }

    # Source credibility tiers
    SOURCE_CREDIBILITY = {
        'tier1': {  # Highest credibility
            'domains': ['irs.gov', 'sec.gov', 'bls.gov', 'census.gov', 'fda.gov'],
            'confidence': 'high'
        },
        'tier2': {  # High credibility - major business news
            'domains': ['reuters.com', 'bloomberg.com', 'wsj.com', 'ft.com'],
            'confidence': 'high'
        },
        'tier3': {  # Medium credibility - industry publications
            'domains': ['pymnts.com', 'paymentsjournal.com', 'businesswire.com', 'prnewswire.com'],
            'confidence': 'medium'
        },
        'tier4': {  # Lower credibility - general news/blogs
            'domains': ['default'],
            'confidence': 'low'
        }
    }

    def __init__(self, searxng_url: Optional[str] = None):
        """
        Initialize commercial intelligence tool.

        Args:
            searxng_url: URL for SearXNG instance (optional, falls back to DuckDuckGo)
        """
        self.searxng_url = searxng_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _get_source_credibility(self, url: str) -> Dict[str, str]:
        """Determine credibility tier of a source URL."""
        url_lower = url.lower()

        for tier, data in self.SOURCE_CREDIBILITY.items():
            for domain in data['domains']:
                if domain in url_lower:
                    return {'tier': tier, 'confidence': data['confidence']}

        return {'tier': 'tier4', 'confidence': 'low'}

    def _search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search using DuckDuckGo HTML (no API key needed).

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of search results with url, title, snippet
        """
        try:
            url = "https://html.duckduckgo.com/html/"
            response = self.session.post(url, data={'q': query}, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            for result in soup.select('.result')[:max_results]:
                title_elem = result.select_one('.result__title')
                snippet_elem = result.select_one('.result__snippet')
                link_elem = result.select_one('.result__url')

                if title_elem and link_elem:
                    # Extract actual URL from DuckDuckGo redirect
                    href = title_elem.find('a')
                    if href and href.get('href'):
                        actual_url = href.get('href')
                        # DuckDuckGo uses redirect URLs, extract actual
                        if 'uddg=' in actual_url:
                            import urllib.parse
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(actual_url).query)
                            actual_url = parsed.get('uddg', [actual_url])[0]

                        results.append({
                            'title': title_elem.get_text(strip=True),
                            'url': actual_url,
                            'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                            'credibility': self._get_source_credibility(actual_url)
                        })

            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    def search_industry_news(self, industry: str, topic: Optional[str] = None,
                            days_back: int = 30) -> Dict[str, Any]:
        """
        Search industry-specific news from authoritative sources.

        Args:
            industry: Industry category ('payments', 'ertc', 'factoring', 'equipment_leasing')
            topic: Specific topic to search
            days_back: How far back to search (for date filtering in query)

        Returns:
            Dict with categorized news by credibility tier
        """
        industry_lower = industry.lower().replace(' ', '_')

        if industry_lower not in self.INDUSTRY_SOURCES:
            return {
                'error': f"Industry '{industry}' not configured",
                'available_industries': list(self.INDUSTRY_SOURCES.keys()),
                'confidence': 'none'
            }

        industry_config = self.INDUSTRY_SOURCES[industry_lower]

        # Build search query with site restrictions for authoritative sources
        site_queries = ' OR '.join([f'site:{pub}' for pub in industry_config['publications']])
        keywords = topic if topic else ' '.join(industry_config['keywords'][:3])

        query = f"{keywords} ({site_queries})"

        # Search
        results = self._search_duckduckgo(query, max_results=20)

        # Categorize by credibility
        categorized = {
            'tier1_authoritative': [],
            'tier2_business_news': [],
            'tier3_industry_pubs': [],
            'tier4_general': []
        }

        for result in results:
            tier = result['credibility']['tier']
            if tier == 'tier1':
                categorized['tier1_authoritative'].append(result)
            elif tier == 'tier2':
                categorized['tier2_business_news'].append(result)
            elif tier == 'tier3':
                categorized['tier3_industry_pubs'].append(result)
            else:
                categorized['tier4_general'].append(result)

        # Calculate overall confidence
        high_quality_count = len(categorized['tier1_authoritative']) + len(categorized['tier2_business_news'])
        medium_quality_count = len(categorized['tier3_industry_pubs'])

        if high_quality_count >= 3:
            confidence = 'high'
        elif high_quality_count >= 1 or medium_quality_count >= 3:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'industry': industry,
            'topic': topic,
            'query_used': query,
            'results': categorized,
            'total_results': len(results),
            'high_quality_results': high_quality_count,
            'confidence': confidence,
            'data_source': 'Industry Publications + Business News',
            'is_verified': high_quality_count > 0,
            'retrieved_at': datetime.now().isoformat()
        }

    def get_irs_ertc_status(self) -> Dict[str, Any]:
        """
        Get latest IRS news on ERTC/ERC backlog and processing status.

        Returns:
            Dict with IRS announcements and status updates
        """
        query = "ERTC OR ERC employee retention credit site:irs.gov"
        results = self._search_duckduckgo(query, max_results=10)

        irs_results = [r for r in results if 'irs.gov' in r['url'].lower()]

        return {
            'topic': 'ERTC/ERC IRS Status',
            'irs_announcements': irs_results,
            'irs_main_page': 'https://www.irs.gov/coronavirus/employee-retention-credit',
            'data_source': 'IRS.gov',
            'confidence': 'high' if irs_results else 'medium',
            'is_verified': True,
            'note': 'Check IRS main page for most current moratorium status',
            'retrieved_at': datetime.now().isoformat()
        }

    def get_competitor_activity(self, industry: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get competitor activity from press releases and news.

        Args:
            industry: Industry category
            company_name: Specific competitor to track (optional)

        Returns:
            Dict with competitor news and activity
        """
        if company_name:
            query = f'"{company_name}" (site:prnewswire.com OR site:businesswire.com OR site:globenewswire.com)'
        else:
            industry_lower = industry.lower().replace(' ', '_')
            if industry_lower in self.INDUSTRY_SOURCES:
                keywords = self.INDUSTRY_SOURCES[industry_lower]['keywords']
                query = f'{keywords[0]} funding OR acquisition OR launch (site:prnewswire.com OR site:businesswire.com)'
            else:
                query = f'{industry} funding OR acquisition (site:prnewswire.com OR site:businesswire.com)'

        results = self._search_duckduckgo(query, max_results=15)

        # Extract key events
        events = []
        for result in results:
            event_type = 'unknown'
            title_lower = result['title'].lower()

            if 'funding' in title_lower or 'raises' in title_lower or 'investment' in title_lower:
                event_type = 'funding'
            elif 'acquisition' in title_lower or 'acquires' in title_lower or 'merger' in title_lower:
                event_type = 'acquisition'
            elif 'launch' in title_lower or 'announces' in title_lower or 'introduces' in title_lower:
                event_type = 'product_launch'
            elif 'partnership' in title_lower or 'partners' in title_lower:
                event_type = 'partnership'

            events.append({
                'title': result['title'],
                'url': result['url'],
                'event_type': event_type,
                'snippet': result['snippet']
            })

        return {
            'industry': industry,
            'company': company_name,
            'competitor_events': events,
            'event_types_found': list(set([e['event_type'] for e in events])),
            'data_source': 'Press Releases (PR Newswire, BusinessWire)',
            'confidence': 'medium',
            'is_verified': True,
            'retrieved_at': datetime.now().isoformat()
        }

    def get_job_market_indicator(self, industry: str, role: Optional[str] = None) -> Dict[str, Any]:
        """
        Get job market data as industry health indicator.

        Args:
            industry: Industry to search jobs for
            role: Specific role (e.g., 'sales', 'engineer')

        Returns:
            Dict with job market indicators
        """
        search_terms = [industry]
        if role:
            search_terms.append(role)

        query = f'{" ".join(search_terms)} jobs (site:indeed.com OR site:linkedin.com/jobs)'
        results = self._search_duckduckgo(query, max_results=20)

        # Analyze job postings
        job_indicators = {
            'total_postings_found': len(results),
            'sample_postings': results[:5],
            'market_signal': 'growing' if len(results) >= 10 else 'stable' if len(results) >= 5 else 'contracting'
        }

        return {
            'industry': industry,
            'role_filter': role,
            'job_market_data': job_indicators,
            'interpretation': f"{'Strong' if len(results) >= 10 else 'Moderate' if len(results) >= 5 else 'Weak'} hiring activity indicates {'healthy' if len(results) >= 10 else 'stable' if len(results) >= 5 else 'challenging'} market conditions",
            'data_source': 'Job Boards (Indeed, LinkedIn)',
            'confidence': 'medium',
            'is_verified': True,
            'note': 'Job postings are a leading indicator of industry health',
            'retrieved_at': datetime.now().isoformat()
        }

    def research_commercial_industry(self, industry: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive research for commercial/non-regulated industries.

        Args:
            industry: Industry name
            topic: Specific topic

        Returns:
            Combined research from multiple commercial intelligence sources
        """
        results = {
            'industry': industry,
            'topic': topic,
            'sources': [],
            'data': {},
            'confidence': 'medium',
            'is_verified': True
        }

        # Industry news
        news = self.search_industry_news(industry, topic)
        if 'error' not in news:
            results['data']['industry_news'] = news
            results['sources'].append('Industry Publications')

        # Competitor activity
        competitors = self.get_competitor_activity(industry)
        results['data']['competitor_activity'] = competitors
        results['sources'].append('Press Releases')

        # Job market
        jobs = self.get_job_market_indicator(industry)
        results['data']['job_market'] = jobs
        results['sources'].append('Job Market Data')

        # ERTC-specific
        if 'ertc' in industry.lower() or 'erc' in industry.lower():
            irs_status = self.get_irs_ertc_status()
            results['data']['irs_status'] = irs_status
            results['sources'].append('IRS.gov')
            results['confidence'] = 'high'  # Authoritative source

        # Calculate confidence based on source quality
        high_quality = sum(1 for s in results['sources'] if s in ['IRS.gov', 'Industry Publications'])
        if high_quality >= 2:
            results['confidence'] = 'high'
        elif high_quality >= 1:
            results['confidence'] = 'medium'

        results['retrieved_at'] = datetime.now().isoformat()
        return results


# Singleton instance
commercial_intel = CommercialIntelTool()


def search_commercial_news(industry: str, topic: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for commercial industry news search."""
    return commercial_intel.search_industry_news(industry, topic)


def research_commercial_market(industry: str, topic: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for comprehensive commercial research."""
    return commercial_intel.research_commercial_industry(industry, topic)
