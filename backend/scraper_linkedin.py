import json
import os
import logging
from urllib.parse import quote
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScraperLinkedIn")

DEFAULT_KEYWORDS = ["looking for developer", "looking for freelancer"]
PROFILE_PATH = "./browser_profile_linkedin"

def get_latest_linkedin_posts():
    """Scrapes the latest job-related posts from LinkedIn."""
    scraped_posts = []
    
    with sync_playwright() as p:
        logger.info("Launching browser for LinkedIn scraping...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",          
                "--disable-setuid-sandbox"
            ],
            slow_mo=500 
        )
        
        page = browser.pages[0] 
        
        # Load keywords
        keywords = DEFAULT_KEYWORDS
        try:
            if os.path.exists('keywords.json'):
                with open('keywords.json', 'r') as f:
                    kw_data = json.load(f)
                    keywords = kw_data.get('keywords', DEFAULT_KEYWORDS)
        except Exception as e:
            logger.warning(f"Failed to load keywords, using defaults: {e}")
        
        # Build search URL
        query_string = " OR ".join([f'"{kw}"' for kw in keywords])
        search_url = f'https://www.linkedin.com/search/results/content/?keywords={quote(query_string)}&sortBy=%22date_posted%22'
        
        logger.info(f"Navigating to LinkedIn search: {search_url}")
        page.goto(search_url)
        
        try:
            page.wait_for_selector('div[data-urn]', timeout=20000)
            posts = page.locator('div[data-urn]').all()
            
            logger.info(f"Found {len(posts)} posts. Extracting...")
            for post in posts:
                try:
                    text_element = post.locator('.update-components-update-v2__commentary')
                    if text_element.count() == 0:
                        continue
                        
                    text = text_element.first.inner_text()
                    urn = post.get_attribute("data-urn")
                    
                    if urn:
                        full_url = f"https://www.linkedin.com/feed/update/{urn}/"
                        scraped_posts.append({"url": full_url, "text": text})
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Error during LinkedIn extraction: {e}")
        finally:
            browser.close()
            
    return scraped_posts

def post_linkedin_reply(post_url, reply_text):
    """Automates posting a reply to a specific LinkedIn post."""
    with sync_playwright() as p:
        logger.info(f"Launching browser to reply to: {post_url}")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False, 
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-setuid-sandbox"],
            slow_mo=500 
        )
        page = browser.pages[0] 
        page.goto(post_url)
        
        try:
            # LinkedIn uses a Quill editor for comments
            reply_box = page.locator('.comments-comment-box-comment__text-editor .ql-editor')
            reply_box.wait_for(state="visible", timeout=15000)
            
            logger.info("Typing reply...")
            reply_box.fill(reply_text)
            page.wait_for_timeout(1000)
            
            reply_button = page.locator('.comments-comment-box__submit-button')
            reply_button.click()
            logger.info("Comment posted successfully.")
            
            page.wait_for_timeout(3000)
        except Exception as e:
            logger.error(f"Failed to post LinkedIn reply: {e}")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    # Standalone test
    posts = get_latest_linkedin_posts()
    for p in posts:
        print(f"URL: {p['url']}\nTEXT: {p['text'][:100]}...\n{'-'*30}")
