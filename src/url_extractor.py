"""
Module for extracting URLs from Wayback Machine snapshots.
"""

import csv
import requests
import pandas as pd
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class URLExtractor:
    """Extracts URLs from Wayback Machine snapshots"""
    
    def __init__(self, config):
        """Initialize with the provided configuration"""
        self.config = config
        self.api_key = config.get_scraperapi_key()
        
        self.proxies = None
        if self.api_key:
            self.proxies = {
                "http": f"http://scraperapi:{self.api_key}@proxy-server.scraperapi.com:8001",
                "https": f"https://scraperapi:{self.api_key}@proxy-server.scraperapi.com:8001"
            }
    
    def extract_urls(self, site_name):
        """Extract URLs from Wayback Machine snapshots for the specified site"""
        logger.info(f"Extracting URLs for {site_name}")
        
        input_file = self.config.get_site_data_path(site_name, "urls_wayback.csv")
        output_file = self.config.get_site_data_path(site_name, "urls_uncleaned.csv")
        base_url = self.config.sites[site_name]['base_url']
        
        # Ensure output file exists
        with open(output_file, 'w', newline='') as f:
            pass  # Create an empty file
        
        # Read snapshots file
        try:
            logging.info(f"Reading snapshots from {input_file}")
            df = pd.read_csv(input_file)
            total_snapshots = len(df)
            processed = 0
            
            for index, row in df.iterrows():
                if row['status'] == 'yes':
                    processed += 1
                    continue
                
                try:
                    snapshot_id = row['timestamp']
                    snapshot_url = row['url']
                    
                    # Extract links from the snapshot
                    links = self._extract_links_from_snapshot(snapshot_url)
                    
                    # Process the links to get original URLs
                    processed_links = self._process_links(links)
                    
                    # Save the extracted URLs
                    self._save_links(processed_links, output_file, snapshot_id)
                    
                    # Mark the snapshot as processed
                    df.at[index, 'status'] = 'yes'
                    processed += 1
                    
                    logger.info(f"Processed snapshot {processed}/{total_snapshots} for {site_name}: {snapshot_url}")
                
                except Exception as e:
                    logger.error(f"Error processing snapshot {row['url']}: {e}")
                    df.at[index, 'status'] = 'fail'
            
            # Save progress
            df.to_csv(input_file, index=False)
            
            # Clean and filter the URLs
            self._clean_urls(output_file, base_url)
            
            logger.info(f"Completed URL extraction for {site_name}: {processed}/{total_snapshots} snapshots processed")
        
        except Exception as e:
            logger.error(f"Error extracting URLs for {site_name}: {e}")
    
    def _extract_links_from_snapshot(self, snapshot_url):
        """Extract links from a Wayback Machine snapshot"""
        try:
            # Use ScraperAPI proxy if available
            if self.proxies:
                protocol = 'https' if snapshot_url.startswith('https') else 'http'
                response = requests.get(snapshot_url, proxies={protocol: self.proxies[protocol]})
            else:
                response = requests.get(snapshot_url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch snapshot {snapshot_url}: Status {response.status_code}")
                return []
            
            # Parse links
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            
            logger.info(f"Extracted {len(links)} links from {snapshot_url}")
            return links
        
        except Exception as e:
            logger.error(f"Error extracting links from {snapshot_url}: {e}")
            return []
    
    def _process_links(self, links):
        """Process links extracted from Wayback Machine snapshots"""
        processed_links = []
        
        for link in links:
            if not link or len(link) < 10:
                continue
                
            try:
                # Extract the original URL from Wayback Machine format
                # Format is typically: /web/TIMESTAMP/ORIGINAL_URL
                parts = link.split('/')
                if len(parts) >= 3 and parts[1] == 'web':
                    # The original URL starts from the 3rd part
                    original_url = '/'.join(parts[3:])
                    if original_url.startswith('http'):
                        processed_links.append(original_url)
                elif 'http' in link:
                    # Try to find 'http' in the link
                    idx = link.find('http')
                    if idx >= 0:
                        processed_links.append(link[idx:])
            except Exception:
                continue
        
        return processed_links
    
    def _save_links(self, links, output_file, snapshot_id):
        """Save extracted links to the output file"""
        try:
            with open(output_file, 'a', newline='') as file:
                writer = csv.writer(file)
                for link in links:
                    writer.writerow([snapshot_id, link, 'no'])
        except Exception as e:
            logger.error(f"Error saving links to {output_file}: {e}")
    
    def _clean_urls(self, file_path, base_url):
        """Clean and filter URLs"""
        try:
            if not file_path.exists() or file_path.stat().st_size == 0:
                logger.warning(f"No URLs to clean in {file_path}")
                return
                
            df = pd.read_csv(file_path, header=None, names=['id', 'url', 'status'])
            original_count = len(df)
            
            # Drop duplicates
            df.drop_duplicates(subset=['url'], inplace=True)
            
            # Keep only URLs with the specified base URL
            df = df[df['url'].str.contains(base_url, na=False)]
            
            # Drop videos and short URLs
            df = df[~df['url'].str.contains('/video/', na=False)]
            df = df[df['url'].str.len() >= 10]
            
            # Sort by URL length (shorter URLs are often more valuable)
            df['length'] = df['url'].str.len()
            df.sort_values(by='length', ascending=True, inplace=True)
            df.drop(columns=['length'], inplace=True)
            
            # Write back to file
            df.to_csv(file_path, index=False, header=False)
            
            logger.info(f"Cleaned URLs: {original_count} -> {len(df)}")
        
        except Exception as e:
            logger.error(f"Error cleaning URLs in {file_path}: {e}")