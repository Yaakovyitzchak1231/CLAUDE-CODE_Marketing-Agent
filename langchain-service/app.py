"""
FastAPI Server for Marketing Automation Agents
Exposes all LangChain agents through REST API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime
import uvicorn

# Agent imports
from agents.supervisor import create_supervisor
from agents.research_agent import create_research_agent
from agents.competitor_agent import create_competitor_agent
from agents.market_agent import create_market_agent
from agents.content_agent import create_content_agent
from agents.image_agent import create_image_agent
from agents.video_agent import create_video_agent
from agents.trend_agent import create_trend_agent

# Chain imports
from chains.seo_optimizer import create_seo_optimizer
from chains.image_prompt_builder import create_image_prompt_builder
from chains.video_script_builder import create_video_script_builder

# Tool and utility imports
from config import settings, create_llm

# API route imports
from api.brand_voice import router as brand_voice_router

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Marketing Automation AI API",
    description="Multi-agent system for B2B marketing content generation and automation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(brand_voice_router)

# Initialize LLM (OpenAI if configured, else Ollama)
llm = create_llm()

# Initialize agents (singleton pattern)
agents = {}
chains = {}


def initialize_agents():
    """Initialize all agents and chains"""
    global agents, chains

    logger.info("initializing_agents_and_chains")

    try:
        # Initialize agents
        agents["supervisor"] = create_supervisor(llm)
        agents["research"] = create_research_agent()
        agents["competitor"] = create_competitor_agent()
        agents["market"] = create_market_agent()
        agents["content"] = create_content_agent()
        agents["image"] = create_image_agent()
        agents["video"] = create_video_agent()
        agents["trend"] = create_trend_agent()

        # Initialize chains
        chains["seo_optimizer"] = create_seo_optimizer(llm)
        chains["image_prompt_builder"] = create_image_prompt_builder(llm)
        chains["video_script_builder"] = create_video_script_builder(llm)

        logger.info("agents_and_chains_initialized", agent_count=len(agents), chain_count=len(chains))

    except Exception as e:
        logger.error("initialization_error", error=str(e))
        raise


# Pydantic models for request/response validation

class SupervisorRequest(BaseModel):
    task: str = Field(..., description="Task description for supervisor to route")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")


class ResearchRequest(BaseModel):
    query: str = Field(..., description="Research query")
    depth: str = Field(default="comprehensive", description="Research depth: quick, standard, comprehensive")
    sources: Optional[List[str]] = Field(default=None, description="Specific sources to search")


class CompetitorAnalysisRequest(BaseModel):
    competitor_name: str = Field(..., description="Competitor company name")
    competitor_url: Optional[str] = Field(default=None, description="Competitor website URL")
    analysis_type: str = Field(default="full", description="Analysis type: full, content_strategy, monitoring")


class MarketAnalysisRequest(BaseModel):
    product_description: str = Field(..., description="Product or service description")
    target_market: str = Field(..., description="Target market description")
    geography: str = Field(default="global", description="Geographic market")


class ContentCreationRequest(BaseModel):
    content_type: str = Field(..., description="Content type: blog, linkedin_post, email, social_post")
    topic: str = Field(..., description="Content topic")
    target_audience: str = Field(..., description="Target audience")
    tone: str = Field(default="professional", description="Tone of voice")
    keywords: Optional[List[str]] = Field(default=None, description="Target keywords")
    length: Optional[int] = Field(default=None, description="Target word count")
    brand_voice_profile_id: Optional[str] = Field(default=None, description="UUID of brand voice profile to apply")


class ImageGenerationRequest(BaseModel):
    content_description: str = Field(..., description="Description of content/message")
    platform: str = Field(default="linkedin", description="Target platform")
    style: str = Field(default="professional", description="Visual style")
    brand_colors: Optional[List[str]] = Field(default=None, description="Brand colors")
    provider: str = Field(default="dalle", description="Provider: dalle, midjourney")


class VideoGenerationRequest(BaseModel):
    content: str = Field(..., description="Video content/message")
    platform: str = Field(default="linkedin", description="Target platform")
    duration: int = Field(default=30, description="Target duration in seconds")
    style: str = Field(default="professional", description="Visual style")
    provider: str = Field(default="runway", description="Provider: runway, pika")


class TrendAnalysisRequest(BaseModel):
    industry: str = Field(..., description="Industry to monitor")
    time_range: str = Field(default="week", description="Time range: day, week, month")
    include_social: bool = Field(default=True, description="Include social media analysis")


class SEOOptimizationRequest(BaseModel):
    content: str = Field(..., description="Content to optimize")
    primary_keyword: Optional[str] = Field(default=None, description="Primary keyword")
    target_keywords: Optional[List[str]] = Field(default=None, description="Additional target keywords")


class ImagePromptRequest(BaseModel):
    content_description: str = Field(..., description="Content description")
    image_purpose: str = Field(default="social media post", description="Purpose of image")
    platform: Optional[str] = Field(default=None, description="Target platform")
    style_preference: str = Field(default="professional", description="Style preference")
    brand_colors: Optional[List[str]] = Field(default=None, description="Brand colors")


class VideoScriptRequest(BaseModel):
    content: str = Field(..., description="Content or message")
    duration: int = Field(default=30, description="Target duration in seconds")
    video_type: str = Field(default="social_media", description="Video type")
    platform: Optional[str] = Field(default=None, description="Target platform")
    style: str = Field(default="professional", description="Visual style")


class VectorEmbeddingsSearchRequest(BaseModel):
    collection_name: str = Field(..., description="Name of the vector collection")
    query: str = Field(..., description="Search query text")
    k: int = Field(default=5, description="Number of results to return")
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filter")


class VectorEmbeddingsAddRequest(BaseModel):
    collection_name: str = Field(..., description="Name of the vector collection")
    texts: List[str] = Field(..., description="Texts to embed and store")
    metadatas: Optional[List[Dict[str, Any]]] = Field(default=None, description="Metadata for each text")
    chunk_strategy: str = Field(default="recursive", description="Chunking strategy: none, recursive, semantic")


class GrammarCheckRequest(BaseModel):
    text: str = Field(..., description="Text to check for grammar issues")


class OrchestrationRequest(BaseModel):
    """Request for unified orchestration endpoint."""
    task_type: str = Field(..., description="Task type: content_blog, content_linkedin, campaign_plan, campaign_calendar, research_market, research_competitor, research_trends")
    mode: str = Field(default="auto", description="Orchestration mode: langgraph, crewai, or auto")
    topic: Optional[str] = Field(default=None, description="Content topic (for content tasks)")
    target_audience: Optional[str] = Field(default=None, description="Target audience")
    campaign_brief: Optional[str] = Field(default=None, description="Campaign brief (for campaign tasks)")
    campaign_theme: Optional[str] = Field(default=None, description="Campaign theme (for calendar)")
    product_description: Optional[str] = Field(default=None, description="Product description (for market research)")
    target_market: Optional[str] = Field(default=None, description="Target market (for market research)")
    competitor_name: Optional[str] = Field(default=None, description="Competitor name (for competitor analysis)")
    competitor_url: Optional[str] = Field(default=None, description="Competitor URL")
    industry: Optional[str] = Field(default=None, description="Industry (for trend analysis)")
    keywords: Optional[List[str]] = Field(default=None, description="Target keywords")
    word_count: Optional[int] = Field(default=None, description="Target word count")
    tone: Optional[str] = Field(default="professional", description="Tone of voice")
    duration_weeks: Optional[int] = Field(default=4, description="Campaign duration in weeks")
    channels: Optional[List[str]] = Field(default=None, description="Marketing channels")


# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Marketing Automation AI API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    # Determine which LLM provider is active
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        llm_info = {
            "provider": "openai",
            "model": settings.OPENAI_MODEL
        }
    else:
        llm_info = {
            "provider": "ollama",
            "model": settings.OLLAMA_MODEL,
            "base_url": settings.OLLAMA_BASE_URL
        }

    return {
        "status": "healthy",
        "agents": list(agents.keys()),
        "chains": list(chains.keys()),
        "llm": llm_info,
        "timestamp": datetime.utcnow().isoformat()
    }


# Supervisor Agent endpoint
@app.post("/supervisor")
async def run_supervisor(request: SupervisorRequest):
    """
    Run supervisor agent to route and execute task

    The supervisor analyzes the task and routes to appropriate specialist agents
    """
    try:
        logger.info("supervisor_request", task=request.task)

        # Generate a campaign ID for this request
        import uuid
        campaign_id = str(uuid.uuid4())[:8]

        result = agents["supervisor"].execute(
            campaign_id=campaign_id,
            task_type="general",
            initial_prompt=request.task
        )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("supervisor_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Research Agent endpoint
@app.post("/agents/research")
async def run_research(request: ResearchRequest):
    """
    Conduct research on a topic

    Uses SearXNG, web scraping, and sentiment analysis
    """
    try:
        logger.info("research_request", query=request.query, depth=request.depth)

        result = agents["research"].conduct_research(
            query=request.query,
            depth=request.depth,
            sources=request.sources
        )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("research_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Competitor Agent endpoint
@app.post("/agents/competitor")
async def run_competitor_analysis(request: CompetitorAnalysisRequest):
    """
    Analyze competitor

    Profiles competitors, analyzes content strategy, and monitors changes
    """
    try:
        logger.info("competitor_request", competitor=request.competitor_name)

        if request.analysis_type == "full":
            result = agents["competitor"].profile_competitor(
                competitor_name=request.competitor_name,
                competitor_url=request.competitor_url
            )
        elif request.analysis_type == "content_strategy":
            result = agents["competitor"].analyze_content_strategy(
                competitor_name=request.competitor_name
            )
        else:
            result = agents["competitor"].monitor_changes(
                competitor_name=request.competitor_name
            )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("competitor_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Market Analysis Agent endpoint
@app.post("/agents/market")
async def run_market_analysis(request: MarketAnalysisRequest):
    """
    Analyze market and create buyer personas

    Provides TAM/SAM/SOM calculations and audience segmentation
    """
    try:
        logger.info("market_request", product=request.product_description)

        result = agents["market"].analyze_market_opportunity(
            product_description=request.product_description,
            target_market=request.target_market,
            geography=request.geography
        )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("market_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Content Creation Agent endpoint
@app.post("/agents/content")
async def run_content_creation(request: ContentCreationRequest):
    """
    Generate marketing content

    Creates blog posts, LinkedIn posts, emails, and social media content
    """
    try:
        logger.info(
            "content_request",
            content_type=request.content_type,
            topic=request.topic,
            brand_voice_profile_id=request.brand_voice_profile_id
        )

        # Create content agent with brand voice profile if provided
        # This allows per-request brand voice customization
        if request.brand_voice_profile_id:
            content_agent = create_content_agent(brand_voice_profile_id=request.brand_voice_profile_id)
        else:
            content_agent = agents["content"]

        if request.content_type == "blog":
            result = content_agent.create_blog_post(
                topic=request.topic,
                target_audience=request.target_audience,
                keywords=request.keywords or [],
                word_count=request.length or 1500
            )
        elif request.content_type == "linkedin_post":
            result = content_agent.create_linkedin_post(
                topic=request.topic,
                target_audience=request.target_audience,
                tone=request.tone
            )
        elif request.content_type == "email":
            result = content_agent.create_email_campaign(
                campaign_topic=request.topic,
                target_audience=request.target_audience,
                email_count=3
            )
        else:  # social_post
            result = content_agent.create_social_post(
                topic=request.topic,
                platform=request.platform if hasattr(request, 'platform') else "linkedin",
                target_audience=request.target_audience
            )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("content_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Image Generation Agent endpoint
@app.post("/agents/image")
async def run_image_generation(request: ImageGenerationRequest):
    """
    Generate marketing images

    Uses DALL-E 3 or Midjourney to create visuals
    """
    try:
        logger.info("image_request", platform=request.platform, provider=request.provider)

        result = agents["image"].generate_social_media_image(
            content=request.content_description,
            platform=request.platform,
            brand_colors=request.brand_colors,
            style=request.style,
            provider=request.provider
        )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("image_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Video Generation Agent endpoint
@app.post("/agents/video")
async def run_video_generation(request: VideoGenerationRequest):
    """
    Generate marketing videos

    Uses Runway ML or Pika to create videos
    """
    try:
        logger.info("video_request", platform=request.platform, duration=request.duration)

        result = agents["video"].generate_social_video(
            content=request.content,
            platform=request.platform,
            duration=request.duration,
            style=request.style,
            provider=request.provider
        )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("video_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Trend Agent endpoint
@app.post("/agents/trend")
async def run_trend_analysis(request: TrendAnalysisRequest):
    """
    Monitor industry trends

    Tracks trending topics and analyzes momentum
    """
    try:
        logger.info("trend_request", industry=request.industry)

        result = agents["trend"].monitor_industry_trends(
            industry=request.industry,
            time_range=request.time_range,
            include_social=request.include_social
        )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("trend_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# SEO Optimization Chain endpoint
@app.post("/chains/seo")
async def run_seo_optimization(request: SEOOptimizationRequest):
    """
    Optimize content for SEO

    Analyzes and enhances content for search engines
    """
    try:
        logger.info("seo_request", content_length=len(request.content))

        result = chains["seo_optimizer"].optimize(
            content=request.content,
            primary_keyword=request.primary_keyword,
            target_keywords=request.target_keywords
        )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("seo_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Image Prompt Builder Chain endpoint
@app.post("/chains/image-prompt")
async def run_image_prompt_builder(request: ImagePromptRequest):
    """
    Build optimized image generation prompts

    Converts content descriptions to DALL-E 3 and Midjourney prompts
    """
    try:
        logger.info("image_prompt_request", purpose=request.image_purpose)

        result = chains["image_prompt_builder"].build_prompt(
            content_description=request.content_description,
            image_purpose=request.image_purpose,
            platform=request.platform,
            style_preference=request.style_preference,
            brand_colors=request.brand_colors
        )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("image_prompt_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Video Script Builder Chain endpoint
@app.post("/chains/video-script")
async def run_video_script_builder(request: VideoScriptRequest):
    """
    Build video scripts with scene breakdowns

    Creates detailed video scripts for content
    """
    try:
        logger.info("video_script_request", duration=request.duration, video_type=request.video_type)

        result = chains["video_script_builder"].build_script(
            content=request.content,
            duration=request.duration,
            video_type=request.video_type,
            platform=request.platform,
            style=request.style
        )

        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("video_script_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# SEO Optimizer alias endpoint (for n8n workflows)
@app.post("/chains/seo-optimizer")
async def run_seo_optimizer_alias(request: SEOOptimizationRequest):
    """
    Alias for /chains/seo endpoint

    Used by n8n workflows for SEO optimization
    """
    return await run_seo_optimization(request)


# =============================================================================
# VECTOR EMBEDDINGS ENDPOINTS
# =============================================================================

@app.post("/storage/vector-embeddings/search")
async def search_vector_embeddings(request: VectorEmbeddingsSearchRequest):
    """
    Search vector embeddings in a collection

    Used by n8n workflows to find similar content
    """
    try:
        logger.info(
            "vector_search_request",
            collection=request.collection_name,
            query=request.query[:50]
        )

        # Import vector store utilities
        from storage.vector_store import get_vector_store

        vector_store = get_vector_store(request.collection_name)

        # Perform similarity search
        results = vector_store.similarity_search_with_score(
            query=request.query,
            k=request.k,
            filter=request.filter
        )

        # Format results
        formatted_results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            }
            for doc, score in results
        ]

        return JSONResponse(content={
            "success": True,
            "collection": request.collection_name,
            "query": request.query,
            "results": formatted_results,
            "count": len(formatted_results),
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("vector_search_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/storage/vector-embeddings/add")
async def add_vector_embeddings(request: VectorEmbeddingsAddRequest):
    """
    Add texts to vector embeddings collection

    Used by n8n workflows to store content embeddings
    """
    try:
        logger.info(
            "vector_add_request",
            collection=request.collection_name,
            text_count=len(request.texts)
        )

        # Import vector store utilities
        from storage.vector_store import get_vector_store

        vector_store = get_vector_store(request.collection_name)

        # Add texts with optional metadata
        ids = vector_store.add_texts(
            texts=request.texts,
            metadatas=request.metadatas
        )

        return JSONResponse(content={
            "success": True,
            "collection": request.collection_name,
            "added_count": len(ids),
            "ids": ids,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("vector_add_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TOOLS ENDPOINTS
# =============================================================================

@app.post("/tools/grammar-check")
async def check_grammar(request: GrammarCheckRequest):
    """
    Check text for grammar issues

    Uses LLM to identify and suggest grammar corrections
    """
    try:
        logger.info("grammar_check_request", text_length=len(request.text))

        from langchain.prompts import PromptTemplate

        grammar_prompt = PromptTemplate(
            input_variables=["text"],
            template="""Analyze the following text for grammar, spelling, and punctuation errors.
