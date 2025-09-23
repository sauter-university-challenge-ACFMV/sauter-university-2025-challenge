import os
import re
import httpx
import pandas as pd
import asyncio
from repositories.gcs_repository import GCSFileRepository
import io
from datetime import date, datetime
from pathlib import Path
from models.ons_dto import DateFilterDTO
from utils.logger import LogLevels, log


repo = GCSFileRepository()

def save_file(file, filename: str, content_type: str) -> str:
    return repo.upload(file, filename, content_type)


async def _download_and_process_parquet(
    client: httpx.AsyncClient, 
    url: str, 
    start_date: date, 
    end_date: date
) -> pd.DataFrame:
    """Helper to download one parquet file, filter it, and return a DataFrame."""
    log(f"==> Processing URL: {url}", level=LogLevels.DEBUG)
    
    # Generate local file path
    filename = get_cache_filename(url)
    local_path = CACHE_DIR / filename
    
    # Check if file already exists locally
    if local_path.exists():
        log(f"File already cached: {local_path}", level=LogLevels.DEBUG)
        return str(local_path)
    
    try:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        log(f"Download successful ({len(response.content)} bytes).", level=LogLevels.DEBUG)
        
        # Save to local file
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        log(f"Saved parquet file locally: {local_path}", level=LogLevels.DEBUG)
        
        # Optional: Verify the file can be read
        with io.BytesIO(response.content) as buffer:
            df = pd.read_parquet(buffer, engine="fastparquet")
            log(f"Verified parquet file with {len(df)} rows.", level=LogLevels.DEBUG)
        
        return str(local_path)
        
    except Exception as e:
        log(f"Failed to process URL {url}. Reason: {e}", level=LogLevels.ERROR)
        return ""

async def process_reservoir_data(filters: DateFilterDTO) -> list[dict]:
    """
    Service to fetch parquet file URLs, download them concurrently, save locally,
    and return the local file paths.
    """
    log(f"Service started with filters: start={filters.start_date}, end={filters.end_date}", level=LogLevels.DEBUG)
    
    package = "ear-diario-por-reservatorio" if not filters.package else filters.package
    ons_base_api_url = os.environ.get("ONS_API_URL")
    ons_api_url = f"{ons_base_api_url}?id={package}" if ons_base_api_url else None
    
    log(f"Using ONS API URL: {ons_api_url}", level=LogLevels.DEBUG)
    log(f"Using package: {package}", level=LogLevels.DEBUG)
    
    if not ons_api_url:
        log("ONS_API_URL environment variable not set.", level=LogLevels.ERROR)
        raise ValueError("ONS_API_URL environment variable not set.")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(ons_api_url)
        response.raise_for_status()
        data = response.json()
        
        result = data.get("result", {})
        all_resources = result.get("resources", [])
        parquet_urls_to_download = []
        
        start_year = filters.start_date.year
        end_year = filters.end_date.year
        
        for resource in all_resources:
            if resource.get("format", "").upper() == "PARQUET" and resource.get("url"):
                name = resource.get("name", "")
                match = re.search(r"(\d{4})", name)
                if match:
                    resource_year = int(match.group(1))
                    if start_year <= resource_year <= end_year:
                        parquet_urls_to_download.append(resource["url"])
        
        log(f"Found {len(parquet_urls_to_download)} parquet files for years {start_year}-{end_year}.")
        
        if not parquet_urls_to_download:
            return []
        
        tasks = [
            download_parquet(client, url)
            for url in parquet_urls_to_download
        ]
        
        local_file_paths = await asyncio.gather(*tasks)
        
        # Filter out empty results (failed downloads)
        successful_downloads = [
            {"url": url, "local_path": path} 
            for url, path in zip(parquet_urls_to_download, local_file_paths) 
            if path
        ]
        
        log(f"Successfully downloaded {len(successful_downloads)} files to local cache.", level=LogLevels.DEBUG)
        log(f"Cache directory: {CACHE_DIR}", level=LogLevels.DEBUG)
        
        return successful_downloads