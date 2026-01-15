"""
Supervisor Agent
Orchestrates all specialist agents using LangGraph

ENHANCED with deterministic routing:
- Rule-based agent selection (NO LLM hallucination in routing)
- Industry-aware workflow sequencing
- Configurable routing matrix
- Transparent decision logic with algorithm attribution
"""

from typing import Dict, List, Any, Annotated, TypedDict, Sequence, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import structlog
from datetime import datetime
import operator
import re

from config import settings


logger = structlog.get_logger()


# =============================================================================
# DETERMINISTIC ROUTING MATRIX - NO LLM HALLUCINATION
# =============================================================================
# Task type -> Industry type -> Agent sequence
# Agents are executed in order; workflow finishes when sequence is complete

ROUTING_MATRIX = {
    # Research tasks
    "research": {
        "regulated": ["research_agent", "trend_agent"],  # BLS/Census data focus
        "commercial": ["research_agent", "trend_agent"],  # Commercial intel focus
        "unknown": ["research_agent", "trend_agent"]
    },
    # Trend analysis tasks
    "trend_analysis": {
        "regulated": ["trend_agent", "research_agent"],
        "commercial": ["trend_agent", "research_agent"],
        "unknown": ["trend_agent"]
    },
    # Content generation tasks
    "content_generation": {
        "regulated": ["research_agent", "trend_agent", "content_agent"],
        "commercial": ["research_agent", "trend_agent", "content_agent"],
        "unknown": ["research_agent", "content_agent"]
    },
    # Full campaign (content + media)
    "full_campaign": {
        "regulated": ["research_agent", "trend_agent", "content_agent", "image_agent", "review_coordinator"],
        "commercial": ["research_agent", "trend_agent", "content_agent", "image_agent", "review_coordinator"],
        "unknown": ["research_agent", "content_agent", "image_agent", "review_coordinator"]
    },
    # Market analysis tasks
    "market_analysis": {
        "regulated": ["research_agent", "market_agent"],
        "commercial": ["research_agent", "market_agent"],
        "unknown": ["market_agent"]
    },
    # Competitor analysis
    "competitor_analysis": {
        "regulated": ["research_agent", "trend_agent"],
        "commercial": ["research_agent", "trend_agent"],
        "unknown": ["research_agent"]
    },
    # Content review workflow
    "content_review": {
        "any": ["review_coordinator"]
    },
    # Publishing workflow
    "publishing": {
        "any": ["publishing_agent"]
    }
}

# Industry classification keywords
REGULATED_INDUSTRIES = {
    "healthcare", "pharma", "pharmaceutical", "medical", "hospital", "clinic",
    "financial", "banking", "insurance", "fintech", "investment",
    "government", "federal", "defense", "military",
    "energy", "utilities", "nuclear",
    "education", "university", "school"
}

COMMERCIAL_INDUSTRIES = {
    "saas", "software", "technology", "tech", "startup",
    "retail", "ecommerce", "e-commerce", "consumer",
    "manufacturing", "industrial",
    "professional services", "consulting", "agency",
    "media", "entertainment", "marketing"
}


def classify_industry(context: str) -> str:
    """
    Classify industry type from context string.

    ALGORITHM: Keyword matching (deterministic, no LLM)
    Returns: 'regulated', 'commercial', or 'unknown'
    """
    context_lower = context.lower()

    # Check for regulated industry keywords
    for keyword in REGULATED_INDUSTRIES:
        if keyword in context_lower:
            return "regulated"

    # Check for commercial industry keywords
    for keyword in COMMERCIAL_INDUSTRIES:
        if keyword in context_lower:
            return "commercial"

    return "unknown"


