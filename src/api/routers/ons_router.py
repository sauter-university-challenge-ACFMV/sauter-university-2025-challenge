from fastapi import APIRouter, HTTPException, Body
from models.ons_dto import DateFilterDTO
import httpx
from fastapi import APIRouter, HTTPException
from services.ons_service import OnsService

router = APIRouter(
    prefix="/ons",
    tags=["ONS Data"]
)

service = OnsService()

# @router.post("/upload")
# async def upload(file: UploadFile = File(...)):
#     try:
#         url = service.save_file(file.file, file.filename, file.content_type)
#         return {"filename": file.filename, "url": url}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/filter-parquet-files",
    response_model=list[dict],
    summary="Filter ONS PARQUET Files",
    description="Fetches and filters a list of PARQUET file resources from the ONS API based on dates provided in the request body."
)
async def filter_ons_parquet_files_endpoint(
    filters: DateFilterDTO = Body(...)
) -> list[dict]:
    """
    API Endpoint to filter ONS Parquet files.
    This function handles the HTTP request/response and calls the service layer.
    """
    try:
        filtered_files = await service.process_reservoir_data(filters)
        return filtered_files
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Error requesting ONS API: {exc}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"ONS API returned an error: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(exc)}")
