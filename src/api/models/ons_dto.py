from pydantic import BaseModel, Field


# add option to get data by another url
# add option to save in another bucket
class DateFilterDTO(BaseModel):
    """
    Input DTO for receiving date filters in the request body.
    """

    start_year: int | None = Field(
        None, description="Filter for files modified on or after this year (YYYY)."
    )
    end_year: int | None = Field(
        None, description="Filter for files modified on or before this year (YYYY)."
    )
    package: str | None = Field(None, description="Package name to filter resources.")

    bucket: str | None = Field(None, description="GCS bucket to save files.")
