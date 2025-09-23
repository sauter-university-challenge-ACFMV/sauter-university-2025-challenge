import os
import re
import httpx
import pandas as pd
import asyncio
from repositories.gcs_repository import GCSFileRepository
import io
from datetime import date, datetime
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
    try:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        log(f"Download successful ({len(response.content)} bytes).", level=LogLevels.DEBUG)
        
        with io.BytesIO(response.content) as buffer:
            df = pd.read_parquet(buffer, engine="fastparquet")

        log(f"Read Parquet file into DataFrame with {len(df)} rows.", level=LogLevels.DEBUG)

        filtered_df = filter_parquet_by_date(df, start_date, end_date)

        return filtered_df

    except Exception as e:
        log(f"Failed to process URL {url}. Reason: {e}", level=LogLevels.ERROR)
        return pd.DataFrame()


def filter_parquet_by_date(df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    """Filter the DataFrame by the given date range on 'ear_data' column."""
    if 'ear_data' not in df.columns:
        log("'ear_data' column not found in DataFrame.", level=LogLevels.DEBUG)
        return pd.DataFrame()
    
    df['ear_data'] = pd.to_datetime(df['ear_data']).dt.date
    mask = (df['ear_data'] >= start_date) & (df['ear_data'] <= end_date)
    filtered_df = df.loc[mask]
    log(f"Filtered DataFrame to {len(filtered_df)} rows between {start_date} and {end_date}.", level=LogLevels.DEBUG)
    return filtered_df


async def process_reservoir_data(filters: DateFilterDTO) -> list[dict]:
    """
    Service to fetch parquet file URLs, download them concurrently, merge,
    filter by date, and return the combined data.
    """
    log(f"Service started with filters: start={filters.start_date}, end={filters.end_date}", level=LogLevels.DEBUG)
    package = "ear-diario-por-reservatorio" if not filters.package else filters.package
    ons_base_api_url = os.environ.get("ONS_API_URL")
    ons_api_url = f"{ons_base_api_url}?id={package}" if ons_base_api_url else None
    log(f"Using ONS API URL: {ons_api_url}", level=LogLevels.DEBUG)
    log(f"Using package: {package}", level=LogLevels.DEBUG)
    if not ons_api_url:
        # For critical errors like this, raising an exception is better than just logging
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
            _download_and_process_parquet(client, url, filters.start_date, filters.end_date)
            for url in parquet_urls_to_download
        ]
        list_of_dataframes = await asyncio.gather(*tasks)

        valid_dataframes = [df for df in list_of_dataframes if not df.empty]
        if not valid_dataframes:
            log("No valid dataframes found after processing all files.", level=LogLevels.DEBUG)
            return []
        
        log(f"Merging {len(valid_dataframes)} dataframes into one.", level=LogLevels.DEBUG)
        merged_df = pd.concat(valid_dataframes, ignore_index=True)
        log(f"Final merged dataframe has {len(merged_df)} rows. Converting to dict.", level=LogLevels.DEBUG)

    return merged_df.to_dict('records')



