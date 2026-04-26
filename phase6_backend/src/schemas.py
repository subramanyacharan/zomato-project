from pydantic import BaseModel, Field
from typing import Optional, List, Any

class RecommendationRequest(BaseModel):
    location: str = Field(..., description="City or locality")
    budget: str = Field(..., description="low, medium, or high")
    cuisine: Optional[str] = Field(None, description="Preferred cuisine")
    minimum_rating: Optional[float] = Field(None, ge=0, le=5)
    top_n: int = Field(5, ge=1, le=50)
    mock: bool = Field(False, description="Run without actual Groq API call")

class RestaurantRecommendation(BaseModel):
    rank: int
    restaurant_name: str
    location: Optional[str]
    cuisines: Optional[str]
    cost_for_two: Optional[float]
    rating: Optional[float]
    tags: Optional[str]
    llm_reason: str
    llm_summary: str

class RecommendationResponse(BaseModel):
    success: bool
    recommendations: List[RestaurantRecommendation]
    warnings: List[str]
    errors: List[str]
    metadata: dict[str, Any]
