"""
Base Agent Class
Provides common functionality for all specialist agents
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
import structlog
from datetime import datetime

from config import settings


logger = structlog.get_logger()


class BaseAgent(ABC):
    """
    Base class for all marketing automation agents

    Implements:
    - ReAct pattern (Reasoning + Acting)
    - Conversation memory
    - Tool management
    - Logging and tracing
    """

    def __init__(
        self,
        name: str,
        description: str,
        tools: List[Tool],
        llm: Optional[Any] = None,
        memory: Optional[ConversationBufferMemory] = None,
        verbose: bool = False
    ):
        """
        Initialize base agent

        Args:
            name: Agent name (e.g., "Research Agent")
            description: Agent's role and capabilities
            tools: List of tools available to this agent
            llm: Language model (defaults to Ollama)
            memory: Conversation memory (defaults to new memory)
            verbose: Enable verbose logging
        """
        self.name = name
        self.description = description
        self.tools = tools
        self.verbose = verbose

        # Initialize LLM
        self.llm = llm or self._create_default_llm()

        # Initialize memory
        self.memory = memory or ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

        # Create agent executor
        self.executor = self._create_executor()

        # Metadata
        self.created_at = datetime.utcnow()
        self.execution_count = 0

        logger.info(
            "agent_initialized",
            name=self.name,
            tools=[tool.name for tool in self.tools]
        )

    def _create_default_llm(self) -> Ollama:
        """Create default Ollama LLM"""
        return Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.LLM_TEMPERATURE
        )

    def _create_executor(self) -> AgentExecutor:
        """Create ReAct agent executor"""

        # Create ReAct prompt template
        template = """You are {agent_name}, {agent_description}.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Previous conversation:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["tools", "tool_names", "chat_history", "input", "agent_scratchpad"],
            partial_variables={
                "agent_name": self.name,
                "agent_description": self.description
            }
        )

        # Create agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        # Create executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=self.verbose,
            max_iterations=settings.AGENT_MAX_ITERATIONS,
            max_execution_time=settings.AGENT_TIMEOUT,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )

    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Execute agent with input

        Args:
            input_text: User query or task
            **kwargs: Additional parameters

        Returns:
            Dict with output and metadata
        """
        start_time = datetime.utcnow()

        try:
            logger.info(
                "agent_execution_start",
                agent=self.name,
                input=input_text[:100]  # Truncate for logging
            )

            # Run agent
            result = self.executor.invoke({"input": input_text, **kwargs})

            # Update metrics
            self.execution_count += 1
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                "agent_execution_complete",
                agent=self.name,
                execution_time=execution_time,
                iterations=len(result.get("intermediate_steps", []))
            )

            return {
                "output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_time": execution_time,
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(
                "agent_execution_error",
                agent=self.name,
                error=str(e),
                exc_info=True
            )

            return {
                "output": f"Error: {str(e)}",
                "error": str(e),
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def arun(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Async execution

        Args:
            input_text: User query or task
            **kwargs: Additional parameters

        Returns:
            Dict with output and metadata
        """
        start_time = datetime.utcnow()

        try:
            logger.info(
                "agent_async_execution_start",
                agent=self.name,
                input=input_text[:100]
            )

            # Run agent asynchronously
            result = await self.executor.ainvoke({"input": input_text, **kwargs})

            # Update metrics
            self.execution_count += 1
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                "agent_async_execution_complete",
                agent=self.name,
                execution_time=execution_time
            )

            return {
                "output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_time": execution_time,
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(
                "agent_async_execution_error",
                agent=self.name,
                error=str(e),
                exc_info=True
            )

            return {
                "output": f"Error: {str(e)}",
                "error": str(e),
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]

    def get_memory(self) -> List[Dict[str, str]]:
        """Get conversation memory"""
        return self.memory.chat_memory.messages

    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("agent_memory_cleared", agent=self.name)

    def add_tool(self, tool: Tool):
        """Add new tool to agent"""
        self.tools.append(tool)
        # Recreate executor with new tools
        self.executor = self._create_executor()
        logger.info("agent_tool_added", agent=self.name, tool=tool.name)

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.get_tools(),
            "execution_count": self.execution_count,
            "created_at": self.created_at.isoformat(),
            "memory_size": len(self.get_memory())
        }

    @abstractmethod
    def get_specialized_prompt(self) -> str:
        """
        Get specialized system prompt for this agent
        Subclasses must implement this to define agent-specific behavior
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', tools={len(self.tools)})>"
