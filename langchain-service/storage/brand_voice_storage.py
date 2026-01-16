"""
Brand Voice Storage
Database operations for brand voice profiles
"""

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
import os

logger = structlog.get_logger()


class BrandVoiceStorage:
    """
    Brand Voice Profile storage manager

    Handles storage of:
    - Brand voice profiles
    - Training example content
    - Calculated voice characteristics
    - Profile metadata
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize Brand Voice storage

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

            logger.info("brand_voice_storage_initialized")

        except Exception as e:
            logger.error("brand_voice_storage_initialization_error", error=str(e))
            raise

    # === Create Operations ===

    def create_profile(
        self,
        profile_name: str,
        example_content: str,
        calculated_profile: Dict[str, Any],
        campaign_id: Optional[str] = None
    ) -> str:
        """
        Create a new brand voice profile

        Args:
            profile_name: Name of the brand voice profile
            example_content: Sample content used for training
            calculated_profile: AI-analyzed brand voice characteristics
            campaign_id: Optional campaign UUID

        Returns:
            UUID of created profile
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO brand_voice_profiles (
                    campaign_id, profile_name, example_content, calculated_profile
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                campaign_id,
                profile_name,
                example_content,
                Json(calculated_profile)
            ))

            profile_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                "brand_voice_profile_created",
                profile_id=profile_id,
                profile_name=profile_name,
                campaign_id=campaign_id
            )

            return str(profile_id)

        except Exception as e:
            conn.rollback()
            logger.error("brand_voice_profile_creation_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    # === Read Operations ===

    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a brand voice profile by ID

        Args:
            profile_id: UUID of the profile

        Returns:
            Profile data or None if not found
        """
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute("""
                SELECT * FROM brand_voice_profiles
                WHERE id = %s
            """, (profile_id,))

            result = cursor.fetchone()
            return dict(result) if result else None

        finally:
            self.pool.putconn(conn)

    def get_profiles_by_campaign(
        self,
        campaign_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all brand voice profiles for a campaign

        Args:
            campaign_id: Campaign UUID
            limit: Maximum results to return

        Returns:
            List of profile data
        """
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute("""
                SELECT * FROM brand_voice_profiles
                WHERE campaign_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (campaign_id, limit))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        finally:
            self.pool.putconn(conn)

    def get_profile_by_name(
        self,
        profile_name: str,
        campaign_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a brand voice profile by name

        Args:
            profile_name: Name of the profile
            campaign_id: Optional campaign UUID filter

        Returns:
            Profile data or None if not found
        """
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            if campaign_id:
                cursor.execute("""
                    SELECT * FROM brand_voice_profiles
                    WHERE profile_name = %s AND campaign_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (profile_name, campaign_id))
            else:
                cursor.execute("""
                    SELECT * FROM brand_voice_profiles
                    WHERE profile_name = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (profile_name,))

            result = cursor.fetchone()
            return dict(result) if result else None

        finally:
            self.pool.putconn(conn)

    def list_all_profiles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all brand voice profiles

        Args:
            limit: Maximum results to return

        Returns:
            List of profile data
        """
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute("""
                SELECT * FROM brand_voice_profiles
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        finally:
            self.pool.putconn(conn)

    # === Update Operations ===

    def update_profile(
        self,
        profile_id: str,
        profile_name: Optional[str] = None,
        example_content: Optional[str] = None,
        calculated_profile: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a brand voice profile

        Args:
            profile_id: UUID of the profile
            profile_name: Optional new profile name
            example_content: Optional new example content
            calculated_profile: Optional new calculated profile

        Returns:
            True if updated successfully
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            updates = []
            params = []

            if profile_name is not None:
                updates.append("profile_name = %s")
                params.append(profile_name)

            if example_content is not None:
                updates.append("example_content = %s")
                params.append(example_content)

            if calculated_profile is not None:
                updates.append("calculated_profile = %s")
                params.append(Json(calculated_profile))

            if not updates:
                return False

            params.append(profile_id)

            cursor.execute(f"""
                UPDATE brand_voice_profiles
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)

            updated = cursor.rowcount > 0
            conn.commit()

            if updated:
                logger.info(
                    "brand_voice_profile_updated",
                    profile_id=profile_id
                )

            return updated

        except Exception as e:
            conn.rollback()
            logger.error("brand_voice_profile_update_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    # === Delete Operations ===

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete a brand voice profile

        Args:
            profile_id: UUID of the profile

        Returns:
            True if deleted successfully
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM brand_voice_profiles
                WHERE id = %s
            """, (profile_id,))

            deleted = cursor.rowcount > 0
            conn.commit()

            if deleted:
                logger.info(
                    "brand_voice_profile_deleted",
                    profile_id=profile_id
                )

            return deleted

        except Exception as e:
            conn.rollback()
            logger.error("brand_voice_profile_deletion_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    # === Campaign Link Operations ===

    def set_campaign_voice_profile(
        self,
        campaign_id: str,
        profile_id: Optional[str]
    ) -> bool:
        """
        Set the active brand voice profile for a campaign

        Args:
            campaign_id: UUID of the campaign
            profile_id: UUID of the profile (None to unset)

        Returns:
            True if updated successfully
        """
        conn = self.pool.getconn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE campaigns
                SET brand_voice_profile_id = %s
                WHERE id = %s
            """, (profile_id, campaign_id))

            updated = cursor.rowcount > 0
            conn.commit()

            if updated:
                logger.info(
                    "campaign_voice_profile_set",
                    campaign_id=campaign_id,
                    profile_id=profile_id
                )

            return updated

        except Exception as e:
            conn.rollback()
            logger.error("campaign_voice_profile_set_error", error=str(e))
            raise

        finally:
            self.pool.putconn(conn)

    def get_campaign_active_profile(
        self,
        campaign_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the active brand voice profile for a campaign

        Args:
            campaign_id: UUID of the campaign

        Returns:
            Profile data or None if no profile is set
        """
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute("""
                SELECT bvp.*
                FROM brand_voice_profiles bvp
                JOIN campaigns c ON c.brand_voice_profile_id = bvp.id
                WHERE c.id = %s
            """, (campaign_id,))

            result = cursor.fetchone()
            return dict(result) if result else None

        finally:
            self.pool.putconn(conn)

    def close(self):
        """Close connection pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("brand_voice_storage_closed")


# === Factory Function ===

def create_brand_voice_storage() -> BrandVoiceStorage:
    """Create BrandVoiceStorage instance"""
    return BrandVoiceStorage()
