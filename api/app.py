from flask import Flask, jsonify, request
import os, json, csv, requests
from datetime import datetime
from threading import Thread

# Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Platform modules
from platform_modules.instagram_poster import post_instagram
from platform_modules.threads_poster import post_threads
from x_twitter_semi_auto.approval_listener import post_x_twitter

# AI content generator
from agents.content_agent import generate_post

app = Flask(__name__)

# Load Google service account from env
GOOGLE_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
SERVICE_ACCOUNT_INFO = json.loads(GOOGLE_JSON)

SHEET_NAME = "SaveCash_Test"
LOG_FILE = "logs/post_logs.csv"

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_INFO, scope)
client = gspread.authorize(credentials)
sheet = client.open(SHEET_NAME).sheet1

# ------------------
# ROUTES
# ------------------

@app.route("/")
def home():
    return jsonify({"status": "SaveCash AI Marketing API is running"})

# Generate AI posts for all platforms
@app.route("/generate-next", methods=["POST"])
def generate_next():
    try:
        topic = request.json.get("topic", "SaveCash AI Marketing Automation")
        platforms = ["Instagram", "Threads", "X"]

        for platform in platforms:
            content = generate_post(platform, topic)
            sheet.append_row([platform, content, "", "pending"])

        return jsonify({"success": True, "message": "AI posts generated and added"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Post next pending row
@app.route("/post-next", methods=["POST"])
def post_next():
    try:
        rows = sheet.get_all_records()
        next_post = None
        for idx, row in enumerate(rows):
            if row.get("status", "").lower() in ["", "pending"]:
                next_post = (idx + 2, row)  # +2 for header
                break
        if not next_post:
            return jsonify({"success": False, "message": "No pending posts found"})

        row_number, post = next_post
        platform = post.get("platform").lower()
        content = post.get("content")
        media_url = post.get("media_url", None)

        success = False
        message = ""
        if platform == "instagram":
            success, message = post_instagram(content, media_url)
        elif platform == "threads":
            success, message = post_threads(content, media_url)
        elif platform in ["x", "twitter"]:
            success, message = post_x_twitter(content, media_url)
        else:
            message = f"Unknown platform: {platform}"

        # Update Google Sheet
        sheet.update_cell(row_number, sheet.find("status").col, "posted" if success else "failed")

        # Log
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.utcnow().isoformat(), platform, content, success, message])

        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ------------------
# AUTO-POSTING LOOP
# ------------------

def auto_post_loop(interval=3600):
    while True:
        try:
            requests.post(f"{os.getenv('API_URL')}/post-next")
        except Exception as e:
            print("Auto-post error:", e)
        import time
        time.sleep(interval)

Thread(target=auto_post_loop, daemon=True).start()

# ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
