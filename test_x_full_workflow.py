import sys
import os
import logging

# Add the root directory to sys.path so we can import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.scraper_x import get_latest_posts, post_reply

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestXFlow")

def run_test():
    logger.info("Step 1: Scraping latest tweets...")
    posts = get_latest_posts()
    
    if not posts:
        logger.warning("No tweets found to reply to. Check your keywords or login session.")
        return

    # Pick the first tweet for testing
    target_post = posts[0]
    logger.info(f"Step 2: Selected tweet for testing: {target_post['url']}")
    
    # Mock AI response
    test_bid = "This looks like a great project! I have experience with Python and Playwright and would love to help out. Let's chat!"
    
    logger.info("Step 3: Running the X reply automation...")
    logger.info("NOTE: Since we activated the post buttons, this will actually attempt to post unless you close the browser manually!")
    
    try:
        post_reply(target_post['url'], test_bid)
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    run_test()
