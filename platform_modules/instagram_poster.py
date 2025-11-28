import os, requests

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

def post_instagram(content, media_url=None):
    try:
        # Create media container
        payload = {
            "caption": content,
            "access_token": ACCESS_TOKEN
        }
        if media_url:
            payload["image_url"] = media_url
        else:
            # fallback to placeholder image
            payload["image_url"] = "https://via.placeholder.com/1080"

        # Step 1: create container
        r = requests.post(f"https://graph.facebook.com/v16.0/{ACCOUNT_ID}/media", data=payload)
        r.raise_for_status()
        creation_id = r.json()["id"]

        # Step 2: publish
        r2 = requests.post(f"https://graph.facebook.com/v16.0/{ACCOUNT_ID}/media_publish",
                           data={"creation_id": creation_id, "access_token": ACCESS_TOKEN})
        r2.raise_for_status()

        return True, "Posted to Instagram successfully"
    except Exception as e:
        return False, str(e)
