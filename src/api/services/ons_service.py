import os
import re
import httpx
from datetime import date
from models.ons_dto import DateFilterDTO, ParquetResourceDTO


async def fetch_and_filter_parquet_files(filters: DateFilterDTO) -> list[ParquetResourceDTO]:
    """
    Service layer function to handle the business logic of fetching and filtering data.
    """
    ons_api_url = os.environ.get("ONS_API_URL")

    if not ons_api_url:
        # In a real app, you might raise a custom service-layer exception here
        raise ValueError("ONS_API_URL environment variable not set.")

    async with httpx.AsyncClient() as client:
        response = await client.get(ons_api_url)
        response.raise_for_status()  # httpx will raise its own exceptions on failure
        data = response.json()

    result = data.get("result", {})
    all_resources = result.get("resources", [])
    
    # 1. Filter for PARQUET format
    parquet_resources = [
        r for r in all_resources 
        if r.get("format", "").upper() == "PARQUET" and r.get("url")
    ]

    # 2. Filter by date using the DTO from the request body
    start_date = filters.start_date
    end_date = filters.end_date

    if not start_date and not end_date:
        return [ParquetResourceDTO(**res) for res in parquet_resources]

    filtered_by_date = []
    for resource in parquet_resources:
        name = resource.get("name", "")
        match = re.search(r"\d{4}", name)
        if match:
            resource_year = int(match.group())
        else:
            continue
        if start_date.year <= resource_year and end_date.year <= resource_year:
            continue
        
        filtered_by_date.append(resource)

    # 3. Create a list of DTOs from the final filtered data
    return [ParquetResourceDTO(**res) for res in filtered_by_date]
