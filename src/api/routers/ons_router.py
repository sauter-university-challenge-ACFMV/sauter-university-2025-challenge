from fastapi import APIRouter, HTTPException, Body
from models.ons_dto import DateFilterDTO, ParquetFilesResponse
from services.ons_service import fetch_and_filter_parquet_files
import httpx

router = APIRouter(
    prefix="/ons",
    tags=["ONS Data"]
)

@router.post(
    "/filter-parquet-files",
    response_model=ParquetFilesResponse,
    summary="Filter ONS PARQUET Files",
    description="Fetches and filters a list of PARQUET file resources from the ONS API based on dates provided in the request body."
)
async def filter_ons_parquet_files_endpoint(
    filters: DateFilterDTO = Body(...)
) -> ParquetFilesResponse:
    """
    API Endpoint to filter ONS Parquet files.
    This function handles the HTTP request/response and calls the service layer.
    """
    try:
        filtered_files = await fetch_and_filter_parquet_files(filters)
        return ParquetFilesResponse(parquet_files=filtered_files)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Error requesting ONS API: {exc}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"ONS API returned an error: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(exc)}")
