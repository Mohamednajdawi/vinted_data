from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/v1", tags=["Vindy Extension API"])

# Mock Authentication Dependency
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        # Typically would verify JWT from Supabase here
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Extract token
    token = authorization.split(" ")[1]
    return {"user_id": "mock_user_id_from_token", "token": token}


# --- Models ---

class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]
    version: int

class LikeItem(BaseModel):
    product_id: str
    vinted_user_id: str

class CheckLikesRequest(BaseModel):
    likes: List[LikeItem]

class LinkAccountRequest(BaseModel):
    vinted_domain: str
    vinted_user_id: int
    vinted_username: Optional[str] = None
    profile_photo_url: Optional[str] = None
    country_code: Optional[str] = None
    locale: Optional[str] = None
    iso_locale_code: Optional[str] = None
    currency: Optional[str] = None

class OnboardingStep(BaseModel):
    step: str

class FeatureIncrement(BaseModel):
    feature: str
    increment: int = 1

class AICreditsAction(BaseModel):
    items: List[str]

class AnalyticsEvent(BaseModel):
    user_id: str
    action: str
    timestamp: str
    details: Dict[str, Any] = {}

class ClassifyGarment(BaseModel):
    image_base64: str
    mime_type: str

class ClassifyGarmentsBatch(BaseModel):
    images: List[ClassifyGarment]

class StageGarment(BaseModel):
    image_base64: str
    mime_type: str
    mode: str
    category: str
    side: str
    background: str
    model_options: Optional[Dict[str, Any]] = None
    credits_pre_reserved: bool = False

class ProcessImage(BaseModel):
    image_urls: List[str]
    image_url: str
    remove_background: bool = False
    add_background: bool = False
    background_style: Optional[str] = None
    custom_prompt: Optional[str] = None
    center_product: bool = False

class AnalyzeProductImages(BaseModel):
    photo_urls: List[str]
    domain: str
    user_locale: Optional[str] = None

class GenerateDescription(BaseModel):
    product: Dict[str, Any]
    additional_notes: str = ""
    user_locale: Optional[str] = None

class CreatePaymentLink(BaseModel):
    price_id: str
    plan_name: str
    success_url: str
    cancel_url: str


# --- Endpoints ---

@router.get("/user_settings")
async def get_user_settings(user: dict = Depends(get_current_user)):
    return {"settings": {}, "version": 1}

@router.put("/user_settings")
async def update_user_settings(data: SettingsUpdate, user: dict = Depends(get_current_user)):
    return {"success": True, "version": data.version + 1}

@router.post("/boost/check_community_likes")
async def check_community_likes(data: CheckLikesRequest, user: dict = Depends(get_current_user)):
    results = {f"{item.product_id}_{item.vinted_user_id}": False for item in data.likes}
    return {"success": True, "results": results}

@router.post("/link_vinted_account")
async def link_vinted_account(data: LinkAccountRequest, user: dict = Depends(get_current_user)):
    return {"success": True, "already_existed": False, "onboarding_step_completed": True}

@router.post("/onboarding/complete_step")
async def complete_onboarding_step(data: OnboardingStep, user: dict = Depends(get_current_user)):
    return {"success": True, "all_completed": False}

@router.get("/feature_status")
async def get_feature_status(user: dict = Depends(get_current_user)):
    return {
        "features": {
            "auto_follow": {"used_today": 0, "daily_limit": 100},
            "bump_item": {"used_today": 0, "daily_limit": 5},
            "aidescription": {"used_today": 0, "daily_limit": 10}
        }
    }

@router.post("/increment_feature")
async def increment_feature(data: FeatureIncrement, user: dict = Depends(get_current_user)):
    return {"success": True}

@router.get("/ai_credits")
async def get_ai_credits(user: dict = Depends(get_current_user)):
    return {"success": True, "onboarding_credit_available": True, "remaining": 50}

@router.post("/ai_credits/reserve")
async def reserve_ai_credits(data: AICreditsAction, user: dict = Depends(get_current_user)):
    return {"success": True, "remaining": 49}

@router.post("/ai_credits/refund")
async def refund_ai_credits(data: AICreditsAction, user: dict = Depends(get_current_user)):
    return {"success": True}

@router.post("/analisi")
async def submit_analytics(data: AnalyticsEvent, user: dict = Depends(get_current_user)):
    return {"success": True}

@router.post("/classify_garment")
async def classify_garment(data: ClassifyGarment, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "category": "T-Shirt",
        "side": "front",
        "view_type": "product",
        "has_bg": False,
        "raw": "Mock classification response"
    }

@router.post("/classify_garments_batch")
async def classify_garments_batch(data: ClassifyGarmentsBatch, user: dict = Depends(get_current_user)):
    return {
        "success": True, 
        "results": [{"success": True, "category": "Jeans"} for _ in data.images]
    }

@router.post("/stage_garment")
async def stage_garment(data: StageGarment, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "image_url": "https://example.com/mock_image.jpg",
        "image_base64": None,
        "credits_remaining": 48
    }

@router.post("/generate_virtual_model")
async def generate_virtual_model(data: Dict[str, Any], user: dict = Depends(get_current_user)):
    return {"success": True, "job_id": "mock_job_id_123"}

@router.get("/job_status/{job_id}")
async def get_job_status(job_id: str, user: dict = Depends(get_current_user)):
    return {
        "status": "completed",
        "results": {
            "image_urls": ["https://example.com/mock_processed.jpg"],
            "image_url": "https://example.com/mock_processed.jpg",
            "credits_used": 1,
            "credits_remaining": 47
        }
    }

@router.post("/process_image")
async def process_image(data: ProcessImage, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "image_url": "https://example.com/mock_processed.jpg",
        "image_urls": ["https://example.com/mock_processed.jpg"],
        "credits_used": 1,
        "credits_remaining": 47
    }

@router.post("/analyze_product_images")
async def analyze_product_images(data: AnalyzeProductImages, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "dominant_color": "blue",
            "style": "casual"
        }
    }

@router.post("/generate_description")
async def generate_description(data: GenerateDescription, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "description": "A wonderful mock item description generated by AI. Enjoy!"
    }

@router.get("/check_membership")
async def check_membership(user: dict = Depends(get_current_user)):
    return {
        "hasAccess": True,
        "plan": "premium",
        "isPremium": True,
        "status": "active",
        "stripe_product_id": "prod_mock123",
        "trial": None,
        "has_billing_account": True
    }

@router.post("/create_payment_link")
async def create_payment_link(data: CreatePaymentLink, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "url": "https://checkout.stripe.com/mock_link"
    }
