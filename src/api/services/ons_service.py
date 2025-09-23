import os
import re
import httpx
import pandas as pd
import asyncio

from pydantic import BaseModel
from repositories.gcs_repository import GCSFileRepository
import io
from pathlib import Path
from datetime import datetime
from models.ons_dto import DateFilterDTO
from utils.logger import LogLevels, log
import traceback


class DownloadInfo(BaseModel):
    url: str
    year: int
    package: str
    data_type: str


class OnsService():
    def __init__(self):
        self.repository = GCSFileRepository()

    async def _download_parquet(
        self,
        client: httpx.AsyncClient,
        download_info: DownloadInfo,
    ) -> str:
        """
        Helper to download a file, convert ALL columns to string, save as Parquet,
        and return the GCS path.
        """
        url = download_info.url
        resource_year = download_info.year
        package_name = download_info.package
        data_type = download_info.data_type

        log(f"Processing URL ({data_type}): {url}", level=LogLevels.DEBUG)

        try:
            response = await client.get(url, timeout=60.0)
            response.raise_for_status()
            log(f"Download successful ({len(response.content)} bytes)", level=LogLevels.DEBUG)

            original_filename = Path(url).name
            df = None

            try:
                with io.BytesIO(response.content) as initial_buffer:
                    log(f"Initial buffer closed before read: {initial_buffer.closed}", level=LogLevels.DEBUG)
                    if data_type == 'parquet':
                        df = pd.read_parquet(initial_buffer, engine="pyarrow")
                    elif data_type == 'csv':
                        df = pd.read_csv(initial_buffer, sep=';', encoding='latin1', low_memory=False)
                    elif data_type == 'xlsx':
                        df = pd.read_excel(initial_buffer)
                    else:
                        log(f"Unsupported data_type for conversion: {data_type}", level=LogLevels.ERROR)
                        return ""
                    log(f"Initial buffer closed after read: {initial_buffer.closed}", level=LogLevels.DEBUG)
            except Exception as e:
                log(f"Failed to read source file {original_filename}: {e}", level=LogLevels.ERROR)
                return ""

            log(f"Converting all columns to string for {original_filename}", level=LogLevels.DEBUG)
            df = df.astype(str)

            final_buffer_to_save = io.BytesIO()
            df.to_parquet(final_buffer_to_save, engine='pyarrow', index=False)
            log(f"DataFrame successfully written to final in-memory Parquet buffer", level=LogLevels.DEBUG)
            log(f"Final buffer closed after write: {final_buffer_to_save.closed}", level=LogLevels.DEBUG)

            parquet_filename = Path(original_filename).with_suffix('.parquet').name
            now = datetime.now()
            if resource_year < now.year:
                gcs_path = f"{package_name}/{resource_year}/{parquet_filename}"
            else:
                gcs_path = f"{package_name}/{now.year}/{now.month:02d}/{now.day:02d}/{parquet_filename}"
            log(f"Determined GCS path: {gcs_path}", level=LogLevels.DEBUG)

            final_buffer_to_save.seek(0)
            save_buffer = io.BytesIO(final_buffer_to_save.getvalue())
            log(f"Final buffer closed before save: {final_buffer_to_save.closed}", level=LogLevels.DEBUG)
            log(f"Save buffer closed before save: {save_buffer.closed}", level=LogLevels.DEBUG)
            try:
                gcs_url = self.repository.save(save_buffer, gcs_path)
                log(f"Successfully saved to bucket path: {gcs_path}, URL: {gcs_url}", level=LogLevels.INFO)
                log(f"Final buffer closed after save: {final_buffer_to_save.closed}", level=LogLevels.DEBUG)
                log(f"Save buffer closed after save: {save_buffer.closed}", level=LogLevels.DEBUG)
            except Exception as e:
                log(f"Failed to save to bucket path {gcs_path}: {e}\n{traceback.format_exc()}", level=LogLevels.ERROR)
                return ""

            return gcs_path

        except Exception as e:
            log(f"Unexpected error processing URL {url}: {e}\n{traceback.format_exc()}", level=LogLevels.ERROR)
            return ""


    async def process_reservoir_data(
            self,
            filters: DateFilterDTO) -> list[dict]:
        log(f"Service started with filters: start_year={filters.start_year}, end_year={filters.end_year}", level=LogLevels.INFO)

        package = filters.package if filters.package else "ear-diario-por-reservatorio"
        ons_base_api_url = os.environ.get("ONS_API_URL")

        if not ons_base_api_url:
            error_msg = "ONS_API_URL environment variable not set"
            log(error_msg, level=LogLevels.ERROR)
            raise ValueError(error_msg)

        ons_api_url = f"{ons_base_api_url}?id={package}"

        log(f"Using ONS API URL: {ons_api_url}", level=LogLevels.DEBUG)
        log(f"Using package: {package}", level=LogLevels.DEBUG)
        log(f"Target bucket: {self.repository.bucket_name}", level=LogLevels.INFO)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                log("Fetching package information from ONS API", level=LogLevels.DEBUG)
                response = await client.get(ons_api_url)
                response.raise_for_status()
                data = response.json()

                result = data.get("result", {})
                all_resources = result.get("resources", [])

                if not all_resources:
                    log("No resources found in the package", level=LogLevels.ERROR)
                    return []

                parquet_resources_to_download = []
                start_year = filters.start_year
                end_year = filters.end_year
                data_type = filters.data_type.lower() if filters.data_type else "parquet"

                log(f"Filtering resources for years {start_year}-{end_year} and type {data_type}", level=LogLevels.DEBUG)

                for resource in all_resources:
                    if resource.get("format", "").lower() == data_type and resource.get("url"):
                        name = resource.get("name", "")
                        match = re.search(r"(\d{4})", name)
                        if match:
                            resource_year = int(match.group(1))
                            if start_year <= resource_year <= end_year:
                                download_info = DownloadInfo(
                                    url=resource["url"],
                                    year=resource_year,
                                    package=package,
                                    data_type=data_type
                                )
                                parquet_resources_to_download.append(download_info)
                                log(f"Added resource for year {resource_year}: {name}", level=LogLevels.DEBUG)

                log(f"Found {len(parquet_resources_to_download)} files for years {start_year}-{end_year}", level=LogLevels.INFO)

                if not parquet_resources_to_download:
                    log(f"No files of type '{data_type}' found for the specified date range", level=LogLevels.ERROR)
                    return []

                log("Starting concurrent downloads", level=LogLevels.INFO)
                tasks = [
                    self._download_parquet(client, resource)
                    for resource in parquet_resources_to_download
                ]

                gcs_paths = await asyncio.gather(*tasks, return_exceptions=True)

                successful_downloads = []
                for resource, result in zip(parquet_resources_to_download, gcs_paths):
                    if isinstance(result, Exception):
                        log(f"Task failed for {resource.url}: {result}", level=LogLevels.ERROR)
                    elif result:
                        successful_downloads.append({
                            "url": resource.url,
                            "gcs_path": result,
                            "bucket": self.repository.bucket_name
                        })

                success_count = len(successful_downloads)
                total_count = len(parquet_resources_to_download)

                log(f"Download summary: {success_count}/{total_count} files successfully processed", level=LogLevels.INFO)

                if success_count == 0:
                    log("No files were successfully downloaded and saved", level=LogLevels.ERROR)
                elif success_count < total_count:
                    log(f"Partial success: {total_count - success_count} files failed", level=LogLevels.ERROR)
                else:
                    log("All files successfully downloaded and saved to bucket", level=LogLevels.INFO)

                return successful_downloads

        except httpx.RequestError as e:
            error_msg = f"Request error while fetching ONS API: {e}"
            log(error_msg, level=LogLevels.ERROR)
            raise Exception(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} while fetching ONS API: {e}"
            log(error_msg, level=LogLevels.ERROR)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error in process_reservoir_data: {e}"
            log(error_msg, level=LogLevels.ERROR)
            raise Exception(error_msg)