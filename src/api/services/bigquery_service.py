from typing import List, Dict, Any, Optional, Tuple
from repositories.bigquery_repository import GCPBigQueryRepository
from models.bigquery_dto import ReservoirResponseDTO
from utils.logger import LogLevel, log
from datetime import date
import asyncio


class ReservoirService:
    def __init__(self, repository: Optional[GCPBigQueryRepository] = None) -> None:
        self._repository = repository  # guarda a ref
        self.table_id = "gold.dados_reservatorios_completo"

    @property
    def repository(self) -> GCPBigQueryRepository:
        """Só cria o repositório se realmente precisar"""
        if self._repository is None:
            self._repository = GCPBigQueryRepository()
        return self._repository

    async def get_reservoir_data(
        self,
        start_date: date,
        end_date: date,
        page_offset: int,
        page_size: int
    ) -> ReservoirResponseDTO:
        """Get reservoir data filtered by date range with pagination"""
        log(f"Fetching reservoir data from {start_date} to {end_date}", LogLevel.INFO)

        try:
            base_query = f"""
                SELECT *
                FROM `{self.repository.project_id}.{self.table_id}`
                WHERE ena_data >= '{start_date}' 
                  AND ena_data <= '{end_date}'
                ORDER BY ena_data ASC
            """

            count_query = f"""
                SELECT COUNT(*) as total 
                FROM `{self.repository.project_id}.{self.table_id}`
                WHERE ena_data >= '{start_date}' 
                  AND ena_data <= '{end_date}'
            """

            log(f"Base query: {base_query}", LogLevel.DEBUG)
            log(f"Count query: {count_query}", LogLevel.DEBUG)

            data, total_records = await asyncio.to_thread(
                self.repository.execute_paginated_query,
                base_query,
                count_query,
                page_offset,
                page_size
            )

            return ReservoirResponseDTO(
                data=data,
                total_records=total_records,
                page=page_offset,
                page_size=page_size
            )

        except Exception as e:
            log(f"Error fetching reservoir data: {e}", LogLevel.ERROR)
            raise
