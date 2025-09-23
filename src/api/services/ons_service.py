import os
import re
import httpx
import pandas as pd
import asyncio
from repositories.gcs_repository import GCSFileRepository
import io
from pathlib import Path
from models.ons_dto import DateFilterDTO
from utils.logger import LogLevels, log


class OnsService():
    def __init__(self):
        self.repository = GCSFileRepository()

    async def _download_parquet(
        self,
        client: httpx.AsyncClient, 
        url: str, 
    ) -> str:
        """Helper to download one parquet file, save to bucket, and return filename."""
        log(f"Processing URL: {url}", level=LogLevels.DEBUG)
        
        try:
            # Download the file
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            log(f"Download successful ({len(response.content)} bytes)", level=LogLevels.DEBUG)
            
            filename = Path(url).name
            
            # Create a BytesIO buffer from response content
            file_buffer = io.BytesIO(response.content)
            
            # Verify it's a valid parquet file by reading it
            try:
                # Reset buffer position to beginning for reading
                file_buffer.seek(0)
                df = pd.read_parquet(file_buffer, engine="fastparquet")
                log(f"Verified parquet file with {len(df)} rows and {len(df.columns)} columns", level=LogLevels.DEBUG)
            except Exception as e:
                log(f"Failed to read parquet file {filename}: {e}", level=LogLevels.ERROR)
                return ""
            
            # Reset buffer position to beginning for saving
            file_buffer.seek(0)
            
            # Save to GCS bucket
            try:
                public_url = self.repository.save(file_buffer, filename)
                log(f"Successfully saved {filename} to bucket: {self.repository.bucket_name}", level=LogLevels.INFO)
                log(f"File URL: {public_url}", level=LogLevels.DEBUG)
            except Exception as e:
                log(f"Failed to save {filename} to bucket: {e}", level=LogLevels.ERROR)
                return ""
            
            return filename

        except httpx.RequestError as e:
            log(f"Request error for URL {url}: {e}", level=LogLevels.ERROR)
            return ""
        except httpx.HTTPStatusError as e:
            log(f"HTTP error {e.response.status_code} for URL {url}: {e}", level=LogLevels.ERROR)
            return ""
        except Exception as e:
            log(f"Unexpected error processing URL {url}: {e}", level=LogLevels.ERROR)
            return ""


    async def process_reservoir_data(
            self,
            filters: DateFilterDTO) -> list[dict]:
        """
        Service to fetch parquet file URLs, download them concurrently, save to GCS bucket,
        and return the successful downloads information.
        """
        log(f"Service started with filters: start={filters.start_date}, end={filters.end_date}", level=LogLevels.INFO)
        
        # Set default package if none provided
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
                # Fetch package information
                log("Fetching package information from ONS API", level=LogLevels.DEBUG)
                response = await client.get(ons_api_url)
                response.raise_for_status()
                data = response.json()
                
                result = data.get("result", {})
                all_resources = result.get("resources", [])
                
                if not all_resources:
                    log("No resources found in the package", level=LogLevels.ERROR)
                    return []
                
                # Filter parquet files by year range
                parquet_urls_to_download = []
                start_year = filters.start_date.year
                end_year = filters.end_date.year
                
                log(f"Filtering resources for years {start_year}-{end_year}", level=LogLevels.DEBUG)
                
                for resource in all_resources:
                    if resource.get("format", "").upper() == "PARQUET" and resource.get("url"):
                        name = resource.get("name", "")
                        # Extract year from resource name
                        match = re.search(r"(\d{4})", name)
                        if match:
                            resource_year = int(match.group(1))
                            if start_year <= resource_year <= end_year:
                                parquet_urls_to_download.append(resource["url"])
                                log(f"Added resource for year {resource_year}: {name}", level=LogLevels.DEBUG)
                
                log(f"Found {len(parquet_urls_to_download)} parquet files for years {start_year}-{end_year}", level=LogLevels.INFO)
                
                if not parquet_urls_to_download:
                    log("No parquet files found for the specified date range", level=LogLevels.ERROR)
                    return []
                
                # Download files concurrently
                log("Starting concurrent downloads", level=LogLevels.INFO)
                tasks = [
                    self._download_parquet(client, url)
                    for url in parquet_urls_to_download
                ]
                
                filenames = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results and handle exceptions
                successful_downloads = []
                for url, result in zip(parquet_urls_to_download, filenames):
                    if isinstance(result, Exception):
                        log(f"Task failed for {url}: {result}", level=LogLevels.ERROR)
                    elif result:  # Non-empty filename means success
                        successful_downloads.append({
                            "url": url,
                            "filename": result,
                            "bucket": self.repository.bucket_name
                        })
                
                success_count = len(successful_downloads)
                total_count = len(parquet_urls_to_download)
                
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