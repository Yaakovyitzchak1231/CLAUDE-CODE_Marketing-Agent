"""
CrewAI Integration Module

Provides alternative orchestration using CrewAI's role-based multi-agent framework.

Features:
- Content generation crews
- Campaign management crews
- Research crews
- Integration with existing agents

Usage:
    from crewai_integration import CrewAIOrchestrator, get_orchestrator

    # Get orchestrator (creates crews on demand)
    orchestrator = get_orchestrator()

    # Run a content generation task
    result = orchestrator.generate_content(
        content_type="linkedin_post",
        topic="AI in marketing",
        target_audience="marketing executives"
    )

    # Run a full campaign
    result = orchestrator.run_campaign(
        campaign_brief="Q1 product launch",
        target_audience="enterprise CTOs"
    )
"""

from .orchestrator import CrewAIOrchestrator, get_orchestrator

__all__ = [
    'CrewAIOrchestrator',
    'get_orchestrator'
]
