import sys
import os
import logging

# Add the root directory to sys.path so we can import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.scraper_linkedin import get_latest_linkedin_posts, post_linkedin_reply

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestLinkedInFlow")

def run_test():
    logger.info("Step 1: Scraping latest posts...")
    posts = get_latest_linkedin_posts()
    
    if not posts:
        logger.warning("No posts found to reply to. Check your keywords or login session.")
        return

    # Pick the first post for testing
    target_post = posts[0]
    logger.info(f"Step 2: Selected post for testing: {target_post['url']}")
    
    # Mock AI response
    test_bid = "Hey! I saw your post looking for a developer. I've worked on similar projects using React and FastAPI, and I'd love to help you out with this. Let's connect!"
    
    logger.info("Step 3: Running the reply automation...")
    logger.info("IMPORTANT: Since the post button is now active, be ready to close the browser if you don't want to post!")
    
    try:
        post_linkedin_reply(target_post['url'], test_bid)
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    run_test()
