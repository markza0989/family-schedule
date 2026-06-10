# Family Schedule — Setup & Hosting Guide (Windows PC)

A small private website where the family can post and view each other's weekly
schedules. Everyone connects over your **home Wi-Fi** — nothing is exposed to
the public internet.

## Accounts

| Name  | Password  |
|-------|-----------|
| Mark  | Mark123   |
| Mart  | Mart123   |
| Oom   | Oom123    |
| Noel  | Noel123   |
| Ramon | Ramon123  |

> **Changing a password:** each person can change their own password from the
> **Password** button on the board (top right) — no file editing, schedules are
> kept. Changed passwords are stored (hashed) in `schedule.db` and survive
> restarts. The table above lists only the *initial* passwords.
>
> **Forgot a password / full reset:** delete `schedule.db` and restart the
> server. This rebuilds all five accounts back to the initial passwords above
> (existing schedules are cleared).

---

## What it does
- Each person logs in and edits **their own** schedule.
- Per day (Monday–Sunday), up to **3 tasks**, each with a **time** and a **name**.
- They can plan **this week** and **next week**.
- Everyone sees a shared board with **all five** members' schedules.
- Works on Samsung/iPhone phones, MacBooks, and HP laptops (responsive layout).

---

## First-time setup (do this once)

1. **Install Python** on the Windows PC: https://www.python.org/downloads/
   During install, tick **"Add python.exe to PATH"**.
2. Copy this whole `family-schedule` folder onto the PC (e.g. `C:\family-schedule`).
3. Double-click **`setup.bat`**. It builds an isolated environment and installs
   everything. Wait for "Setup complete".

## Starting the server

- Double-click **`start-server.bat`**. Leave the window open — that window *is*
  the server. The site is now live on your home network.

## Finding the address family members type in

Everyone on the same home Wi-Fi opens this in their browser:

> ## `http://192.168.20.21:5000`

(That is this PC's current Wi-Fi address. If it ever changes, re-check it: open
Command Prompt, run `ipconfig`, and read the **"IPv4 Address"** under your Wi-Fi
adapter. To avoid changes, you can set a static/reserved IP for the PC in your
router — optional.)

Tip: on phones, use "Add to Home Screen" so it opens like an app.

> If other devices can't connect, allow it through the firewall **once**:
> the first time you start the server, Windows may pop up a "Windows Defender
> Firewall" prompt — tick **Private networks** and click **Allow access**.

---

## Keeping it on 24/7 (auto-start, runs in background)

So you don't have to keep a window open or restart it manually after a reboot:

1. Press `Win + R`, type `taskschd.msc`, press Enter (Task Scheduler).
2. Click **Create Task** (not "Basic Task").
3. **General** tab: name it `Family Schedule`. Tick **"Run whether user is
   logged on or not"** and **"Run with highest privileges"**.
4. **Triggers** tab → New → Begin the task: **At startup** → OK.
5. **Actions** tab → New → Program/script: browse to
   `C:\family-schedule\.venv\Scripts\pythonw.exe`
   Add argument: `serve.py`
   Start in: `C:\family-schedule`
6. **Settings** tab: tick **"If the task fails, restart every"** 1 minute,
   and untick "Stop the task if it runs longer than...".
7. OK. The server now starts automatically on boot and restarts if it crashes.
   (`pythonw.exe` runs it silently with no window.)

To stop it: in Task Scheduler, right-click the task → **End**, or **Disable**.

---

## Security notes (why this is "secure enough" for home use)
- **Not on the public internet** — only reachable by devices on your Wi-Fi.
- **Passwords are hashed** in the database (`schedule.db`), never stored in plain text.
- **Login required** for every page; each person can edit only their own schedule.
- Session cookies are HttpOnly + SameSite=Lax.
- A random `secret.key` is generated on first run and kept on the PC.

For convenience and to keep it minimal, the site uses plain HTTP on the local
network (no certificate setup). That is appropriate for a trusted home Wi-Fi.
If you ever decide to open it to the internet, additional steps (HTTPS,
stronger passwords) would be needed — ask before doing that.

---

## Where things are stored
- `schedule.db` — all schedules and accounts (back this up if you care about it).
- `secret.key` — session signing key (keep private; don't share or commit it).