Return a JSON object with:
- "corrected_text": The text with all corrections applied
- "issues": An array of issues found, each with "original", "correction", "type" (grammar/spelling/punctuation), and "explanation"
- "score": A grammar quality score from 0-100

Text to analyze:
{text}

Return only valid JSON, no additional text."""
        )

        chain = grammar_prompt | llm
        result = chain.invoke({"text": request.text})

        # Parse the LLM response
        import json
        try:
            parsed_result = json.loads(result.content if hasattr(result, 'content') else str(result))
        except json.JSONDecodeError:
            # If JSON parsing fails, return a basic response
            parsed_result = {
                "corrected_text": request.text,
                "issues": [],
                "score": 100
            }

        return JSONResponse(content={
            "success": True,
            "original_text": request.text,
            "corrected_text": parsed_result.get("corrected_text", request.text),
            "issues": parsed_result.get("issues", []),
            "score": parsed_result.get("score", 100),
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("grammar_check_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# NEW INTEGRATION ENDPOINTS
# =============================================================================

# Unified Orchestration endpoint
@app.post("/orchestrate")
async def run_orchestration(request: OrchestrationRequest):
    """
    Unified orchestration endpoint supporting both LangGraph and CrewAI modes.

    Task types:
    - content_blog, content_linkedin: Content generation
    - campaign_plan, campaign_calendar: Campaign management
    - research_market, research_competitor, research_trends: Research tasks

    Modes:
    - langgraph: Use existing LangGraph supervisor (default)
    - crewai: Use CrewAI multi-agent crews
    - auto: Choose best mode based on task
    """
    try:
        from config import settings

        # Determine orchestration mode
        mode = request.mode
        if mode == "auto":
            mode = getattr(settings, 'ORCHESTRATION_MODE', 'langgraph')

        logger.info(
            "orchestration_request",
            task_type=request.task_type,
            mode=mode
        )

        if mode == "crewai":
            # Use CrewAI orchestrator
            from crewai_integration import get_orchestrator

            orchestrator = get_orchestrator()
            kwargs = {
                'topic': request.topic,
                'target_audience': request.target_audience,
                'campaign_brief': request.campaign_brief,
                'campaign_theme': request.campaign_theme,
                'product_description': request.product_description,
                'target_market': request.target_market,
                'competitor_name': request.competitor_name,
                'competitor_url': request.competitor_url,
                'industry': request.industry,
                'keywords': request.keywords,
                'word_count': request.word_count,
                'tone': request.tone,
                'duration_weeks': request.duration_weeks,
                'channels': request.channels
            }
            # Remove None values
            kwargs = {k: v for k, v in kwargs.items() if v is not None}

            result = orchestrator.run(request.task_type, **kwargs)

        else:
            # Use LangGraph supervisor (existing behavior)
            # Map task types to supervisor commands
            task_mapping = {
                'content_blog': f"Create a blog post about {request.topic} for {request.target_audience}",
                'content_linkedin': f"Create a LinkedIn post about {request.topic} for {request.target_audience}",
                'campaign_plan': f"Plan a marketing campaign: {request.campaign_brief} for {request.target_audience}",
                'research_market': f"Research market opportunity for {request.product_description} in {request.target_market}",
                'research_competitor': f"Analyze competitor: {request.competitor_name}",
                'research_trends': f"Identify trends in {request.industry}"
            }

            task_description = task_mapping.get(
                request.task_type,
                f"Execute task: {request.task_type}"
            )

            # Generate a campaign ID for this request
            import uuid
            campaign_id = str(uuid.uuid4())[:8]

            result = agents["supervisor"].execute(
                campaign_id=campaign_id,
                task_type=request.task_type,
                initial_prompt=task_description
            )
            result['process'] = 'langgraph_supervisor'

        return JSONResponse(content={
            "success": True,
            "mode": mode,
            "task_type": request.task_type,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("orchestration_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# LLM Providers endpoint
@app.get("/llm/providers")
async def list_llm_providers():
    """
    List all available LLM providers and their status.

    Returns provider information including:
    - Configuration (model, temperature, etc.)
    - Availability status
    - Capabilities (streaming, function calling)
    """
    try:
        from llm_providers import list_providers

        providers = list_providers()

        return JSONResponse(content={
            "success": True,
            "providers": providers,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("llm_providers_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Orchestration Modes endpoint
@app.get("/orchestration/modes")
async def list_orchestration_modes():
    """
    List available orchestration modes and current configuration.

    Modes:
    - langgraph: LangGraph supervisor with specialist agents
    - crewai: CrewAI role-based multi-agent crews
    """
    try:
        from config import settings

        current_mode = getattr(settings, 'ORCHESTRATION_MODE', 'langgraph')

        modes = {
            'current_mode': current_mode,
            'available_modes': {
                'langgraph': {
                    'name': 'LangGraph Supervisor',
                    'description': 'Hierarchical supervisor routing to specialist agents',
                    'agents': list(agents.keys()),
                    'status': 'active' if agents else 'not_initialized'
                },
                'crewai': {
                    'name': 'CrewAI Orchestrator',
                    'description': 'Role-based multi-agent crews with defined tasks',
                    'available_tasks': [
                        'content_blog', 'content_linkedin',
                        'campaign_plan', 'campaign_calendar',
                        'research_market', 'research_competitor', 'research_trends'
                    ],
                    'status': 'available'
                }
            }
        }

        return JSONResponse(content={
            "success": True,
            "modes": modes,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("orchestration_modes_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize agents and chains on startup"""
    logger.info("api_server_starting")
    initialize_agents()
    logger.info("api_server_ready")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("api_server_shutting_down")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
