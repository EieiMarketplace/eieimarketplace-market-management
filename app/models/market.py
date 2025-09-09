from typing import Optional
from pydantic import BaseModel

class Market(BaseModel):
    id: str
    address: str
    detail: str

class MarketId(Market):
    id: str
