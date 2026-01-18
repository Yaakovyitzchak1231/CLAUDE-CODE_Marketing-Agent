"""
PostgreSQL Storage
Data storage utilities for LangChain service outputs
"""

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
import os

logger = structlog.get_logger()


class PostgreSQLStorage:
    """
    PostgreSQL storage manager for LangChain service

    Handles storage of:
    - Research results
    - Content analysis
    - Sentiment scores
    - NER entities
    - Generated content
    - Agent outputs
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize PostgreSQL storage

        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://n8n:n8npassword@postgres:5432/marketing'
        )

        self.pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=self.database_url
            )

            logger.info("postgres_storage_initialized")

            # Create tables if they don't exist
            self._create_tables()

        except Exception as e:
            logger.error("postgres_initialization_error", error=str(e))
            raise

    def _create_tables(self):
        """Create storage tables"""
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            # Enable UUID extension
            cursor.execute("""
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            """)

            # Research results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_results (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    campaign_id UUID,
                    query TEXT NOT NULL,
                    source TEXT,
                    results JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    CONSTRAINT fk_campaign FOREIGN KEY (campaign_id)
                        REFERENCES campaigns(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_research_campaign
                    ON research_results(campaign_id);
                CREATE INDEX IF NOT EXISTS idx_research_created
                    ON research_results(created_at);
            """)

            # Content analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_analysis (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    content_id UUID,
                    analysis_type VARCHAR(50) NOT NULL,
                    results JSONB NOT NULL,
                    sentiment_score NUMERIC,
                    topics JSONB,
                    entities JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_analysis_content
                    ON content_analysis(content_id);
                CREATE INDEX IF NOT EXISTS idx_analysis_type
                    ON content_analysis(analysis_type);
            """)

            # Agent outputs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_outputs (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    agent_name VARCHAR(100) NOT NULL,
                    campaign_id UUID,
                    input JSONB,
                    output JSONB NOT NULL,
                    execution_time NUMERIC,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    CONSTRAINT fk_campaign FOREIGN KEY (campaign_id)
                        REFERENCES campaigns(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_agent_outputs_campaign
                    ON agent_outputs(campaign_id);
                CREATE INDEX IF NOT EXISTS idx_agent_outputs_agent
                    ON agent_outputs(agent_name);
                CREATE INDEX IF NOT EXISTS idx_agent_outputs_created
                    ON agent_outputs(created_at);
            """)

            # Market insights table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_insights (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    campaign_id UUID NOT NULL,
                    segment VARCHAR(255),
                    insights_json JSONB NOT NULL,
                    confidence_score DECIMAL(5,2),
                    source VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW(),
                    CONSTRAINT fk_campaign FOREIGN KEY (campaign_id)
                        REFERENCES campaigns(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_insights_campaign
                    ON market_insights(campaign_id);
                CREATE INDEX IF NOT EXISTS idx_insights_segment
                    ON market_insights(segment);
            """)

            # Trends table (already exists but adding if not)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trends (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    topic VARCHAR(255) NOT NULL,
                    score DECIMAL(10,2),
                    category VARCHAR(100),
                    source VARCHAR(100),
                    metadata_json JSONB,
                    detected_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_trends_topic
                    ON trends(topic);
                CREATE INDEX IF NOT EXISTS idx_trends_detected
                    ON trends(detected_at);
                CREATE INDEX IF NOT EXISTS idx_trends_score
                    ON trends(score DESC);
            """)

            conn.commit()
            logger.info("storage_tables_created")

        except Exception as e:
            conn.rollback()
            logger.error("table_creation_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    # === Research Results ===

    def store_research_result(
        self,
        query: str,
        results: Dict[str, Any],
        campaign_id: Optional[str] = None,
        source: Optional[str] = None
    ) -> str:
        """
        Store research results

        Args:
            query: Search query
            results: Research results (dict)
            campaign_id: Optional campaign ID
            source: Source of results (searxng, web_scraper, etc.)

        Returns:
            ID of stored result
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO research_results (campaign_id, query, source, results)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (campaign_id, query, source, Json(results)))

            result_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                "research_result_stored",
                result_id=str(result_id),
                query=query,
                source=source
            )

            return str(result_id)

        except Exception as e:
            conn.rollback()
            logger.error("research_storage_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    def get_research_results(
        self,
        campaign_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve research results

        Args:
            campaign_id: Optional campaign ID filter
            limit: Maximum results to return

        Returns:
            List of research results
        """
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            if campaign_id:
                cursor.execute("""
                    SELECT * FROM research_results
                    WHERE campaign_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (campaign_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM research_results
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        finally:
            self.pool.putconn(conn)

    # === Content Analysis ===

    def store_content_analysis(
        self,
        content_id: str,
        analysis_type: str,
        results: Dict[str, Any],
        sentiment_score: Optional[float] = None,
        topics: Optional[List[Dict[str, Any]]] = None,
        entities: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """
        Store content analysis results

        Args:
            content_id: ID of analyzed content
            analysis_type: Type of analysis (sentiment, ner, topic, etc.)
            results: Analysis results (dict)
            sentiment_score: Optional sentiment score
            topics: Optional extracted topics
            entities: Optional extracted entities

        Returns:
            ID of stored analysis
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO content_analysis (
                    content_id, analysis_type, results,
                    sentiment_score, topics, entities
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                content_id,
                analysis_type,
                Json(results),
                sentiment_score,
                Json(topics) if topics else None,
                Json(entities) if entities else None
            ))

            analysis_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                "content_analysis_stored",
                analysis_id=str(analysis_id),
                content_id=content_id,
                analysis_type=analysis_type
            )

            return str(analysis_id)

        except Exception as e:
            conn.rollback()
            logger.error("analysis_storage_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    # === Agent Outputs ===

    def store_agent_output(
        self,
        agent_name: str,
        output: Dict[str, Any],
        campaign_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """
        Store agent execution output

        Args:
            agent_name: Name of the agent
            output: Agent output (dict)
            campaign_id: Optional campaign ID
            input_data: Optional agent input
            execution_time: Execution time in seconds
            success: Whether execution succeeded
            error_message: Optional error message

        Returns:
            ID of stored output
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO agent_outputs (
                    agent_name, campaign_id, input, output,
                    execution_time, success, error_message
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                agent_name,
                campaign_id,
                Json(input_data) if input_data else None,
                Json(output),
                execution_time,
                success,
                error_message
            ))

            output_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                "agent_output_stored",
                output_id=str(output_id),
                agent_name=agent_name,
                success=success
            )

            return str(output_id)

        except Exception as e:
            conn.rollback()
            logger.error("agent_output_storage_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    def get_agent_outputs(
        self,
        agent_name: Optional[str] = None,
        campaign_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve agent outputs

        Args:
            agent_name: Optional agent name filter
            campaign_id: Optional campaign ID filter
            limit: Maximum results to return

        Returns:
            List of agent outputs
        """
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            query = "SELECT * FROM agent_outputs WHERE 1=1"
            params = []

            if agent_name:
                query += " AND agent_name = %s"
                params.append(agent_name)

            if campaign_id:
                query += " AND campaign_id = %s"
                params.append(campaign_id)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)

            results = cursor.fetchall()
            return [dict(row) for row in results]

        finally:
            self.pool.putconn(conn)

    # === Market Insights ===

    def store_market_insight(
        self,
        campaign_id: str,
        insights: Dict[str, Any],
        segment: Optional[str] = None,
        confidence_score: Optional[float] = None,
        source: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> str:
        """
        Store market insights

        Args:
            campaign_id: Campaign ID
            insights: Insights data (dict)
            segment: Market segment
            confidence_score: Confidence score
            sources: List of data sources

        Returns:
            ID of stored insight
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            insights_payload = dict(insights or {})
            if sources:
                insights_payload["sources"] = sources

            cursor.execute(
                """
                INSERT INTO market_insights (
                    campaign_id, segment, insights_json,
                    confidence_score, source
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    campaign_id,
                    segment,
                    Json(insights_payload),
                    confidence_score,
                    source,
                ),
            )

            insight_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                "market_insight_stored",
                insight_id=str(insight_id),
                campaign_id=campaign_id,
                segment=segment
            )

            return str(insight_id)

        except Exception as e:
            conn.rollback()
            logger.error("insight_storage_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    # === Trends ===

    def store_trend(
        self,
        topic: str,
        score: float,
        category: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store detected trend

        Args:
            topic: Trend topic
            score: Trend score
            source: Data source
            metadata: Additional metadata

        Returns:
            ID of stored trend
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO trends (topic, score, category, source, metadata_json)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """,
                (
                    topic,
                    score,
                    category,
                    source,
                    Json(metadata) if metadata else None,
                ),
            )

            trend_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                "trend_stored",
                trend_id=str(trend_id),
                topic=topic,
                score=score
            )

            return str(trend_id)

        except Exception as e:
            conn.rollback()
            logger.error("trend_storage_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    def get_trending_topics(
        self,
        limit: int = 20,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get trending topics

        Args:
            limit: Maximum results
            min_score: Minimum trend score

        Returns:
            List of trending topics
        """
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute("""
                SELECT topic, AVG(score) as avg_score,
                       COUNT(*) as mention_count,
                       MAX(detected_at) as last_detected
                FROM trends
                WHERE score >= %s
                GROUP BY topic
                ORDER BY avg_score DESC, mention_count DESC
                LIMIT %s
            """, (min_score, limit))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        finally:
            self.pool.putconn(conn)

    # === Media Assets ===

    def save_media_asset(
        self,
        draft_id: Optional[str],
        asset_type: str,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        prompt: Optional[str] = None,
        provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cost: Optional[float] = None
    ) -> str:
        """
        Save media asset to database

        Args:
            draft_id: Optional draft ID (UUID)
            asset_type: Type of asset (image, video)
            file_path: Local file path
            url: Remote URL
            prompt: Generation prompt
            provider: API provider (dalle3, midjourney, runway, pika, etc.)
            metadata: Additional metadata (dimensions, duration, format, etc.)
            cost: Generation cost

        Returns:
            Asset ID (UUID string)
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO media_assets (
                    draft_id, type, file_path, url, prompt,
                    api_provider, metadata_json, generation_cost
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                draft_id,
                asset_type,
                file_path,
                url,
                prompt,
                provider,
                Json(metadata) if metadata else None,
                cost
            ))

            asset_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                "media_asset_saved",
                asset_id=asset_id,
                asset_type=asset_type,
                provider=provider,
                file_path=file_path
            )

            return str(asset_id)

        except Exception as e:
            conn.rollback()
            logger.error("media_asset_save_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    def save_media_edit(
        self,
        asset_id: str,
        edit_type: str,
        parameters: Dict[str, Any],
        result_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save media edit (music/watermark) to database

        Args:
            asset_id: ID of the media asset being edited
            edit_type: Type of edit (music, watermark)
            parameters: Edit parameters (music file, watermark settings, etc.)
            result_path: Path to the edited file (stored as edited_file_path)
            metadata: Optional additional metadata (stored in edit_params)

        Returns:
            Edit ID (UUID string)
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            edit_params: Dict[str, Any] = {"parameters": parameters or {}}      
            if metadata:
                edit_params["metadata"] = metadata

            cursor.execute(
                """
                INSERT INTO media_edits (
                    asset_id, edit_type, edit_params, edited_file_path
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """,
                (
                    asset_id,
                    edit_type,
                    Json(edit_params),
                    result_path,
                ),
            )

            edit_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                "media_edit_saved",
                edit_id=edit_id,
                asset_id=asset_id,
                edit_type=edit_type
            )

            return str(edit_id)

        except Exception as e:
            conn.rollback()
            logger.error("media_edit_save_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    def close(self):
        """Close connection pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("postgres_storage_closed")


# === Factory Function ===

def create_storage() -> PostgreSQLStorage:
    """Create PostgreSQL storage instance"""
    return PostgreSQLStorage()
