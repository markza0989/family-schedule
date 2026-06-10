"""Production entrypoint for 24/7 hosting.

Uses Waitress (a stable WSGI server) instead of Flask's built-in dev server.
Run with:  python serve.py
"""

from waitress import serve

from app import app, init_db

if __name__ == "__main__":
    init_db()
    # 0.0.0.0 = reachable from other devices on the home Wi-Fi.
    serve(app, host="0.0.0.0", port=5000)
