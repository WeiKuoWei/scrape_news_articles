# News Scraper

A simplified tool for scraping news articles from CNN and Fox News from 2013 to 2023 using the Wayback Machine.

## Overview

This project scrapes historical news articles by:

1. Fetching archived snapshots from the Wayback Machine
2. Extracting article URLs from these snapshots 
3. Downloading and parsing article content using NewsPlease

## Project Structure

```
news_scraper/
│
├── config/              # Configuration files
│   └── sites.json       # News sites configuration
│
├── src/                 # Source code
│   ├── __init__.py
│   ├── main.py          # Main entry point
│   ├── config.py        # Configuration utilities
│   ├── wayback_scraper.py  # Wayback Machine scraper
│   ├── url_extractor.py    # URL extraction from snapshots
│   └── article_fetcher.py  # Article content fetcher
│
├── data/                # Scraped data storage
│   ├── cnn/             # CNN articles data
│   └── foxnews/         # Fox News articles data
│
├── logs/                # Log files
│
└── README.md            # This file
```

## Requirements

- Python 3.7+
- Required packages:
  - `requests`
  - `beautifulsoup4`
  - `pandas`
  - `newsplease`
  - `python-dotenv`

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/news-scraper.git
cd news-scraper
```

2. Install required packages:

```bash
pip install requests beautifulsoup4 pandas news-please python-dotenv
```

3. Create a `.env` file in the project root with your ScraperAPI key (optional but recommended):

```
SCRAPERAPI_KEY=your_api_key_here
```

## Usage

Run the scraper:

```bash
cd src
python main.py
```

The script will:
1. Create necessary directories
2. Fetch Wayback Machine snapshots for each site
3. Extract article URLs from snapshots
4. Download and parse article content
5. Save all data in the appropriate files

## Data Files

For each site (e.g., CNN, Fox News), the scraper creates:

- `urls_wayback.csv` - Wayback Machine snapshot URLs
- `urls_cleaned.csv` - Extracted article URLs
- `articles.json` - Parsed article content

## Article Data Structure

Article data is stored in JSON format with this structure:

```json
{
  "https://example.com/article-url": {
    "title": "Article Title",
    "authors": ["Author Name"],
    "date_publish": "2020-01-01 12:00:00",
    "text": "Full article text...",
    "wayback_id": "20200101120000"
  }
}
```

## Notes

- ScraperAPI is recommended to avoid IP blocks when scraping at scale
- Progress is periodically saved to prevent data loss