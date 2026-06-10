"""Family Schedule - a minimal Flask app for a household to share weekly plans.

Each user logs in, edits their own schedule for the current and next week
(Monday-Sunday, up to 3 tasks per day with a name and time), and everyone can
view a shared board of all members' schedules.
"""

import os
import sqlite3
from datetime import date, timedelta
from functools import wraps

from flask import (
    Flask, g, redirect, render_template, request, session, url_for, abort
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "schedule.db")

# The five household accounts. Passwords are hashed into the database on first run.
USERS = {
    "Mark": "Mark123",
    "Mart": "Mart123",
    "Oom": "Oom123",
    "Noel": "Noel123",
    "Ramon": "Ramon123",
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SLOTS = [0, 1, 2]  # up to 3 tasks per day

app = Flask(__name__)
# Secret key persists across restarts so login sessions survive a server reboot.
_secret_file = os.path.join(BASE_DIR, "secret.key")
if not os.path.exists(_secret_file):
    with open(_secret_file, "wb") as f:
        f.write(os.urandom(32))
with open(_secret_file, "rb") as f:
    app.secret_key = f.read()

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


# --- Database helpers -------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username      TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            week_start TEXT NOT NULL,   -- ISO date of the Monday
            day        INTEGER NOT NULL,-- 0=Monday .. 6=Sunday
            slot       INTEGER NOT NULL,-- 0,1,2
            name       TEXT NOT NULL,
            time       TEXT NOT NULL,   -- start time HH:MM
            end_time   TEXT,            -- optional end time HH:MM
            UNIQUE(username, week_start, day, slot)
        )
        """
    )
    # Migration: add end_time to older databases that predate this column.
    cols = {row[1] for row in db.execute("PRAGMA table_info(tasks)").fetchall()}
    if "end_time" not in cols:
        db.execute("ALTER TABLE tasks ADD COLUMN end_time TEXT")
    for username, password in USERS.items():
        existing = db.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing is None:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
    db.commit()
    db.close()


# --- Week helpers -----------------------------------------------------------

def monday_of(d):
    return d - timedelta(days=d.weekday())


def week_options():
    """Return [(week_start_iso, label), ...] for the current and next week."""
    this_monday = monday_of(date.today())
    next_monday = this_monday + timedelta(days=7)
    return [
        (this_monday.isoformat(), _week_label(this_monday, "This week")),
        (next_monday.isoformat(), _week_label(next_monday, "Next week")),
    ]


def _week_label(monday, prefix):
    sunday = monday + timedelta(days=6)
    return f"{prefix} ({monday.strftime('%d %b')} – {sunday.strftime('%d %b')})"


def valid_week(week_start):
    return week_start in {w[0] for w in week_options()}


# --- Auth -------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["user"] = username
            return redirect(url_for("board"))
        error = "Incorrect name or password."
    return render_template("login.html", users=list(USERS.keys()), error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    user = session["user"]
    error = None
    success = False
    if request.method == "POST":
        current = request.form.get("current", "")
        new = request.form.get("new", "")
        confirm = request.form.get("confirm", "")
        db = get_db()
        row = db.execute(
            "SELECT password_hash FROM users WHERE username = ?", (user,)
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], current):
            error = "Current password is incorrect."
        elif len(new) < 6:
            error = "New password must be at least 6 characters."
        elif new != confirm:
            error = "New passwords do not match."
        else:
            db.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (generate_password_hash(new), user),
            )
            db.commit()
            success = True
    return render_template(
        "password.html", current_user=user, error=error, success=success
    )


# --- Shared board -----------------------------------------------------------

@app.route("/")
@login_required
def board():
    weeks = week_options()
    week_start = request.args.get("week", weeks[0][0])
    if not valid_week(week_start):
        week_start = weeks[0][0]

    rows = get_db().execute(
        "SELECT username, day, slot, name, time, end_time "
        "FROM tasks WHERE week_start = ?",
        (week_start,),
    ).fetchall()

    # schedule[username][day] = sorted list of {time, end_time, name}
    schedule = {u: {d: [] for d in range(7)} for u in USERS}
    for r in rows:
        schedule[r["username"]][r["day"]].append(
            {"time": r["time"], "end_time": r["end_time"], "name": r["name"]}
        )
    for u in schedule:
        for d in schedule[u]:
            schedule[u][d].sort(key=lambda t: t["time"])

    return render_template(
        "board.html",
        weeks=weeks,
        week_start=week_start,
        days=DAYS,
        users=list(USERS.keys()),
        schedule=schedule,
        current_user=session["user"],
    )


# --- Edit own schedule ------------------------------------------------------

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    weeks = week_options()
    user = session["user"]

    if request.method == "POST":
        week_start = request.form.get("week", weeks[0][0])
        if not valid_week(week_start):
            abort(400)
        db = get_db()
        db.execute(
            "DELETE FROM tasks WHERE username = ? AND week_start = ?",
            (user, week_start),
        )
        for day in range(7):
            for slot in SLOTS:
                name = request.form.get(f"name_{day}_{slot}", "").strip()
                time = request.form.get(f"time_{day}_{slot}", "").strip()
                end_time = request.form.get(f"end_{day}_{slot}", "").strip()
                # End time is optional. If given and earlier than start, ignore it.
                if end_time and end_time <= time:
                    end_time = ""
                if name and time:
                    db.execute(
                        "INSERT INTO tasks "
                        "(username, week_start, day, slot, name, time, end_time) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (user, week_start, day, slot, name, time,
                         end_time or None),
                    )
        db.commit()
        return redirect(url_for("board", week=week_start))

    week_start = request.args.get("week", weeks[0][0])
    if not valid_week(week_start):
        week_start = weeks[0][0]

    rows = get_db().execute(
        "SELECT day, slot, name, time, end_time FROM tasks "
        "WHERE username = ? AND week_start = ?",
        (user, week_start),
    ).fetchall()
    existing = {(r["day"], r["slot"]): r for r in rows}

    return render_template(
        "edit.html",
        weeks=weeks,
        week_start=week_start,
        days=DAYS,
        slots=SLOTS,
        existing=existing,
        current_user=user,
    )


if __name__ == "__main__":
    init_db()
    # host=0.0.0.0 makes it reachable from other devices on the home Wi-Fi.
    app.run(host="0.0.0.0", port=5000)
