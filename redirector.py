from flask import Flask, redirect, request, jsonify
from flask_cors import CORS
import logging
import os
from supabase import create_client, Client

# ==========================
# Configuration
# ==========================
DEPLOYED_URL = "https://mitlogs-links.onrender.com"
if DEPLOYED_URL == "https://mitlogs-links.onrender.com":
    DEPLOYED_URL = "https://links.themitlogs.com"

SUPABASE_URL = os.getenv("SUPABASE_URL")  # e.g., https://xyzcompany.supabase.co
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Supabase anon or service key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================
# Logging
# ==========================
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ==========================
# Flask app
# ==========================
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# ==========================
# Helper functions
# ==========================


def get_url(short_id: str):
    """Fetch the URL associated with a short_id from Supabase safely."""
    try:
        response = (
            supabase.table("links")
            .select("url")
            .eq("short_id", short_id)
            .maybe_single()
            .execute()
        )
        if not response or response.error:
            # Either the request failed or response.error is set
            if response and response.error:
                logger.error(f"Error fetching {short_id}: {response.error}")
            return None
        return response.data["url"] if response.data else None
    except Exception as e:
        logger.exception(f"Unexpected error fetching {short_id}: {e}")
        return None


def set_url(short_id: str, url: str):
    """Insert or update a URL in Supabase. Returns the old URL if overwritten."""
    old_url = get_url(short_id)
    if old_url:
        # Update existing row
        response = (
            supabase.table("links")
            .update({"url": url})
            .eq("short_id", short_id)
            .execute()
        )
        if response.error:
            logger.error(f"Error updating {short_id}: {response.error}")
    else:
        # Insert new row
        response = (
            supabase.table("links").insert({"short_id": short_id, "url": url}).execute()
        )
        if response.error:
            logger.error(f"Error inserting {short_id}: {response.error}")
    return old_url


# ==========================
# Routes
# ==========================
@app.route("/<short_id>")
def redirect_link(short_id):
    url = get_url(short_id)
    if url:
        return redirect(url)
    return "Link not found", 404


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/create", methods=["POST"])
def create_link():
    logger.info(f"Received request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")

    if not request.is_json:
        logger.error("Request is not JSON")
        return jsonify({"error": "Content-Type must be application/json"}), 400

    try:
        data = request.get_json()
        logger.info(f"Request data: {data}")
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    short_id = data.get("id")
    url = data.get("url")
    if not short_id or not url:
        logger.error(f"Missing id or url. id: {short_id}, url: {url}")
        return jsonify({"error": "Missing id or url"}), 400

    old_url = set_url(short_id, url)
    if old_url:
        logger.info(f"short_url is: {DEPLOYED_URL}/{short_id}")
        return (
            jsonify(
                {
                    "message": f"Replaced old URL: {old_url}",
                    "short_url": f"{DEPLOYED_URL}/{short_id}",
                }
            ),
            200,
        )

    logger.info(f"short_url is: {DEPLOYED_URL}/{short_id}")
    return jsonify({"short_url": f"{DEPLOYED_URL}/{short_id}"}), 201


# ==========================
# Main
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)

# from flask import Flask, redirect, request, jsonify, make_response
# from flask_cors import CORS
# import sqlite3
# import logging
# import os

# DEPLOYED_URL = "https://mitlogs-links.onrender.com"

# if DEPLOYED_URL == "https://mitlogs-links.onrender.com":
#     DEPLOYED_URL = "https://links.themitlogs.com"

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# app = Flask(__name__)
# CORS(app)  # This will enable CORS for all routes
# DB_PATH = "links.db"


# # Initialize database
# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute(
#         """
#         CREATE TABLE IF NOT EXISTS links (
#             short_id TEXT PRIMARY KEY,
#             url TEXT NOT NULL
#         )
#     """
#     )
#     conn.commit()
#     conn.close()


# init_db()


# # Helper functions
# def get_url(short_id):
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute("SELECT url FROM links WHERE short_id = ?", (short_id,))
#     row = c.fetchone()
#     conn.close()
#     return row[0] if row else None


# def set_url(short_id, url):
#     old_url = get_url(short_id)
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute("REPLACE INTO links (short_id, url) VALUES (?, ?)", (short_id, url))
#     conn.commit()
#     conn.close()
#     return old_url


# # Redirect route
# @app.route("/<short_id>")
# def redirect_link(short_id):
#     url = get_url(short_id)
#     if url:
#         return redirect(url)
#     return "Link not found", 404


# # Create/overwrite link
# @app.route("/create", methods=["POST"])
# def create_link():
#     logger.info(f"Received request: {request.method} {request.url}")
#     logger.info(f"Headers: {dict(request.headers)}")

#     if not request.is_json:
#         logger.error("Request is not JSON")
#         return jsonify({"error": "Content-Type must be application/json"}), 400

#     try:
#         data = request.get_json()
#         logger.info(f"Request data: {data}")
#     except Exception as e:
#         logger.error(f"Error parsing JSON: {e}")
#         return jsonify({"error": "Invalid JSON"}), 400

#     short_id = data.get("id")
#     url = data.get("url")

#     if not short_id or not url:
#         logger.error(f"Missing id or url. id: {short_id}, url: {url}")
#         return jsonify({"error": "Missing id or url"}), 400

#     old_url = set_url(short_id, url)
#     if old_url:
#         logger.info(f"short_url is: {DEPLOYED_URL}/{short_id}")
#         return (
#             jsonify(
#                 {
#                     "message": f"Replaced old URL: {old_url}",
#                     "short_url": f"{DEPLOYED_URL}/{short_id}",
#                 }
#             ),
#             200,
#         )
#     logger.info(f"short_url is: {DEPLOYED_URL}/{short_id}")
#     return jsonify({"short_url": f"{DEPLOYED_URL}/{short_id}"}), 201


# if __name__ == "__main__":
#     # Use port 5001 to avoid conflict with AirPlay on macOS
#     port = int(os.environ.get("PORT", 5001))
#     app.run(debug=True, host="0.0.0.0", port=port)
