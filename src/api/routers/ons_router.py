from fastapi import APIRouter, HTTPException, Body, status
from fastapi.responses import JSONResponse
from models.ons_dto import DateFilterDTO
from services.ons_service import OnsService, ProcessResponse
from pydantic import BaseModel
from typing import Dict, Any, List


class ApiResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any] | None = None

class ApiBulkResponse(BaseModel):
    status: str
    message: str
    data: List[Dict[str, Any]] | None = None

class OnsRouter:
    def __init__(self, service: OnsService | None = None) -> None:
        self.service = service or OnsService()
        self.router = APIRouter(prefix="/ons", tags=["ONS Data"])
        self._register_routes()

    def _register_routes(self) -> None:
        @self.router.post(
            "/filter-parquet-files",
            response_model=ApiResponse,
            summary="Processa um único filtro de arquivos PARQUET da ONS",
            description="Recebe um único objeto de filtro e inicia a ingestão dos dados correspondentes.",
            responses={
                200: {
                    "description": "Processamento concluído com sucesso total ou parcial.",
                    "content": {
                        "application/json": {
                            "examples": {
                                "all_success": {
                                    "summary": "Sucesso total",
                                    "value": {
                                        "status": "success",
                                        "message": "Todos os 3 arquivos foram processados com sucesso.",
                                        "data": {"success_count": 3, "failure_count": 0}
                                    }
                                },
                                "partial_success": {
                                    "summary": "Sucesso parcial",
                                    "value": {
                                        "status": "partial_success",
                                        "message": "Sucesso parcial: 2/3 arquivos processados.",
                                        "data": {"success_count": 2, "failure_count": 1}
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
                    "description": "Todos os arquivos falharam ao serem processados.",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "failed",
                                "message": "Todos os 3 arquivos falharam ao processar.",
                                "data": {"success_count": 0, "failure_count": 3}
                            }
                        }
                    }
                },
                500: {"description": "Erro interno inesperado no servidor."}
            }
        )
        async def filter_parquet_files_endpoint(
            filters: DateFilterDTO = Body(...)
        ) -> JSONResponse | ApiResponse:
            try:
                result: ProcessResponse = await self.service.process_reservoir_data(filters)
                
                response_data = {
                    "success_downloads": result.success_downloads,
                    "failed_downloads": result.failed_downloads,
                    "total_processed": result.total_processed,
                    "success_count": result.success_count,
                    "failure_count": result.failure_count,
                }

                if result.failure_count == 0:
                    return ApiResponse(status="success", message=f"Todos os {result.total_processed} arquivos foram processados com sucesso.", data=response_data)
                
                elif result.success_count == 0:
                    content = ApiResponse(status="failed", message=f"Todos os {result.total_processed} arquivos falharam ao processar.", data=response_data).model_dump()
                    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content)

                else:
                    return ApiResponse(status="partial_success", message=f"Sucesso parcial: {result.success_count}/{result.total_processed} arquivos processados.", data=response_data)
            
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ocorreu um erro inesperado: {str(exc)}"
                )

        @self.router.post(
            "/bulk-ingest-parquet-files",
            response_model=ApiBulkResponse,
            summary="Processa um lote de filtros de arquivos PARQUET da ONS",
            description="Recebe uma lista de filtros (DTOs) e processa cada um em paralelo. Ideal para jobs agendados.",
            responses={
                200: {
                    "description": "Lote de filtros processado. O corpo da resposta contém o resultado detalhado de cada filtro.",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "success",
                                "message": "Lote de 2 filtros processado.",
                                "data": [
                                    {
                                        "success_downloads": [{"url": "...", "gcs_path": "..."}],
                                        "failed_downloads": [],
                                        "total_processed": 1,
                                        "success_count": 1,
                                        "failure_count": 0
                                    },
                                    {
                                        "success_downloads": [],
                                        "failed_downloads": [{"url": "...", "error_message": "..."}],
                                        "total_processed": 1,
                                        "success_count": 0,
                                        "failure_count": 1
                                    }
                                ]
                            }
                        }
                    }
                },
                500: {"description": "Erro interno inesperado ao processar o lote."}
            }
        )
        async def bulk_ingest_parquet_files_endpoint(
            filters_list: List[DateFilterDTO] = Body(...)
        ) -> ApiBulkResponse:
            try:
                results: List[ProcessResponse | BaseException] = await self.service.process_reservoir_data_bulk(filters_list)
                results_dict = [result.model_dump() for result in results if not isinstance(result, BaseException)]
                return ApiBulkResponse(
                    status="success",
                    message=f"Lote de {len(results_dict)} filtros processado.",
                    data=results_dict
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ocorreu um erro inesperado ao processar o lote: {str(exc)}"
                )


def create_router() -> APIRouter:
    return OnsRouter().router