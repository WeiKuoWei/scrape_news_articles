"""
Configuration module for the news scraper.
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Create project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ScraperConfig:
    """Configuration class for the news scraper"""
    
    def __init__(self, config_file=CONFIG_DIR / "sites.json"):
        """Load configuration from the specified JSON file"""
        try:
            with open(config_file, 'r') as f:
                self.sites = json.load(f)
            
            # Only keep CNN and Fox News
            self.target_sites = ['cnn', 'foxnews']
            self.sites = {k: v for k, v in self.sites.items() if k in self.target_sites}
            
            # Create data directories for each site
            for site in self.target_sites:
                site_dir = DATA_DIR / site
                site_dir.mkdir(exist_ok=True)
                
            logger.info(f"Loaded configuration with {len(self.target_sites)} target sites")
        
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def get_site_data_path(self, site_name, filename):
        """Get the path to a file in the site's data directory"""
        return DATA_DIR / site_name / filename
    
    def get_scraperapi_key(self):
        """Get ScraperAPI key from environment variables"""
        api_key = os.getenv('SCRAPERAPI_KEY')
        if not api_key:
            logger.warning("ScraperAPI key not found in environment variables")
        return api_key