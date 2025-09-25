from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime

class ReservoirResponseDTO(BaseModel):
    """Simple DTO for reservoir response"""
    data: List[Dict[str, Any]]
    total_records: int
    page: int
    page_size: int    
   