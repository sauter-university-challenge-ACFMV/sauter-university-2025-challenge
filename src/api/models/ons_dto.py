from pydantic import BaseModel, HttpUrl, Field
from datetime import date

class DateFilterDTO(BaseModel):
    """
    Input DTO for receiving date filters in the request body.
    """
    start_date: date | None = Field(None, description="Filter for files modified on or after this date (YYYY-MM-DD).")
    end_date: date | None = Field(None, description="Filter for files modified on or before this date (YYYY-MM-DD).")

class ParquetResourceDTO(BaseModel):
    """
    Data Transfer Object representing a single PARQUET file resource.
    """
    name: str | None = Field(None, description="The name of the resource file.")
    url: HttpUrl = Field(..., description="Direct download URL for the PARQUET file.")
    description: str | None = Field(None, description="Description of the resource.")
    last_modified: str | None = Field(None, description="ISO timestamp of the last modification.")
    size: int | None = Field(None, description="File size in bytes.")

class ParquetFilesResponse(BaseModel):
    """
    The response model for the endpoint, containing a list of parquet files.
    """
    parquet_files: list[ParquetResourceDTO]
