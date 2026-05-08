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
            headless=True, 
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
                    
                    scraped_posts.append({
                        "url": full_url, 
                        "text": text,
                        "platform": "x"
                    })
                except Exception:
                    continue # Skip ads or malformed tweets
        except Exception as e:
            logger.error(f"Error during tweet extraction: {e}")
        finally:
            browser.close()
    
    return scraped_posts

def post_reply(post_url, reply_text):
    """Automates posting a reply to a specific X post with verification."""
    with sync_playwright() as p:
        logger.info(f"Launching browser to reply to: {post_url}")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=True, 
            args=["--disable-blink-features=AutomationControlled"],
            slow_mo=500
        )
        page = browser.pages[0] 
        page.goto(post_url)
        
        try:
            # 1. Wait for reply box
            # X uses a div with data-testid="tweetTextarea_0"
            reply_box_selector = '[data-testid="tweetTextarea_0"]'
            reply_box = page.locator(reply_box_selector).first
            
            logger.info("Waiting for X reply box...")
            reply_box.wait_for(state="visible", timeout=30000)
            
            # 2. Focus and Type
            logger.info("Focusing and typing X reply...")
            reply_box.click()
            page.wait_for_timeout(1000)
            
            # Use keyboard typing to trigger UI state changes
            reply_box.press_sequentially(reply_text, delay=50)
            page.wait_for_timeout(2000)
            
            # 3. Locate and Verify Reply Button
            button_selector = '[data-testid="tweetButtonInline"]'
            reply_button = page.locator(button_selector).first
            
            reply_button.wait_for(state="visible", timeout=10000)
            
            if reply_button.is_disabled():
                logger.error("X Reply button is disabled after typing.")
                raise Exception("X Reply button remained disabled.")

            # 4. Click and Verify
            logger.info("Clicking the X reply button...")
            reply_button.click()
            
            # Verification: On X, the reply box usually collapses or clears,
            # and a "Your reply was sent" toast may appear.
            logger.info("Verifying X reply submission...")
            try:
                # Expect the button to disappear (as the box collapses)
                reply_button.wait_for(state="hidden", timeout=10000)
                logger.info("Reply button is gone, X reply likely sent.")
            except Exception:
                # Fallback: check if the text is still in the box
                current_text = reply_box.inner_text().strip()
                if current_text != "":
                    logger.error("X reply text still present in box after click.")
                    raise Exception("X reply failed to submit (text still present)")

            logger.info("X reply posted and verified successfully!")
            page.wait_for_timeout(2000)
            
        except Exception as e:
            logger.error(f"Failed to post X reply: {e}")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    # Standalone test
    posts = get_latest_posts()
    for p in posts:
        print(f"URL: {p['url']}\nTEXT: {p['text'][:100]}...\n{'-'*30}")