def get_agent_sequence(task_type: str, industry_type: str) -> List[str]:
    """
    Get deterministic agent execution sequence.

    ALGORITHM: Matrix lookup (NO LLM HALLUCINATION)

    Args:
        task_type: Type of task (from ROUTING_MATRIX keys)
        industry_type: 'regulated', 'commercial', or 'unknown'

    Returns:
        List of agent names to execute in order
    """
    # Normalize task type
    task_type_normalized = task_type.lower().replace(" ", "_").replace("-", "_")

    # Get task routes
    task_routes = ROUTING_MATRIX.get(task_type_normalized, {})

    # Check for 'any' industry (applies to all)
    if "any" in task_routes:
        return task_routes["any"]

    # Get industry-specific route
    if industry_type in task_routes:
        return task_routes[industry_type]

    # Fallback to unknown industry route
    if "unknown" in task_routes:
        return task_routes["unknown"]

    # Default fallback
    return ["research_agent"]


# Define state for the supervisor graph
class SupervisorState(TypedDict):
    """State maintained throughout supervisor execution"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str
    campaign_id: str
    task_type: str
    research_data: Dict[str, Any]
    content_drafts: List[Dict[str, Any]]
    media_assets: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    # Deterministic routing state
    agent_sequence: List[str]  # Planned sequence of agents
    current_agent_index: int   # Current position in sequence
    industry_type: str         # Classified industry type
    routing_mode: str          # 'deterministic' or 'llm'


class SupervisorAgent:
    """
    Supervisor Agent using LangGraph

    ENHANCED with deterministic routing (NO LLM hallucination in routing decisions)

    Coordinates workflow between:
    - Research Agent (market/competitor research)
    - Content Agent (content creation)
    - Image Agent (image generation)
    - Video Agent (video generation)
    - Review Coordinator (human-in-the-loop)
    - Publishing Agent (multi-channel distribution)
    - Trend Agent (trend analysis)
    - Market Agent (market analysis)
    """

    def __init__(
        self,
        specialist_agents: Dict[str, Any],
        use_deterministic_routing: bool = True  # DEFAULT: Deterministic (no LLM)
    ):
        """
        Initialize supervisor

        Args:
            specialist_agents: Dict mapping agent names to agent instances
            use_deterministic_routing: If True, use rule-based routing matrix.
                                       If False, use LLM for routing decisions.
                                       DEFAULT: True (deterministic, no hallucination)
        """
        self.specialist_agents = specialist_agents
        self.use_deterministic_routing = use_deterministic_routing

        # Only initialize LLM if using LLM routing (saves resources)
        if not use_deterministic_routing:
            self.llm = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                temperature=0.3  # Lower temperature for routing decisions
            )
        else:
            self.llm = None

        # Build workflow graph
        self.workflow = self._build_workflow()

        logger.info(
            "supervisor_initialized",
            agents=list(specialist_agents.keys()),
            routing_mode="deterministic" if use_deterministic_routing else "llm"
        )

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""

        # Create graph
        workflow = StateGraph(SupervisorState)

        # Add supervisor routing node
        workflow.add_node("supervisor", self._supervisor_node)

        # Add specialist agent nodes
        for agent_name in self.specialist_agents.keys():
            workflow.add_node(agent_name, self._create_agent_node(agent_name))

        # Add end node
        workflow.add_node("finish", self._finish_node)

        # Set entry point
        workflow.set_entry_point("supervisor")

        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_decision,
            {
                **{name: name for name in self.specialist_agents.keys()},
                "finish": "finish"
            }
        )

        # Add edges back to supervisor from each agent
        for agent_name in self.specialist_agents.keys():
            workflow.add_edge(agent_name, "supervisor")

        # Finish node leads to END
        workflow.add_edge("finish", END)

        return workflow.compile()

    def _supervisor_node(self, state: SupervisorState) -> SupervisorState:
        """
        Supervisor decision node

        Analyzes current state and decides next agent to invoke.

        ROUTING MODES:
        - Deterministic (default): Uses ROUTING_MATRIX for predictable, verifiable routing
        - LLM: Uses language model for flexible but less predictable routing
        """
        messages = state["messages"]
        task_type = state.get("task_type", "content_generation")

        # =================================================================
        # DETERMINISTIC ROUTING (NO LLM HALLUCINATION)
        # =================================================================
        if self.use_deterministic_routing:
            return self._deterministic_routing(state)

        # =================================================================
        # LLM ROUTING (fallback, less predictable)
        # =================================================================
        return self._llm_routing(state)

    def _deterministic_routing(self, state: SupervisorState) -> SupervisorState:
        """
        Deterministic routing using rule-based matrix.

        ALGORITHM: Sequential agent execution from pre-computed sequence
        - NO LLM HALLUCINATION
        - Fully transparent and reproducible
        - Industry-aware routing
        """
        task_type = state.get("task_type", "content_generation")

        # Initialize sequence if not already set
        if not state.get("agent_sequence"):
            # Get initial prompt for industry classification
            initial_prompt = state["messages"][0].content if state["messages"] else ""

            # Classify industry from context
            industry_type = classify_industry(initial_prompt)
            state["industry_type"] = industry_type

            # Get agent sequence from routing matrix
            agent_sequence = get_agent_sequence(task_type, industry_type)

            # Filter to only available agents
            available_sequence = [
                agent for agent in agent_sequence
                if agent in self.specialist_agents
            ]

            state["agent_sequence"] = available_sequence if available_sequence else ["finish"]
            state["current_agent_index"] = 0
            state["routing_mode"] = "deterministic"

            logger.info(
                "deterministic_routing_initialized",
                task_type=task_type,
                industry_type=industry_type,
                agent_sequence=state["agent_sequence"],
                algorithm="ROUTING_MATRIX lookup (no LLM)"
            )

        # Get next agent from sequence
        current_index = state.get("current_agent_index", 0)
        agent_sequence = state.get("agent_sequence", [])

        if current_index < len(agent_sequence):
            next_agent = agent_sequence[current_index]
            state["current_agent_index"] = current_index + 1
        else:
            next_agent = "finish"

        state["next_agent"] = next_agent

        # Add routing decision to messages with algorithm attribution
        state["messages"].append(AIMessage(
            content=f"[DETERMINISTIC ROUTING] Step {current_index + 1}/{len(agent_sequence)}: {next_agent} "
                    f"(industry: {state.get('industry_type', 'unknown')}, algorithm: matrix_lookup)"
        ))

        logger.info(
            "deterministic_routing_decision",
            next_agent=next_agent,
            step=current_index + 1,
            total_steps=len(agent_sequence),
            industry_type=state.get("industry_type"),
            is_verified=True
        )

        return state

    def _llm_routing(self, state: SupervisorState) -> SupervisorState:
        """
        LLM-based routing (fallback mode).

        WARNING: This mode uses LLM inference for routing decisions,
        which may be less predictable than deterministic routing.
        """
        messages = state["messages"]
        task_type = state.get("task_type", "content_generation")

        # Build supervisor prompt
        system_prompt = """You are the Supervisor Agent coordinating a B2B marketing automation system.

