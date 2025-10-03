from typing import List, Optional
from fastapi import File, Form, UploadFile
from pydantic import BaseModel, Field

# ---------- Value Objects ----------

class MarketPlan(BaseModel):
    market_plan_key: str = Field(..., alias="marketPlanKey")
    market_plan_image_url: Optional[str] = Field(None, alias="marketPlanImageUrl")

    model_config = {
        "populate_by_name": True,
        "extra": "ignore"
    }


class Log(BaseModel):
    name: str
    size: str
    price: float
    user_id: str = Field(..., alias="userID")          # vendor ID (FK)
    reservation_id: str = Field(..., alias="reservationID")

    model_config = {
        "populate_by_name": True,
        "extra": "ignore"
    }

# ---------- Aggregate Root ----------
class Market(BaseModel):   
    id: str
    market_name: Optional[str] = Field(None, alias="marketName")
    address: Optional[str] = None
    cover_image_key: Optional[str] = Field(None, alias="coverImageKey")
    market_plan_keys: Optional[List[MarketPlan]] = Field(default_factory=list, alias="marketPlanKeys")
    logs: List[Log] = Field(default_factory=list)
    detail: Optional[str] = None
    rule: Optional[str] = None
    user_id: Optional[str] = Field(None, alias="userid")
    cover_image_url: Optional[str] = Field(None, alias="coverImageUrl")
    isOpen: Optional[bool] = None
    marketType: Optional[str] = None

    model_config = {
        "populate_by_name": True,   # allow using pythonic names in code
        "extra": "ignore"           # ignore unknown props from NoSQL docs
    }
    
# ---------- Aggregate Root ----------
class MarketSearchResponse(BaseModel):   
    market: List[Market]
    total_count: int
    limit:int
    

# ---------- Simple wrappers ----------

class MarketId(BaseModel):
    id: str


class MarketList(BaseModel):
    markets: List[Market] = []
