"""Models for the API responses"""
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field


class CollectionData(BaseModel):
    """Model for collection data."""
    id: Union[str, int]  # Accept both string and integer for id
    alias: str
    name: str

class DvResponse(BaseModel):
    """Model for the collections tree response."""
    status: str
    data: dict

class CollectionsTreeResponseData(BaseModel):
    """Model for the collections tree response data."""
    status: str
    data: Optional[CollectionData] = Field(default=None, description="The collections tree data")