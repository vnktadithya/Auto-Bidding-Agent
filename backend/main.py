import os
import json
import requests
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import scraper_x
from . import scraper_linkedin
from . import db

# Resolve paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONA_PATH = os.path.join(BASE_DIR, 'persona.json')
KEYWORDS_PATH = os.path.join(BASE_DIR, 'keywords.json')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AutoBidAPI")

app = FastAPI(title="Auto Bidding Bot API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ReplyRequest(BaseModel):
    post_url: str
    reply_text: str

class SaveRequest(BaseModel):
    url: str
    platform: str
    reply_text: Optional[str] = None

class ConfigPayload(BaseModel):
    persona: dict
    keywords: dict
    webhook_url: Optional[str] = None

# Lifecycle
@app.on_event("startup")
def startup_db_migration():
    db.init_db()
    logger.info("Database initialized and ready.")

# --- Scraping Endpoints ---

@app.get("/scrape/{platform}")
def scrape_posts(platform: str):
    """Scrapes latest posts from X or LinkedIn."""
    p = platform.lower()
    if p == "x":
        posts = scraper_x.get_latest_posts()
        return {"platform": "x", "count": len(posts), "posts": posts}
    elif p == "linkedin":
        posts = scraper_linkedin.get_latest_linkedin_posts()
        return {"platform": "linkedin", "count": len(posts), "posts": posts}
    
    raise HTTPException(status_code=400, detail="Invalid platform. Use 'x' or 'linkedin'.")

@app.post("/reply/{platform}")
def post_reply(platform: str, request: ReplyRequest):
    """Automates posting a reply to a specific post."""
    p = platform.lower()
    try:
        if p == "x":
            scraper_x.post_reply(request.post_url, request.reply_text)
        elif p == "linkedin":
            scraper_linkedin.post_linkedin_reply(request.post_url, request.reply_text)
        else:
            raise HTTPException(status_code=400, detail="Invalid platform")
        
        return {"status": "success", "message": f"Replied to {p} post: {request.post_url}"}
    except Exception as e:
        logger.error(f"Reply error on {p}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Database & History Endpoints ---

@app.get("/db/check")
def check_duplicate(url: str):
    """Checks if a URL has already been processed."""
    return {"exists": db.check_exists(url)}

@app.post("/db/save")
def save_post(request: SaveRequest):
    """Saves a processed URL to the history."""
    success = db.save_post(request.url, request.platform, request.reply_text)
    if success:
        return {"status": "success", "message": "Saved to database"}
    return {"status": "ignored", "message": "URL already exists in database"}

@app.get("/db/rate_limit/{platform}")
def check_rate_limit(platform: str):
    """Checks daily posting limits for a platform."""
    p = platform.lower()
    count_today = db.get_daily_count(p)
    limit = 5 if p == "x" else 15
    return {
        "platform": p, 
        "posts_today": count_today, 
        "can_post": count_today < limit
    }

@app.get("/notifications")
def get_notifications():
    """Returns the history of all posted bids."""
    return {"notifications": db.get_history()}

# --- Configuration Endpoints ---

@app.get("/config")
def get_config():
    """Returns current persona and keywords configuration."""
    persona, keywords, webhook_url = {}, {}, ""
    try:
        if os.path.exists(PERSONA_PATH):
            with open(PERSONA_PATH, 'r') as f:
                persona = json.load(f)
        if os.path.exists(KEYWORDS_PATH):
            with open(KEYWORDS_PATH, 'r') as f:
                data = json.load(f)
                keywords = data
                webhook_url = data.get('webhook_url', "")
    except Exception as e:
        logger.error(f"Config read error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load configuration")
    
    return {"persona": persona, "keywords": keywords, "webhook_url": webhook_url}

@app.get("/persona")
def get_persona():
    """Returns ONLY the persona configuration."""
    try:
        if os.path.exists(PERSONA_PATH):
            with open(PERSONA_PATH, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Persona read error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load persona")

@app.post("/config")
def save_config(payload: ConfigPayload):
    """Saves persona and keywords configuration."""
    try:
        with open(PERSONA_PATH, 'w') as f:
            json.dump(payload.persona, f, indent=2)
        
        kw_data = payload.keywords
        kw_data['webhook_url'] = payload.webhook_url
        with open(KEYWORDS_PATH, 'w') as f:
            json.dump(kw_data, f, indent=2)
            
        return {"status": "success", "message": "Configuration saved"}
    except Exception as e:
        logger.error(f"Config save error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save configuration")

@app.post("/trigger")
def trigger_workflow():
    """Triggers the n8n workflow webhook."""
    try:
        webhook_url = ""
        if os.path.exists(KEYWORDS_PATH):
            with open(KEYWORDS_PATH, 'r') as f:
                data = json.load(f)
                webhook_url = data.get('webhook_url', "").strip()
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="Webhook URL not configured")
        
        logger.info(f"Triggering n8n webhook: {webhook_url}")
        response = requests.get(webhook_url, timeout=10)
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="n8n webhook not found. Ensure it is Active.")
            
        return {
            "status": "success", 
            "n8n_status": response.status_code,
            "n8n_response": response.text[:100]
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook network error: {str(e)}")
        raise HTTPException(status_code=500, detail="Network error while reaching n8n")
    except Exception as e:
        logger.error(f"Trigger error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
