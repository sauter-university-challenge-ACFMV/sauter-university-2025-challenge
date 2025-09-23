from pydantic import BaseModel, HttpUrl, Field
from datetime import date

# add option to get data by another url
# add option to save in another bucket
class DateFilterDTO(BaseModel):
    """
    Input DTO for receiving date filters in the request body.
    """
    start_year: int | None = Field(None, description="Filter for files modified on or after this date (YYYY-MM-DD).")
    end_year: int | None = Field(None, description="Filter for files modified on or before this date (YYYY-MM-DD).")
    package: str | None = Field(None, description="Package name to filter resources.")
    data_type: str | None = Field(None, description="Type of data to filter ('parquet', 'csv' or 'xlsx').")