You manage these specialist agents:
- research_agent: Conducts market research and competitor analysis
- content_agent: Creates blog posts, LinkedIn content, emails
- image_agent: Generates images using DALL-E 3
- video_agent: Creates videos using Runway ML
- trend_agent: Monitors social media and industry trends
- review_coordinator: Coordinates human review and approval
- publishing_agent: Publishes content to LinkedIn, WordPress, email
- market_agent: Market analysis and TAM/SAM/SOM calculation

Based on the current task and progress, decide which agent should act next.

Current task type: {task_type}
Progress so far: {progress}

Respond with ONLY the agent name (e.g., "research_agent") or "finish" if the workflow is complete.
"""

        # Determine progress
        progress_summary = self._summarize_progress(state)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Which agent should act next?")
        ])

        # Get LLM decision
        chain = prompt | self.llm
        response = chain.invoke({
            "task_type": task_type,
            "progress": progress_summary,
            "messages": messages
        })

        # Extract agent name from response
        next_agent = response.strip().lower()

        # Set routing mode
        state["routing_mode"] = "llm"

        logger.info(
            "llm_routing_decision",
            next_agent=next_agent,
            task_type=task_type,
            warning="LLM-based routing is less predictable than deterministic"
        )

        state["next_agent"] = next_agent
        state["messages"].append(AIMessage(content=f"[LLM ROUTING] Selected: {next_agent}"))

        return state

    def _route_decision(self, state: SupervisorState) -> str:
        """
        Routing logic based on supervisor decision

        Returns:
            Agent name or "finish"
        """
        next_agent = state.get("next_agent", "finish")

        # Validate agent exists
        if next_agent in self.specialist_agents:
            return next_agent
        elif next_agent == "finish":
            return "finish"
        else:
            # Default to finish if invalid
            logger.warning("invalid_agent_route", agent=next_agent)
            return "finish"

    def _create_agent_node(self, agent_name: str):
        """
        Create node function for specialist agent

        Args:
            agent_name: Name of specialist agent

        Returns:
            Node function
        """
        def agent_node(state: SupervisorState) -> SupervisorState:
            """Execute specialist agent"""
            agent = self.specialist_agents[agent_name]

            # Get last message as input
            last_message = state["messages"][-1].content

            # Execute agent
            logger.info("executing_agent", agent=agent_name)
            result = agent.run(last_message)

            # Update state based on agent type
            if agent_name == "research_agent":
                state["research_data"] = result.get("data", {})
            elif agent_name in ["content_agent", "image_agent", "video_agent"]:
                if "content_drafts" not in state:
                    state["content_drafts"] = []
                state["content_drafts"].append({
                    "agent": agent_name,
                    "content": result.get("output"),
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif agent_name in ["image_agent", "video_agent"]:
                if "media_assets" not in state:
                    state["media_assets"] = []
                state["media_assets"].append({
                    "agent": agent_name,
                    "assets": result.get("assets", []),
                    "timestamp": datetime.utcnow().isoformat()
                })

            # Add agent response to messages
            state["messages"].append(AIMessage(
                content=f"[{agent_name}] {result.get('output', '')}"
            ))

            return state

        return agent_node

    def _finish_node(self, state: SupervisorState) -> SupervisorState:
        """Final node - prepare results"""
        logger.info("workflow_complete", campaign_id=state.get("campaign_id"))

        state["messages"].append(AIMessage(
            content="Workflow complete. All tasks finished."
        ))

        return state

    def _summarize_progress(self, state: SupervisorState) -> str:
        """Summarize current workflow progress"""
        summary_parts = []

        if state.get("research_data"):
            summary_parts.append("✓ Research completed")

        content_count = len(state.get("content_drafts", []))
        if content_count > 0:
            summary_parts.append(f"✓ {content_count} content drafts created")

        media_count = len(state.get("media_assets", []))
        if media_count > 0:
            summary_parts.append(f"✓ {media_count} media assets generated")

        return ", ".join(summary_parts) if summary_parts else "No progress yet"

    def execute(
        self,
        campaign_id: str,
        task_type: str,
        initial_prompt: str
    ) -> Dict[str, Any]:
        """
        Execute supervised workflow

        Args:
            campaign_id: Campaign identifier
            task_type: Type of task (content_generation, competitor_analysis, etc.)
            initial_prompt: Initial user prompt

        Returns:
            Final state with all results
        """
        start_time = datetime.utcnow()

        logger.info(
            "supervisor_execution_start",
            campaign_id=campaign_id,
            task_type=task_type
        )

        # Initialize state
        initial_state = SupervisorState(
            messages=[HumanMessage(content=initial_prompt)],
            next_agent="",
            campaign_id=campaign_id,
            task_type=task_type,
            research_data={},
            content_drafts=[],
            media_assets=[],
            metadata={"started_at": start_time.isoformat()},
            # Deterministic routing state (initialized by _deterministic_routing)
            agent_sequence=[],
            current_agent_index=0,
            industry_type="",
            routing_mode="deterministic" if self.use_deterministic_routing else "llm"
        )

        try:
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                "supervisor_execution_complete",
                campaign_id=campaign_id,
                execution_time=execution_time,
                content_drafts=len(final_state.get("content_drafts", [])),
                media_assets=len(final_state.get("media_assets", []))
            )

            return {
                "status": "completed",
                "campaign_id": campaign_id,
                "task_type": task_type,
                "research_data": final_state.get("research_data", {}),
                "content_drafts": final_state.get("content_drafts", []),
                "media_assets": final_state.get("media_assets", []),
                "messages": [msg.content for msg in final_state.get("messages", [])],
                "execution_time": execution_time,
                "completed_at": datetime.utcnow().isoformat(),
                # Routing transparency (NO LLM hallucination verification)
                "routing": {
                    "mode": final_state.get("routing_mode", "unknown"),
                    "industry_type": final_state.get("industry_type", "unknown"),
                    "agent_sequence": final_state.get("agent_sequence", []),
                    "steps_completed": final_state.get("current_agent_index", 0),
                    "algorithm": "ROUTING_MATRIX lookup" if final_state.get("routing_mode") == "deterministic" else "LLM inference",
                    "is_verified": final_state.get("routing_mode") == "deterministic"
                }
            }

        except Exception as e:
            logger.error(
                "supervisor_execution_error",
                campaign_id=campaign_id,
                error=str(e),
                exc_info=True
            )

            return {
                "status": "error",
                "campaign_id": campaign_id,
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }

    async def aexecute(
        self,
        campaign_id: str,
        task_type: str,
        initial_prompt: str
    ) -> Dict[str, Any]:
        """Async execution wrapper"""
        # LangGraph doesn't have full async support yet
        # For now, wrap sync execution
        return self.execute(campaign_id, task_type, initial_prompt)


def create_supervisor(
    llm=None,
    specialist_agents: Dict[str, Any] = None,
    use_deterministic_routing: bool = True
) -> SupervisorAgent:
    """
    Factory function to create SupervisorAgent instance

    Args:
        llm: LLM instance (not used by supervisor, kept for API compatibility)
        specialist_agents: Dict of specialist agents (optional, can be empty dict)
        use_deterministic_routing: If True (default), use rule-based routing matrix.
                                   This provides predictable, verifiable routing
                                   with NO LLM hallucination in routing decisions.

    Returns:
        SupervisorAgent instance
    """
    if specialist_agents is None:
        specialist_agents = {}

    return SupervisorAgent(
        specialist_agents=specialist_agents,
        use_deterministic_routing=use_deterministic_routing
    )


# =============================================================================
# ROUTING UTILITIES (Exported for testing and direct use)
# =============================================================================

def get_routing_info(task_type: str, context: str) -> Dict[str, Any]:
    """
    Get routing information for a given task type and context.

    Useful for debugging and transparency.

    Args:
        task_type: Type of task (e.g., 'content_generation', 'market_analysis')
        context: Context string for industry classification

    Returns:
        Dict with routing details
    """
    industry_type = classify_industry(context)
    agent_sequence = get_agent_sequence(task_type, industry_type)

    return {
        "task_type": task_type,
        "industry_type": industry_type,
        "agent_sequence": agent_sequence,
        "total_steps": len(agent_sequence),
        "routing_matrix_used": True,
        "algorithm": "ROUTING_MATRIX lookup (deterministic, no LLM)",
        "is_verified": True
    }


def list_available_task_types() -> List[str]:
    """Return list of supported task types for routing."""
    return list(ROUTING_MATRIX.keys())


def list_industry_keywords() -> Dict[str, set]:
    """Return industry classification keywords for debugging."""
    return {
        "regulated": REGULATED_INDUSTRIES,
        "commercial": COMMERCIAL_INDUSTRIES
    }
