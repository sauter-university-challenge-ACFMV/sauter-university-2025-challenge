from fastapi import APIRouter, HTTPException, Body, status
from models.ons_dto import DateFilterDTO
import httpx
from services.ons_service import OnsService, ProcessResponse
from pydantic import BaseModel
from typing import Dict, Any, List


class ApiResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any] | None = None


class OnsRouter:
    def __init__(self, service: OnsService | None = None) -> None:
        self.service = service or OnsService()
        self.router = APIRouter(prefix="/ons", tags=["ONS Data"])
        self._register_routes()

    def _register_routes(self) -> None:
        @self.router.post(
            "/filter-parquet-files",
            response_model=ApiResponse,
            status_code=200,
            summary="Filter ONS PARQUET Files",
            description=(
                "Fetches and filters a list of PARQUET file resources from the ONS API "
                "based on dates provided in the request body. Returns detailed success/failure information."
            ),
            responses={
                200: {
                    "description": "All files processed successfully or partial success",
                    "content": {
                        "application/json": {
                            "examples": {
                                "all_success": {
                                    "summary": "All files processed successfully",
                                    "value": {
                                        "status": "success",
                                        "message": "All 3 files processed successfully",
                                        "data": {
                                            "success_downloads": [
                                                {
                                                    "url": "https://example.com/file1.parquet",
                                                    "year": 2021,
                                                    "package": "ear-diario-por-reservatorio",
                                                    "data_type": "parquet",
                                                    "gcs_path": "ear-diario-por-reservatorio/2021/file1.parquet",
                                                    "bucket": "my-bucket"
                                                }
                                            ],
                                            "failed_downloads": [],
                                            "total_processed": 3,
                                            "success_count": 3,
                                            "failure_count": 0
                                        }
                                    }
                                },
                                "partial_success": {
                                    "summary": "Some files failed to process",
                                    "value": {
                                        "status": "partial_success",
                                        "message": "Partial success: 2/3 files processed successfully",
                                        "data": {
                                            "success_downloads": [],
                                            "failed_downloads": [
                                                {
                                                    "url": "https://example.com/file3.parquet",
                                                    "year": 2023,
                                                    "package": "ear-diario-por-reservatorio",
                                                    "data_type": "parquet",
                                                    "error_message": "Failed to fetch URL: HTTP 404",
                                                    "gcs_path": "",
                                                    "bucket": "my-bucket"
                                                }
                                            ],
                                            "total_processed": 3,
                                            "success_count": 2,
                                            "failure_count": 1
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                400: {
                    "description": "Bad request - configuration error",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "error",
                                "message": "ONS_API_URL environment variable not set",
                                "data": {
                                    "error_type": "configuration_error"
                                }
                            }
                        }
                    }
                },
                422: {
                    "description": "All files failed to process",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "failed",
                                "message": "All 3 files failed to process",
                                "data": {
                                    "success_downloads": [],
                                    "failed_downloads": [
                                        {
                                            "url": "https://example.com/file1.parquet",
                                            "year": 2021,
                                            "package": "ear-diario-por-reservatorio",
                                            "data_type": "parquet",
                                            "error_message": "Data already exists in the raw table",
                                            "gcs_path": "ear-diario-por-reservatorio/2021/file1.parquet",
                                            "bucket": "my-bucket"
                                        }
                                    ],
                                    "total_processed": 3,
                                    "success_count": 0,
                                    "failure_count": 3
                                }
                            }
                        }
                    }
                },
                500: {"description": "Internal server error"},
                503: {"description": "Service unavailable - ONS API error"}
            }
        )
        async def filter_ons_parquet_files_endpoint(
            filters: DateFilterDTO = Body(...)
        ) -> ApiResponse:
            """
            API Endpoint to filter and process ONS Parquet files.
            
            Returns detailed information about successful and failed downloads,
            with appropriate HTTP status codes based on the outcome.
            """
            try:
                result: ProcessResponse = await self.service.process_reservoir_data(filters)
                
                # Determine response based on results
                if result.failure_count == 0:
                    # All successful
                    return ApiResponse(
                        status="success",
                        message=f"All {result.total_processed} files processed successfully",
                        data={
                            "success_downloads": result.success_downloads,
                            "failed_downloads": result.failed_downloads,
                            "total_processed": result.total_processed,
                            "success_count": result.success_count,
                            "failure_count": result.failure_count,
                        }
                    )
                elif result.success_count == 0:
                    # All failed
                    return ApiResponse(
                        status="failed",
                        message=f"All {result.total_processed} files failed to process",
                        data={
                            "success_downloads": result.success_downloads,
                            "failed_downloads": result.failed_downloads,
                            "total_processed": result.total_processed,
                            "success_count": result.success_count,
                            "failure_count": result.failure_count,
                        }
                    )
                else:
                    # Partial success
                    return ApiResponse(
                        status="partial_success",
                        message=f"Partial success: {result.success_count}/{result.total_processed} files processed successfully",
                        data={
                            "success_downloads": result.success_downloads,
                            "failed_downloads": result.failed_downloads,
                            "total_processed": result.total_processed,
                            "success_count": result.success_count,
                            "failure_count": result.failure_count,
                        }
                    )
            
            except ValueError as exc:
                # Configuration errors (missing env vars, invalid parameters)
                return ApiResponse(
                    status="error",
                    message=str(exc),
                    data={"error_type": "configuration_error"}
                )
            
            except httpx.RequestError as exc:
                # Network/connection errors to ONS API
                return ApiResponse(
                    status="error",
                    message=f"Error requesting ONS API: {exc}",
                    data={"error_type": "network_error"}
                )
            
            except httpx.HTTPStatusError as exc:
                # ONS API returned an error status
                return ApiResponse(
                    status="error",
                    message=f"ONS API returned an error: {exc}",
                    data={
                        "error_type": "api_error",
                        "api_status_code": exc.response.status_code
                    }
                )
            
            except Exception as exc:
                # Unexpected errors
                return ApiResponse(
                    status="error",
                    message=f"An unexpected error occurred: {str(exc)}",
                    data={"error_type": "internal_error"}
                )


def create_router() -> APIRouter:
    return OnsRouter().router