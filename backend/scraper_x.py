import json
import os
import logging
from urllib.parse import quote
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScraperX")

# Resolve paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_PATH = os.path.join(BASE_DIR, 'keywords.json')
PROFILE_PATH = os.path.join(BASE_DIR, 'browser_profile_x')

DEFAULT_KEYWORDS = ["looking for developer", "looking for freelancer"]

def get_latest_posts():
    """Scrapes the latest job-related posts from X (Twitter)."""
    scraped_posts = []
    
    with sync_playwright() as p:
        logger.info("Launching browser for X scraping...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False, 
            args=["--disable-blink-features=AutomationControlled"],
            slow_mo=500 
        )
        
        page = browser.pages[0] 
        
        # Load keywords
        keywords = DEFAULT_KEYWORDS
        try:
            if os.path.exists(KEYWORDS_PATH):
                with open(KEYWORDS_PATH, 'r') as f:
                    kw_data = json.load(f)
                    keywords = kw_data.get('keywords', DEFAULT_KEYWORDS)
        except Exception as e:
            logger.warning(f"Failed to load keywords, using defaults: {e}")
        
        # Build search URL
        query_string = " OR ".join([f'"{kw}"' for kw in keywords])
        search_url = f"https://x.com/search?q={quote(query_string)}&src=typed_query&f=live"
        
        logger.info(f"Navigating to search results: {search_url}")
        page.goto(search_url)
        
        try:
            page.wait_for_selector('article[data-testid="tweet"]', timeout=15000)
            tweets = page.locator('article[data-testid="tweet"]').all()
            
            logger.info(f"Found {len(tweets)} tweets. Extracting details...")
            for tweet in tweets:
                try:
                    text = tweet.locator('div[data-testid="tweetText"]').inner_text()
                    post_url_rel = tweet.locator("time").locator("..").get_attribute("href")
                    full_url = "https://x.com" + post_url_rel
                    
                    scraped_posts.append({"url": full_url, "text": text})
                except Exception:
                    continue # Skip ads or malformed tweets
        except Exception as e:
            logger.error(f"Error during tweet extraction: {e}")
        finally:
            browser.close()
    
    return scraped_posts

def post_reply(post_url, reply_text):
    """Automates posting a reply to a specific X post."""
    with sync_playwright() as p:
        logger.info(f"Launching browser to reply to: {post_url}")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False, 
            args=["--disable-blink-features=AutomationControlled"],
            slow_mo=500
        )
        page = browser.pages[0] 
        page.goto(post_url)
        
        try:
            # Wait for reply box
            reply_box = page.locator('[data-testid="tweetTextarea_0"]')
            reply_box.wait_for(state="visible", timeout=15000)
            
            logger.info("Typing reply...")
            reply_box.fill(reply_text)
            page.wait_for_timeout(1000)
            
            reply_button = page.locator('[data-testid="tweetButtonInline"]')
            reply_button.click() 
            logger.info("Reply posted successfully.")
            
            page.wait_for_timeout(3000)
        except Exception as e:
            logger.error(f"Failed to post reply: {e}")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    # Standalone test
    posts = get_latest_posts()
    for p in posts:
        print(f"URL: {p['url']}\nTEXT: {p['text'][:100]}...\n{'-'*30}")
