from pydantic import BaseModel, HttpUrl, Field
from datetime import date

class DateFilterDTO(BaseModel):
    """
    Input DTO for receiving date filters in the request body.
    """
    start_date: date | None = Field(None, description="Filter for files modified on or after this date (YYYY-MM-DD).")
    end_date: date | None = Field(None, description="Filter for files modified on or before this date (YYYY-MM-DD).")

