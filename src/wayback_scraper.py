"""
Module for fetching snapshots from the Wayback Machine.
"""

import csv
import requests
import pandas as pd
from calendar import monthrange
from random import randint
import logging
import time

logger = logging.getLogger(__name__)


class WaybackMachineScraper:
    """Handles fetching URLs from the Wayback Machine archive"""
    
    def __init__(self, config):
        """Initialize with the provided configuration"""
        self.config = config
    
    def get_snapshots(self, site_name):
        """Fetch Wayback Machine snapshots for the specified site"""
        site_config = self.config.sites[site_name]
        output_file = self.config.get_site_data_path(site_name, "urls_wayback.csv")
        
        # Ensure the file exists and has a header
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'url', 'status'])
        
        # Process each URL configuration for the site
        for url_idx, url_config in site_config['url'].items():
            url_link = url_config['link']
            start_year = url_config['start_year']
            end_year = url_config['end_year']
            
            logger.info(f"Fetching Wayback Machine snapshots for {site_name} ({url_link}) from {start_year} to {end_year}")
            self._get_archive_urls(url_link, start_year, end_year, output_file)
        
        # Remove duplicates
        self._clean_snapshots_file(output_file)
        
        logger.info(f"Completed fetching snapshots for {site_name}")
    
    def _get_archive_urls(self, site, start_year, end_year, file_path):
        """Get URLs from Wayback Machine for a specific date range"""
        import re  # For regex pattern matching
        
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            
            # Start with the initial site
            sites_to_check = {site}
            # Track discovered redirects to avoid duplicating work
            discovered_redirects = {}
            
            # Common redirects for Fox News we know about
            if 'foxnews.com/us/' in site:
                sites_to_check.add('http://www.foxnews.com/us/index.html')
            
            for current_site in sites_to_check:
                logger.info(f"Checking snapshots for {current_site}")
                
                for year in range(start_year, end_year + 1):
                    for month in range(1, 13):
                        for day in range(1, monthrange(year, month)[1] + 1):       
                            try:
                                # Format: YYYYMMDDHHMMSS
                                timestamp = f"{year}{month:02d}{day:02d}{randint(0,9)}{randint(0,9)}{randint(0,9)}"
                                request_url = f"https://archive.org/wayback/available?url={current_site}&timestamp={timestamp}"
                                
                                response = requests.get(request_url, timeout=30)
                                if response.status_code != 200:
                                    logger.warning(f"Failed to fetch archive for {current_site} on {year}-{month}-{day}: Status {response.status_code}")
                                    continue
                                
                                data = response.json()
                                if 'archived_snapshots' in data and 'closest' in data['archived_snapshots']:
                                    snapshot = data['archived_snapshots']['closest']
                                    snapshot_timestamp = snapshot['timestamp']
                                    snapshot_url = snapshot['url']
                                    
                                    # Verify this snapshot is from the requested year
                                    if not snapshot_timestamp.startswith(str(year)):
                                        logger.warning(f"Snapshot from wrong year ({snapshot_timestamp[:4]} vs {year}) for {current_site} on {year}-{month}-{day}")
                                        continue
                                        
                                    # Extract the original URL from the Wayback Machine URL format
                                    match = re.search(r'web/\d+/(.+)', snapshot_url)
                                    if match:
                                        actual_url = match.group(1)
                                        if actual_url != current_site:
                                            logger.info(f"Snapshot URL points to {actual_url}, which differs from requested {current_site}")
                                            # We could add this to sites_to_check for future iterations if needed
                                    try:
                                        # Save the snapshot info
                                        logger.info(f"Found snapshot for {current_site} on {year}-{month}-{day}: {snapshot_url}")
                                        writer.writerow([snapshot_timestamp, snapshot_url, 'no'])
                                        logger.info(f"Saved snapshot for {snapshot_timestamp} with {snapshot_url}")
                                        
                                    except Exception as e:
                                        logger.error(f"Error writing snapshot to file: {e}")
                                        
                                else:
                                    logger.warning(f"No snapshot found for {current_site} on {year}-{month}-{day}")
                            
                            except Exception as e:
                                logger.error(f"Error fetching archive for {current_site} on {year}-{month}-{day}: {e}")
                            
                            # Add small delay to avoid overwhelming the API
                            time.sleep(0.2)
    
    def _clean_snapshots_file(self, file_path):
        """Remove duplicate entries from the snapshots file"""
        try:
            df = pd.read_csv(file_path)
            original_count = len(df)
            
            # Drop duplicates based on timestamp
            df.drop_duplicates(subset=['timestamp'], inplace=True)
            
            # Write the cleaned DataFrame back to CSV
            df.to_csv(file_path, index=False)
            
            logger.info(f"Cleaned snapshots file: removed {original_count - len(df)} duplicates")
        except Exception as e:
            logger.error(f"Error cleaning snapshots file {file_path}: {e}")