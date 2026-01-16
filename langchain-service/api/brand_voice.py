"""
Brand Voice API Endpoints
FastAPI routes for brand voice profile management
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from storage.brand_voice_storage import create_brand_voice_storage
from analytics.brand_voice_analyzer import BrandVoiceAnalyzer

logger = structlog.get_logger()

# Initialize router
router = APIRouter(prefix="/brand-voice", tags=["Brand Voice"])

# Initialize storage
storage = create_brand_voice_storage()

# Pydantic models for request/response validation

class TrainProfileRequest(BaseModel):
    profile_name: str = Field(..., description="Name of the brand voice profile")
    example_content: List[str] = Field(..., description="List of example content pieces (10-20 recommended)", min_items=1)
    campaign_id: Optional[str] = Field(default=None, description="Optional campaign UUID to associate with")
    target_profile: Optional[Dict[str, float]] = Field(default=None, description="Optional target metrics for brand voice")


class UpdateProfileRequest(BaseModel):
    profile_name: Optional[str] = Field(default=None, description="New profile name")
    example_content: Optional[List[str]] = Field(default=None, description="New example content")
    retrain: bool = Field(default=False, description="Re-analyze content and recalculate profile")


class ImportProfileRequest(BaseModel):
    profile_data: Dict[str, Any] = Field(..., description="Exported profile data")
    campaign_id: Optional[str] = Field(default=None, description="Optional campaign UUID to associate with")


class SetCampaignProfileRequest(BaseModel):
    campaign_id: str = Field(..., description="Campaign UUID")
    profile_id: Optional[str] = Field(default=None, description="Profile UUID (null to unset)")


class ProfileResponse(BaseModel):
    id: str
    profile_name: str
    campaign_id: Optional[str]
    calculated_profile: Dict[str, Any]
    example_content: str
    created_at: datetime


class TrainProfileResponse(BaseModel):
    profile_id: str
    profile_name: str
    calculated_profile: Dict[str, Any]
    consistency_score: float
    recommendations: List[str]
    created_at: datetime


# === Training Endpoints ===

@router.post("/train", response_model=TrainProfileResponse, status_code=status.HTTP_201_CREATED)
async def train_profile(request: TrainProfileRequest):
    """
    Train a new brand voice profile from example content.

    Analyzes 10-20 pieces of example content to extract:
    - Readability metrics (Flesch-Kincaid, Gunning Fog, etc.)
    - Tone characteristics (formality, jargon density)
    - Sentence structure patterns
    - Vocabulary preferences

    Returns calculated profile with consistency metrics.
    """
    try:
        logger.info("training_brand_voice_profile", profile_name=request.profile_name, example_count=len(request.example_content))

        # Combine all example content
        combined_content = "\n\n".join(request.example_content)

        # Validate content length
        if len(combined_content.strip()) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Example content too short. Provide at least 100 characters total."
            )

        # Analyze brand voice
        analyzer = BrandVoiceAnalyzer(request.target_profile)

        # Calculate readability metrics
        readability = analyzer.calculate_readability_metrics(combined_content)

        # Analyze tone
        tone = analyzer.analyze_tone(combined_content)

        # Calculate consistency score
        consistency = analyzer.calculate_brand_consistency(combined_content, request.target_profile)

        # Combine into calculated profile
        calculated_profile = {
            "readability": readability,
            "tone": tone,
            "consistency": consistency,
            "target_metrics": request.target_profile or analyzer.targets,
            "analyzed_at": datetime.utcnow().isoformat(),
            "example_count": len(request.example_content),
            "total_words": tone.get("total_words", 0),
            "algorithm_version": "1.0.0"
        }

        # Store profile
        profile_id = storage.create_profile(
            profile_name=request.profile_name,
            example_content=combined_content,
            calculated_profile=calculated_profile,
            campaign_id=request.campaign_id
        )

        logger.info(
            "brand_voice_profile_trained",
            profile_id=profile_id,
            profile_name=request.profile_name,
            consistency_score=consistency.get("consistency_score", 0)
        )

        return TrainProfileResponse(
            profile_id=profile_id,
            profile_name=request.profile_name,
            calculated_profile=calculated_profile,
            consistency_score=consistency.get("consistency_score", 0),
            recommendations=consistency.get("recommendations", []),
            created_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("brand_voice_training_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to train brand voice profile: {str(e)}"
        )


# === Retrieval Endpoints ===

@router.get("/profiles", response_model=List[ProfileResponse])
async def list_profiles(
    campaign_id: Optional[str] = None,
    limit: int = 50
):
    """
    List all brand voice profiles.

    Optional filtering by campaign_id.
    """
    try:
        logger.info("listing_brand_voice_profiles", campaign_id=campaign_id, limit=limit)

        if campaign_id:
            profiles = storage.get_profiles_by_campaign(campaign_id, limit)
        else:
            profiles = storage.list_all_profiles(limit)

        return [
            ProfileResponse(
                id=str(p["id"]),
                profile_name=p["profile_name"],
                campaign_id=str(p["campaign_id"]) if p["campaign_id"] else None,
                calculated_profile=p["calculated_profile"],
                example_content=p["example_content"],
                created_at=p["created_at"]
            )
            for p in profiles
        ]

    except Exception as e:
        logger.error("brand_voice_list_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list profiles: {str(e)}"
        )


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str):
    """
    Get a specific brand voice profile by ID.
    """
    try:
        logger.info("getting_brand_voice_profile", profile_id=profile_id)

        profile = storage.get_profile(profile_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found"
            )

        return ProfileResponse(
            id=str(profile["id"]),
            profile_name=profile["profile_name"],
            campaign_id=str(profile["campaign_id"]) if profile["campaign_id"] else None,
            calculated_profile=profile["calculated_profile"],
            example_content=profile["example_content"],
            created_at=profile["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("brand_voice_get_error", error=str(e), profile_id=profile_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )


@router.get("/profiles/name/{profile_name}", response_model=ProfileResponse)
async def get_profile_by_name(
    profile_name: str,
    campaign_id: Optional[str] = None
):
    """
    Get a brand voice profile by name.

    Optional filtering by campaign_id.
    """
    try:
        logger.info("getting_brand_voice_profile_by_name", profile_name=profile_name, campaign_id=campaign_id)

        profile = storage.get_profile_by_name(profile_name, campaign_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_name}' not found"
            )

        return ProfileResponse(
            id=str(profile["id"]),
            profile_name=profile["profile_name"],
            campaign_id=str(profile["campaign_id"]) if profile["campaign_id"] else None,
            calculated_profile=profile["calculated_profile"],
            example_content=profile["example_content"],
            created_at=profile["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("brand_voice_get_by_name_error", error=str(e), profile_name=profile_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile by name: {str(e)}"
        )


# === Update Endpoints ===

@router.patch("/profiles/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: str, request: UpdateProfileRequest):
    """
    Update a brand voice profile.

    Can update name, example content, and optionally retrain.
    """
    try:
        logger.info("updating_brand_voice_profile", profile_id=profile_id, retrain=request.retrain)

        # Check if profile exists
        profile = storage.get_profile(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found"
            )

        # If retraining, recalculate profile
        calculated_profile = None
        if request.retrain and request.example_content:
            combined_content = "\n\n".join(request.example_content)

            analyzer = BrandVoiceAnalyzer()
            readability = analyzer.calculate_readability_metrics(combined_content)
            tone = analyzer.analyze_tone(combined_content)
            consistency = analyzer.calculate_brand_consistency(combined_content)

            calculated_profile = {
                "readability": readability,
                "tone": tone,
                "consistency": consistency,
                "target_metrics": analyzer.targets,
                "analyzed_at": datetime.utcnow().isoformat(),
                "example_count": len(request.example_content),
                "total_words": tone.get("total_words", 0),
                "algorithm_version": "1.0.0"
            }

        # Update profile
        example_content = "\n\n".join(request.example_content) if request.example_content else None

        storage.update_profile(
            profile_id=profile_id,
            profile_name=request.profile_name,
            example_content=example_content,
            calculated_profile=calculated_profile
        )

        # Get updated profile
        updated_profile = storage.get_profile(profile_id)

        return ProfileResponse(
            id=str(updated_profile["id"]),
            profile_name=updated_profile["profile_name"],
            campaign_id=str(updated_profile["campaign_id"]) if updated_profile["campaign_id"] else None,
            calculated_profile=updated_profile["calculated_profile"],
            example_content=updated_profile["example_content"],
            created_at=updated_profile["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("brand_voice_update_error", error=str(e), profile_id=profile_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


# === Delete Endpoints ===

@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: str):
    """
    Delete a brand voice profile.
    """
    try:
        logger.info("deleting_brand_voice_profile", profile_id=profile_id)

        deleted = storage.delete_profile(profile_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("brand_voice_delete_error", error=str(e), profile_id=profile_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


# === Export/Import Endpoints ===

@router.get("/profiles/{profile_id}/export")
async def export_profile(profile_id: str) -> Dict[str, Any]:
    """
    Export a brand voice profile as JSON.

    Returns complete profile data for backup/sharing.
    """
    try:
        logger.info("exporting_brand_voice_profile", profile_id=profile_id)

        profile = storage.get_profile(profile_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found"
            )

        # Convert UUID to string for JSON serialization
        export_data = {
            "profile_name": profile["profile_name"],
            "example_content": profile["example_content"],
            "calculated_profile": profile["calculated_profile"],
            "exported_at": datetime.utcnow().isoformat(),
            "export_version": "1.0.0"
        }

        logger.info("brand_voice_profile_exported", profile_id=profile_id)

        return export_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error("brand_voice_export_error", error=str(e), profile_id=profile_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export profile: {str(e)}"
        )


@router.post("/import", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def import_profile(request: ImportProfileRequest):
    """
    Import a brand voice profile from exported JSON.

    Creates a new profile from previously exported data.
    """
    try:
        logger.info("importing_brand_voice_profile", profile_name=request.profile_data.get("profile_name"))

        # Validate required fields
        required_fields = ["profile_name", "example_content", "calculated_profile"]
        for field in required_fields:
            if field not in request.profile_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )

        # Create profile
        profile_id = storage.create_profile(
            profile_name=request.profile_data["profile_name"],
            example_content=request.profile_data["example_content"],
            calculated_profile=request.profile_data["calculated_profile"],
            campaign_id=request.campaign_id
        )

        # Get created profile
        profile = storage.get_profile(profile_id)

        logger.info("brand_voice_profile_imported", profile_id=profile_id)

        return ProfileResponse(
            id=str(profile["id"]),
            profile_name=profile["profile_name"],
            campaign_id=str(profile["campaign_id"]) if profile["campaign_id"] else None,
            calculated_profile=profile["calculated_profile"],
            example_content=profile["example_content"],
            created_at=profile["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("brand_voice_import_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import profile: {str(e)}"
        )


# === Campaign Integration Endpoints ===

@router.post("/campaigns/set-profile", status_code=status.HTTP_200_OK)
async def set_campaign_profile(request: SetCampaignProfileRequest):
    """
    Set the active brand voice profile for a campaign.

    Pass null profile_id to unset.
    """
    try:
        logger.info(
            "setting_campaign_voice_profile",
            campaign_id=request.campaign_id,
            profile_id=request.profile_id
        )

        # Verify profile exists if not null
        if request.profile_id:
            profile = storage.get_profile(request.profile_id)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Profile {request.profile_id} not found"
                )

        # Set campaign profile
        updated = storage.set_campaign_voice_profile(
            campaign_id=request.campaign_id,
            profile_id=request.profile_id
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {request.campaign_id} not found"
            )

        return {
            "status": "success",
            "campaign_id": request.campaign_id,
            "profile_id": request.profile_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("campaign_voice_profile_set_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set campaign profile: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}/active-profile", response_model=Optional[ProfileResponse])
async def get_campaign_active_profile(campaign_id: str):
    """
    Get the active brand voice profile for a campaign.

    Returns null if no profile is set.
    """
    try:
        logger.info("getting_campaign_active_profile", campaign_id=campaign_id)

        profile = storage.get_campaign_active_profile(campaign_id)

        if not profile:
            return None

        return ProfileResponse(
            id=str(profile["id"]),
            profile_name=profile["profile_name"],
            campaign_id=str(profile["campaign_id"]) if profile["campaign_id"] else None,
            calculated_profile=profile["calculated_profile"],
            example_content=profile["example_content"],
            created_at=profile["created_at"]
        )

    except Exception as e:
        logger.error("campaign_active_profile_get_error", error=str(e), campaign_id=campaign_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign active profile: {str(e)}"
        )
