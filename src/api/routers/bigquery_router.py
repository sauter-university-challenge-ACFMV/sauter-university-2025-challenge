from fastapi import APIRouter, HTTPException, Query
from models.bigquery_dto import ReservoirResponseDTO
from services.bigquery_service import ReservoirService
from typing import Optional
from utils.logger import LogLevel, log
from datetime import date


class ReservoirRouter:
    def __init__(self, service: Optional[ReservoirService] = None) -> None:
        self.service = service or ReservoirService()
        self.router = APIRouter(prefix="/reservoir", tags=["Reservoir Data"])
        self._register_routes()

    def _register_routes(self) -> None:
        
        @self.router.get(
            "/data",
            response_model=ReservoirResponseDTO,
            summary="Get Reservoir Data by Date Range",
            description="Fetch reservoir data filtered by start and end date with pagination."
        )
        async def get_reservoir_data_endpoint(
            start_date: date = Query(..., description="Start date to filter (YYYY-MM-DD)"),
            end_date: date = Query(..., description="End date to filter (YYYY-MM-DD)"),
            page_offset: int = Query(1, ge=1, description="Page number"),
            page_size: int = Query(100, ge=1, le=1000, description="Records per page")
        ) -> ReservoirResponseDTO:
            """Get reservoir data filtered by date range"""
            try:
                # Simple date validation
                if start_date > end_date:
                    raise HTTPException(
                        status_code=400, 
                        detail="Start date must be before end date"
                    )
                
                return await self.service.get_reservoir_data(start_date, end_date, page_offset, page_size)
                
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
            except Exception as exc:
                log(f"Error in reservoir endpoint: {exc}", LogLevel.ERROR)
                raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")


def create_router() -> APIRouter:
    return ReservoirRouter().router