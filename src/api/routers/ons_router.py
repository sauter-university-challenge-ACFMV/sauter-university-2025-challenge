from fastapi import APIRouter, HTTPException, Body
from models.ons_dto import DateFilterDTO
import httpx
from services.ons_service import OnsService


class OnsRouter:
    def __init__(self, service: OnsService | None = None) -> None:
        self.service = service or OnsService()
        self.router = APIRouter(prefix="/ons", tags=["ONS Data"])
        self._register_routes()

    def _register_routes(self) -> None:
        @self.router.post(
            "/filter-parquet-files",
            response_model=list[dict],
            summary="Filter ONS PARQUET Files",
            description=(
                "Fetches and filters a list of PARQUET file resources from the ONS API "
                "based on dates provided in the request body."
            ),
        )
        async def filter_ons_parquet_files_endpoint(
            filters: DateFilterDTO = Body(...),
        ) -> list[dict]:
            """
            API Endpoint to filter ONS Parquet files.
            This function handles the HTTP request/response and calls the service layer.
            """
            try:
                result = await self.service.process_reservoir_data(filters)
                return result.success_downloads
            except ValueError as exc:
                raise HTTPException(status_code=500, detail=str(exc))
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=503, detail=f"Error requesting ONS API: {exc}"
                )
            except httpx.HTTPStatusError as exc:
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=f"ONS API returned an error: {exc}",
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=500, detail=f"An unexpected error occurred: {str(exc)}"
                )


def create_router() -> APIRouter:
    return OnsRouter().router
