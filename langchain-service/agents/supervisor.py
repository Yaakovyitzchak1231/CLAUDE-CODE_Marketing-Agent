"""
Supervisor Agent
Orchestrates all specialist agents using LangGraph
"""

from typing import Dict, List, Any, Annotated, TypedDict, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import structlog
from datetime import datetime
import operator

from config import settings


logger = structlog.get_logger()


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


class SupervisorAgent:
    """
    Supervisor Agent using LangGraph

    Coordinates workflow between:
    - Research Agent (market/competitor research)
    - Content Agent (content creation)
    - Image Agent (image generation)
    - Video Agent (video generation)
    - Review Coordinator (human-in-the-loop)
    - Publishing Agent (multi-channel distribution)
    """

    def __init__(self, specialist_agents: Dict[str, Any]):
        """
        Initialize supervisor

        Args:
            specialist_agents: Dict mapping agent names to agent instances
        """
        self.specialist_agents = specialist_agents
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.3  # Lower temperature for routing decisions
        )

        # Build workflow graph
        self.workflow = self._build_workflow()

        logger.info(
            "supervisor_initialized",
            agents=list(specialist_agents.keys())
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

        Analyzes current state and decides next agent to invoke
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

        logger.info(
            "supervisor_routing",
            next_agent=next_agent,
            task_type=task_type
        )

        state["next_agent"] = next_agent
        state["messages"].append(AIMessage(content=f"Routing to: {next_agent}"))

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
            metadata={"started_at": start_time.isoformat()}
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
                "completed_at": datetime.utcnow().isoformat()
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
