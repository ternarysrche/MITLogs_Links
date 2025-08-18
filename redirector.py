from flask import Flask, redirect, request, jsonify, make_response
from flask_cors import CORS
import sqlite3
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
DB_PATH = "links.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS links (
            short_id TEXT PRIMARY KEY,
            url TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Helper functions
def get_url(short_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT url FROM links WHERE short_id = ?", (short_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_url(short_id, url):
    old_url = get_url(short_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO links (short_id, url) VALUES (?, ?)", (short_id, url))
    conn.commit()
    conn.close()
    return old_url

# Redirect route
@app.route("/<short_id>")
def redirect_link(short_id):
    url = get_url(short_id)
    if url:
        return redirect(url)
    return "Link not found", 404

# Create/overwrite link
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
        return jsonify({
            "message": f"Replaced old URL: {old_url}",
            "short_url": f"http://localhost:5001/{short_id}"
        }), 200
    return jsonify({"short_url": f"http://localhost:5001/{short_id}"}), 201

if __name__ == "__main__":
    # Use port 5001 to avoid conflict with AirPlay on macOS
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
