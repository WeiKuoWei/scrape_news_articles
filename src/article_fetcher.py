"""
Module for fetching and parsing article content.
"""

import json
import pandas as pd
from newsplease import NewsPlease
import logging

logger = logging.getLogger(__name__)


class ArticleFetcher:
    """Fetches article content using NewsPlease"""
    
    def __init__(self, config):
        """Initialize with the provided configuration"""
        self.config = config
    
    def fetch_articles(self, site_name):
        """Fetch articles for the specified site"""
        logger.info(f"Fetching articles for {site_name}")
        
        urls_file = self.config.get_site_data_path(site_name, "urls_cleaned.csv")
        articles_file = self.config.get_site_data_path(site_name, "articles.json")
        
        # Ensure articles file exists
        with open(articles_file, 'w') as f:
            json.dump({}, f)
        
        # Load existing articles
        with open(articles_file, 'r') as f:
            existing_articles = json.load(f)
        
        try:
            # Read URLs
            df = pd.read_csv(urls_file, header=None, names=['id', 'url', 'status'])
            urls_to_process = df[df['status'] == 'no']
            
            total_urls = len(urls_to_process)
            logger.info(f"Found {total_urls} URLs to process for {site_name}")
            
            for index, row in urls_to_process.iterrows():
                url = row['url']
                site_id = row['id']
                
                try:
                    logger.info(f"Fetching article: {url}")
                    article = NewsPlease.from_url(url, timeout=15)
                    
                    if article:
                        # Convert to dictionary and add metadata
                        article_dict = article.get_serializable_dict()
                        article_dict["wayback_id"] = site_id
                        
                        # Save article
                        existing_articles[url] = article_dict
                        
                        # Update status
                        df.at[index, 'status'] = 'yes'
                        
                        logger.info(f"Successfully fetched article: {url}")
                    else:
                        logger.warning(f"Failed to fetch article (no content): {url}")
                        df.at[index, 'status'] = 'none'
                
                except Exception as e:
                    logger.error(f"Error fetching article {url}: {e}")
                    df.at[index, 'status'] = 'fail'
                
                # Periodically save progress
                if index % 20 == 0:
                    self._save_progress(df, urls_file, existing_articles, articles_file)
            
            # Save final progress
            self._save_progress(df, urls_file, existing_articles, articles_file)
            
            logger.info(f"Completed article fetching for {site_name}")
        
        except Exception as e:
            logger.error(f"Error processing articles for {site_name}: {e}")
    
    def _save_progress(self, df, urls_file, articles, articles_file):
        """Save progress to disk"""
        try:
            # Save updated URL statuses
            df.to_csv(urls_file, index=False, header=False)
            
            # Save articles
            with open(articles_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Progress saved: {len(articles)} articles")
        
        except Exception as e:
            logger.error(f"Error saving progress: {e}")