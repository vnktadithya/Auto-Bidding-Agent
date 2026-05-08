import json
import os
import logging
from urllib.parse import quote
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScraperLinkedIn")

# Resolve paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_PATH = os.path.join(BASE_DIR, 'keywords.json')
PROFILE_PATH = os.path.join(BASE_DIR, 'browser_profile_linkedin')

DEFAULT_KEYWORDS = ["looking for developer", "looking for freelancer"]

def get_latest_linkedin_posts():
    """Scrapes the latest job-related posts from LinkedIn."""
    scraped_posts = []
    
    with sync_playwright() as p:
        logger.info("Launching browser for LinkedIn scraping...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=True, 
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
            if os.path.exists(KEYWORDS_PATH):
                with open(KEYWORDS_PATH, 'r') as f:
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
                        scraped_posts.append({
                            "url": full_url, 
                            "text": text,
                            "platform": "linkedin"
                        })
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Error during LinkedIn extraction: {e}")
        finally:
            browser.close()
            
    return scraped_posts

def post_linkedin_reply(post_url, reply_text):
    """Automates posting a reply to a specific LinkedIn post with verification."""
    # We set this to a variable so we can use it in error handling
    is_headless = True 
    
    with sync_playwright() as p:
        logger.info(f"Launching browser to reply to: {post_url}")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=is_headless, 
            args=[
                "--disable-blink-features=AutomationControlled", 
                "--no-sandbox", 
                "--disable-setuid-sandbox"
            ],
            slow_mo=500 
        )
        page = browser.pages[0] 
        page.goto(post_url)
        
        try:
            # 1. Wait for the editor to be ready
            editor_selector = '.ql-editor[contenteditable="true"]'
            reply_box = page.locator(editor_selector).first
            
            logger.info("Waiting for comment editor...")
            reply_box.wait_for(state="visible", timeout=30000)
            
            # 2. Focus and Type
            logger.info("Focusing and typing reply...")
            reply_box.click()
            page.wait_for_timeout(1000)
            
            # Ensure the box is clear before typing
            page.keyboard.press("Control+a")
            page.keyboard.press("Backspace")
            
            # Use keyboard typing for better event triggering
            page.keyboard.type(reply_text, delay=50)
            page.wait_for_timeout(2000)
            
            # 3. Locate and Verify Post/Comment Button
            logger.info("Locating the Comment submission button...")
            
            # Priority selectors: 
            # 1. The specific LinkedIn submit class
            # 2. A primary button with "Comment" text (as seen in your screenshot)
            # 3. A button with "Post" text (fallback for other regions/views)
            selectors = [
                "button.comments-comment-box__submit-button",
                "button.artdeco-button--primary:has-text('Comment')",
                "button.artdeco-button--primary:has-text('Post')",
                ".comments-comment-box__form-container button[type='submit']"
            ]
            
            reply_button = None
            for selector in selectors:
                # We use a more specific search to ensure it's the one in the comment area
                loc = page.locator(f".comments-comment-box {selector}").first
                if loc.is_visible():
                    reply_button = loc
                    break
            
            if not reply_button:
                logger.warning("Specific button not found in comment box, trying global primary buttons...")
                # Avoid "Repost" by being explicit about the text
                reply_button = page.locator('button.artdeco-button--primary:has-text("Comment"), button.artdeco-button--primary:has-text("Post")').first

            reply_button.wait_for(state="visible", timeout=10000)
            
            # If button is still disabled, try a final "wake up" of the editor
            if reply_button.is_disabled():
                logger.warning("Post button is disabled. Re-triggering editor focus...")
                reply_box.click()
                page.keyboard.press("Space")
                page.keyboard.press("Backspace")
                page.wait_for_timeout(1000)
                
            if reply_button.is_disabled():
                raise Exception("LinkedIn Post button remained disabled after typing.")

            # 4. Attempt submission
            logger.info("Attempting submission (Clicking button)...")
            reply_button.click()
            page.wait_for_timeout(3000)
            
            # Verification: Check if text is still in the box
            current_text = reply_box.inner_text().strip()
            if current_text != "" and current_text != "Add a comment...":
                logger.info("Box not cleared by click. Trying keyboard shortcut (Control+Enter)...")
                reply_box.focus()
                page.keyboard.press("Control+Enter")
                page.wait_for_timeout(4000)

            # Final Verification
            current_text = reply_box.inner_text().strip()
            # Success if: editor is hidden OR text is gone/placeholder
            if not reply_box.is_visible() or current_text == "" or current_text == "Add a comment...":
                logger.info("LinkedIn comment posted and verified successfully!")
            else:
                logger.error(f"Verification failed. Final text: '{current_text[:30]}...'")
                raise Exception("Comment failed to submit after multiple attempts (Button & Shortcut).")
            
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
