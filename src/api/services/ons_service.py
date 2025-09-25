import os
import re
import httpx
import pandas as pd  # type: ignore[import-untyped]
import asyncio

from pydantic import BaseModel
from repositories.gcs_repository import GCSFileRepository
import io
from pathlib import Path
from datetime import datetime
from models.ons_dto import DateFilterDTO
from utils.logger import LogLevel, log
import traceback


class DownloadInfo(BaseModel):
    url: str
    year: int
    package: str
    data_type: str
    bucket: str | None = None


class DownloadResult(BaseModel):
    url: str
    year: int
    package: str
    data_type: str
    success: bool
    gcs_path: str = ""
    error_message: str = ""
    bucket: str = ""


class ProcessResponse(BaseModel):
    success_downloads: list[dict]
    failed_downloads: list[dict]
    total_processed: int
    success_count: int
    failure_count: int


class OnsService:
    def __init__(self) -> None:
        self.repository = GCSFileRepository()

    async def _fetch_bytes(self, client: httpx.AsyncClient, url: str) -> bytes:
        log(f"Fetching content: {url}", level=LogLevel.DEBUG)
        response = await client.get(url, timeout=60.0)
        response.raise_for_status()
        log(f"Fetched {len(response.content)} bytes", level=LogLevel.DEBUG)
        return response.content

    def _read_to_dataframe(self, content: bytes, data_type: str) -> pd.DataFrame:
        with io.BytesIO(content) as buffer:
            log(f"Reading content as {data_type}", level=LogLevel.DEBUG)
            if data_type == "parquet":
                return pd.read_parquet(buffer, engine="pyarrow")
            if data_type == "csv":
                return pd.read_csv(buffer, sep=";", encoding="latin1", low_memory=False)
            if data_type == "xlsx":
                return pd.read_excel(buffer)
            raise ValueError(f"Unsupported data_type: {data_type}")

    def _convert_all_columns_to_string(self, df: pd.DataFrame) -> pd.DataFrame:
        log("Converting all columns to string", level=LogLevel.DEBUG)
        return df.astype(str)

    def _dataframe_to_parquet_buffer(self, df: pd.DataFrame) -> io.BytesIO:
        log("Serializing DataFrame to Parquet buffer", level=LogLevel.DEBUG)
        out = io.BytesIO()
        df.to_parquet(out, engine="pyarrow", index=False)
        out.seek(0)
        return out

    def _build_gcs_path(
        self, original_filename: str, resource_year: int, package_name: str
    ) -> str:
        parquet_filename = Path(original_filename).with_suffix(".parquet").name
        now = datetime.now()
        if resource_year < now.year:
            return f"{package_name}/{resource_year}/{parquet_filename}"
        return f"{package_name}/{now.year}/{now.month:02d}/{now.day:02d}/{parquet_filename}"

    def _save_to_gcs(self, buffer: io.BytesIO, gcs_path: str, _bucket_name: str | None) -> str:
        log(f"Saving buffer to GCS: {gcs_path}", level=LogLevel.DEBUG)
        save_buffer = io.BytesIO(buffer.getvalue())
        return self.repository.save(save_buffer, gcs_path, _bucket_name=_bucket_name)

    async def _download_parquet(
        self,
        client: httpx.AsyncClient,
        download_info: DownloadInfo,
    ) -> DownloadResult:
        """
        Download a file, convert ALL columns to string, save as Parquet, and return result.
        """
        url = download_info.url
        resource_year = download_info.year
        package_name = download_info.package
        data_type = download_info.data_type

        result = DownloadResult(
            url=url,
            year=resource_year,
            package=package_name,
            data_type=data_type,
            success=False,
            bucket=self.repository.bucket_name
        )

        try:
            log(f"Processing URL ({data_type}): {url}", level=LogLevel.DEBUG)
            
            # Fetch content
            try:
                content = await self._fetch_bytes(client, url)
            except Exception as e:
                result.error_message = f"Failed to fetch URL: {str(e)}"
                log(f"Failed to fetch {url}: {e}", level=LogLevel.ERROR)
                return result

            original_filename = Path(url).name
            
            # Read DataFrame
            try:
                df = self._read_to_dataframe(content, data_type)
            except Exception as e:
                result.error_message = f"Failed to read source file {original_filename}: {str(e)}"
                log(result.error_message, level=LogLevel.ERROR)
                return result

            # Convert columns and create buffer
            try:
                df = self._convert_all_columns_to_string(df)
                buffer = self._dataframe_to_parquet_buffer(df)
            except Exception as e:
                result.error_message = f"Failed to process DataFrame: {str(e)}"
                log(result.error_message, level=LogLevel.ERROR)
                return result

            # Find date column
            date_column = next((col for col in df.columns if "dat" in col.lower()), None)
            if not date_column:
                result.error_message = "No date column found in the file"
                log(result.error_message, level=LogLevel.DEBUG)
                return result

            gcs_path = self._build_gcs_path(original_filename, resource_year, package_name)

            # Check if data already exists
            try:
                df = df.sort_values(by=date_column)
                last_value = df[date_column].iloc[-1]
                
                log(f"Checking if data already exists with last date: {last_value}", level=LogLevel.DEBUG)
                
                if self.repository.raw_table_has_value(package_name, date_column, last_value):
                    result.error_message = "Data already exists in the raw table"
                    result.gcs_path = gcs_path  # Still provide the path for reference
                    log(f"Data from {url} already exists", level=LogLevel.DEBUG)
                    return result
                
            except Exception as e:
                result.error_message = f"Failed to check existing data: {str(e)}"
                log(result.error_message, level=LogLevel.ERROR)
                return result

            # Save to GCS
            try:
                gcs_url = self._save_to_gcs(buffer, gcs_path, _bucket_name=download_info.bucket)
                result.success = True
                result.gcs_path = gcs_path
                log(f"Successfully saved to bucket path: {gcs_path}, URL: {gcs_url}", level=LogLevel.INFO)
                return result
                
            except Exception as e:
                result.error_message = f"Failed to save to GCS bucket: {str(e)}"
                log(f"Failed to save to bucket path {gcs_path}: {e}\n{traceback.format_exc()}", level=LogLevel.ERROR)
                return result

        except Exception as e:
            result.error_message = f"Unexpected error: {str(e)}"
            log(f"Unexpected error processing URL {url}: {e}\n{traceback.format_exc()}", level=LogLevel.ERROR)
            return result

    async def process_reservoir_data(self, filters: DateFilterDTO) -> ProcessResponse:
        log(
            f"Service started with filters: start_year={filters.start_year}, end_year={filters.end_year}",
            level=LogLevel.INFO,
        )

        package = filters.package if filters.package else "ear-diario-por-reservatorio"
        ons_base_api_url = os.environ.get("ONS_API_URL")

        if not ons_base_api_url:
            error_msg = "ONS_API_URL environment variable not set"
            log(error_msg, level=LogLevel.ERROR)
            raise ValueError(error_msg)

        ons_api_url = f"{ons_base_api_url}?id={package}"

        log(f"Using ONS API URL: {ons_api_url}", level=LogLevel.DEBUG)
        log(f"Using package: {package}", level=LogLevel.DEBUG)
        log(f"Target bucket: {self.repository.bucket_name}", level=LogLevel.INFO)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                log("Fetching package information from ONS API", level=LogLevel.DEBUG)
                response = await client.get(ons_api_url)
                response.raise_for_status()
                data = response.json()

                result = data.get("result", {})
                all_resources = result.get("resources", [])

                if not all_resources:
                    log("No resources found in the package", level=LogLevel.ERROR)
                    raise Exception("No resources found in the package")

                parquet_resources_to_download = []
                start_year = filters.start_year
                end_year = filters.end_year
                preferred_formats = ["parquet", "csv", "xlsx"]

                log(
                    f"Filtering resources for years {start_year}-{end_year} with preferred formats {preferred_formats}",
                    level=LogLevel.DEBUG,
                )

                # Guard against None values for years
                if start_year is None or end_year is None:
                    now_year = datetime.now().year
                    if start_year is None:
                        start_year = now_year
                    if end_year is None:
                        end_year = now_year

                # Build a per-year best-format selection
                by_year: dict[int, dict] = {}
                no_year_resources: list[dict] = []
                
                for resource in all_resources:
                    fmt = resource.get("format", "").lower()
                    url = resource.get("url")
                    if not url or fmt not in preferred_formats:
                        continue
                    name = resource.get("name", "")
                    match = re.search(r"(\d{4})", name)
                    
                    if match:
                        resource_year = int(match.group(1))
                        if resource_year < start_year or resource_year > end_year:
                            continue
                        rank = preferred_formats.index(fmt)
                        current = by_year.get(resource_year)
                        if current is None or rank < current["rank"]:
                            by_year[resource_year] = {"resource": resource, "rank": rank}
                    else:
                        no_year_resources.append(resource)

                for resource_year, item in sorted(by_year.items()):
                    chosen = item["resource"]
                    fmt = chosen.get("format", "").lower()
                    download_info = DownloadInfo(
                        url=chosen["url"],
                        year=resource_year,
                        package=package,
                        data_type=fmt,
                        bucket=filters.bucket
                    )
                    parquet_resources_to_download.append(download_info)
                    log(
                        f"Added resource for year {resource_year}: {chosen.get('name','')}",
                        level=LogLevel.DEBUG,
                    )

                if not parquet_resources_to_download and no_year_resources:
                    log("No year-specific resources found, using fallback resources", level=LogLevel.DEBUG)
                    
                    # Find best format among no-year resources
                    best_resource = None
                    best_rank = len(preferred_formats)
                    
                    for resource in no_year_resources:
                        fmt = resource.get("format", "").lower()
                        if fmt in preferred_formats:
                            rank = preferred_formats.index(fmt)
                            if rank < best_rank:
                                best_resource = resource
                                best_rank = rank
                    
                    if best_resource:
                        fmt = best_resource.get("format", "").lower()
                        download_info = DownloadInfo(
                            url=best_resource["url"],
                            year=datetime.now().year,
                            package=package,
                            data_type=fmt,
                            bucket=filters.bucket
                        )
                        parquet_resources_to_download.append(download_info)
                        log(
                            f"Added fallback resource: {best_resource.get('name','')}",
                            level=LogLevel.DEBUG,
                        )

                log(
                    f"Found {len(parquet_resources_to_download)} files for years {start_year}-{end_year}",
                    level=LogLevel.INFO,
                )

                if not parquet_resources_to_download:
                    log("No files found for the specified date range", level=LogLevel.ERROR)
                    raise Exception("No files found for the specified date range")

                log("Starting concurrent downloads", level=LogLevel.INFO)
                tasks = [
                    self._download_parquet(client, resource)
                    for resource in parquet_resources_to_download
                ]

                download_results = await asyncio.gather(*tasks, return_exceptions=True)

                successful_downloads = []
                failed_downloads = []

                for resource, result in zip(parquet_resources_to_download, download_results):
                    if isinstance(result, Exception):
                        bucket_name = resource.bucket if resource.bucket else self.repository.bucket_name
                        failed_downloads.append({
                            "url": resource.url,
                            "year": resource.year,
                            "package": resource.package,
                            "data_type": resource.data_type,
                            "error_message": str(result),
                            "bucket": bucket_name,
                        })
                        log(f"Task failed for {resource.url}: {result}", level=LogLevel.ERROR)
                    elif isinstance(result, DownloadResult):
                        if result.success:
                            successful_downloads.append({
                                "url": result.url,
                                "year": result.year,
                                "package": result.package,
                                "data_type": result.data_type,
                                "gcs_path": result.gcs_path,
                                "bucket": result.bucket,
                            })
                        else:
                            failed_downloads.append({
                                "url": result.url,
                                "year": result.year,
                                "package": result.package,
                                "data_type": result.data_type,
                                "error_message": result.error_message,
                                "gcs_path": result.gcs_path,
                                "bucket": result.bucket,
                            })

                success_count = len(successful_downloads)
                failure_count = len(failed_downloads)
                total_count = success_count + failure_count

                log(
                    f"Download summary: {success_count}/{total_count} files successfully processed, {failure_count} failed",
                    level=LogLevel.INFO,
                )

                return ProcessResponse(
                    success_downloads=successful_downloads,
                    failed_downloads=failed_downloads,
                    total_processed=total_count,
                    success_count=success_count,
                    failure_count=failure_count,
                )

        except httpx.RequestError as e:
            error_msg = f"Request error while fetching ONS API: {e}"
            log(error_msg, level=LogLevel.ERROR)
            raise Exception(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} while fetching ONS API: {e}"
            log(error_msg, level=LogLevel.ERROR)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error in process_reservoir_data: {e}"
            log(error_msg, level=LogLevel.ERROR)
            raise Exception(error_msg)