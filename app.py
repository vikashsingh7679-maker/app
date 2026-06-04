from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import Flask, g, jsonify, request, send_from_directory


ROOT = Path(__file__).parent
DB_PATH = ROOT / "work" / "rvitm_rooms.db"

app = Flask(__name__, static_folder="static", static_url_path="")


def db() -> sqlite3.Connection:
    if "db" not in g:
        DB_PATH.parent.mkdir(exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: Exception | None) -> None:
    conn = g.pop("db", None)
    if conn:
        conn.close()


def rows(query: str, args: tuple = ()) -> list[dict]:
    return [dict(row) for row in db().execute(query, args).fetchall()]


def one(query: str, args: tuple = ()) -> dict | None:
    row = db().execute(query, args).fetchone()
    return dict(row) if row else None


def token_user() -> dict | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.removeprefix("Bearer ").strip()
    return one("select * from users where token = ?", (token,))


def require_user(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = token_user()
        if not user:
            return jsonify({"error": "Login required"}), 401
        g.user = user
        return fn(*args, **kwargs)

    return wrapped


def require_roles(*roles: str):
    def outer(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = token_user()
            if not user:
                return jsonify({"error": "Login required"}), 401
            if user["role"] not in roles:
                return jsonify({"error": "Permission denied"}), 403
            g.user = user
            return fn(*args, **kwargs)

        return wrapped

    return outer


SCHEMA = """
create table if not exists users (
  id integer primary key autoincrement,
  name text not null,
  email text not null unique,
  role text not null,
  department text not null,
  token text not null unique
);

create table if not exists rooms (
  id integer primary key autoincrement,
  name text not null,
  building text not null,
  floor text not null,
  department text not null,
  type text not null,
  capacity integer not null,
  equipment text not null,
  image text not null,
  status text not null default 'available'
);

create table if not exists bookings (
  id integer primary key autoincrement,
  event_name text not null,
  organizer text not null,
  organizer_id integer not null,
  department text not null,
  room_id integer not null,
  purpose text not null,
  participants integer not null,
  event_date text not null,
  start_time text not null,
  end_time text not null,
  requirements text not null,
  status text not null,
  current_stage text not null,
  remarks text default '',
  created_at text not null,
  foreign key(room_id) references rooms(id),
  foreign key(organizer_id) references users(id)
);

create table if not exists notifications (
  id integer primary key autoincrement,
  user_id integer not null,
  title text not null,
  message text not null,
  is_read integer not null default 0,
  created_at text not null,
  foreign key(user_id) references users(id)
);
"""


def seed() -> None:
    conn = db()
    conn.executescript(SCHEMA)
    if one("select id from users limit 1"):
        return

    users = [
        ("Student Coordinator", "student@rvitm.edu.in", "student", "CSE", "student-demo"),
        ("Faculty Coordinator", "faculty@rvitm.edu.in", "faculty", "CSE", "faculty-demo"),
        ("Dr. HOD", "hod@rvitm.edu.in", "hod", "CSE", "hod-demo"),
        ("Admin Office", "admin@rvitm.edu.in", "admin", "Admin", "admin-demo"),
    ]
    conn.executemany(
        "insert into users (name, email, role, department, token) values (?, ?, ?, ?, ?)",
        users,
    )

    rooms = [
        (
            "Smart Classroom 402",
            "Main Block",
            "4",
            "CSE",
            "Classroom",
            72,
            "Projector, Smartboard, WiFi",
            "https://www.rvitm.edu.in/wp-content/uploads/2020/11/Design-and-Analysis-of-Algorithm-Laboratory-2-scaled-1.jpg",
            "available",
        ),
        (
            "DAA Lab",
            "CSE Block",
            "3",
            "CSE",
            "Computer Lab",
            60,
            "Lab PCs, Projector, WiFi",
            "https://www.rvitm.edu.in/wp-content/uploads/2020/11/Design-and-Analysis-of-Algorithm-Laboratory-2-scaled-1.jpg",
            "occupied",
        ),
        (
            "Microcontroller Lab",
            "ECE Block",
            "2",
            "ECE",
            "Electronics Lab",
            45,
            "Electronics benches, Oscilloscope, Projector",
            "https://www.rvitm.edu.in/wp-content/uploads/2020/08/Microcontroller-and-Embedded-Systems-Lab-1-scaled.jpg",
            "available",
        ),
        (
            "ECE Seminar Hall",
            "ECE Block",
            "1",
            "ECE",
            "Seminar Hall",
            120,
            "Projector, Sound System, WiFi",
            "https://www.rvitm.edu.in/wp-content/uploads/2020/11/electronic-devices-and-instrumentation-lab-1.jpg",
            "pending",
        ),
        (
            "Main Seminar Hall",
            "Seminar Wing",
            "1",
            "Admin",
            "Seminar Hall",
            180,
            "Projector, Sound System, WiFi, Stage",
            "https://www.rvitm.edu.in/wp-content/uploads/2023/12/Logo-1-white.png",
            "reserved",
        ),
        (
            "Conference Room 1",
            "Main Block",
            "2",
            "Admin",
            "Conference Room",
            30,
            "Display, WiFi, Whiteboard",
            "https://www.rvitm.edu.in/wp-content/uploads/2023/12/Logo-1-white.png",
            "available",
        ),
    ]
    conn.executemany(
        """
        insert into rooms
        (name, building, floor, department, type, capacity, equipment, image, status)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rooms,
    )

    now = datetime.now().isoformat(timespec="seconds")
    bookings = [
        (
            "AI Club Orientation",
            "Student Coordinator",
            1,
            "CSE",
            1,
            "Club induction and project briefing",
            60,
            "2026-06-05",
            "10:00",
            "12:00",
            "Projector, WiFi",
            "pending",
            "faculty",
            "",
            now,
        ),
        (
            "Placement Training",
            "Faculty Coordinator",
            2,
            "CSE",
            4,
            "Training session",
            110,
            "2026-06-06",
            "14:00",
            "16:00",
            "Projector, Sound System",
            "approved",
            "approved",
            "Approved by HOD",
            now,
        ),
    ]
    conn.executemany(
        """
        insert into bookings
        (event_name, organizer, organizer_id, department, room_id, purpose, participants,
         event_date, start_time, end_time, requirements, status, current_stage, remarks, created_at)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        bookings,
    )

    conn.executemany(
        "insert into notifications (user_id, title, message, created_at) values (?, ?, ?, ?)",
        [
            (1, "Request submitted", "AI Club Orientation is waiting for faculty review.", now),
            (2, "Approval pending", "A student booking request needs your review.", now),
            (3, "Room utilization", "ECE Seminar Hall has high demand this week.", now),
            (4, "System ready", "RVITM room allocation dashboard is seeded with demo data.", now),
        ],
    )
    conn.commit()


@app.before_request
def ensure_db() -> None:
    seed()


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/login")
def login():
    role = request.json.get("role", "student")
    user = one("select * from users where role = ?", (role,))
    if not user:
        return jsonify({"error": "Unknown role"}), 404
    return jsonify({"user": user, "token": user["token"]})


@app.get("/api/me")
@require_user
def me():
    return jsonify({"user": g.user})


@app.get("/api/dashboard")
@require_user
def dashboard():
    user = g.user
    stats = {
        "rooms": one("select count(*) as count from rooms")["count"],
        "available": one("select count(*) as count from rooms where status = 'available'")["count"],
        "pending": one("select count(*) as count from bookings where status = 'pending'")["count"],
        "approved": one("select count(*) as count from bookings where status = 'approved'")["count"],
    }
    if user["role"] == "student":
        stats["my_requests"] = one(
            "select count(*) as count from bookings where organizer_id = ?", (user["id"],)
        )["count"]
    return jsonify(
        {
            "stats": stats,
            "upcoming": rows(
                """
                select b.*, r.name as room_name from bookings b
                join rooms r on r.id = b.room_id
                order by b.event_date, b.start_time limit 5
                """
            ),
        }
    )


@app.get("/api/rooms")
@require_user
def rooms_api():
    query = request.args.get("q", "").lower()
    room_type = request.args.get("type", "")
    capacity = int(request.args.get("capacity", "0") or 0)
    sql = "select * from rooms where 1=1"
    args: list = []
    if query:
        sql += " and lower(name || building || department || equipment) like ?"
        args.append(f"%{query}%")
    if room_type:
        sql += " and type = ?"
        args.append(room_type)
    if capacity:
        sql += " and capacity >= ?"
        args.append(capacity)
    sql += " order by status, capacity"
    return jsonify({"rooms": rows(sql, tuple(args))})


@app.get("/api/bookings")
@require_user
def bookings_api():
    sql = """
      select b.*, r.name as room_name, r.building, r.type
      from bookings b join rooms r on r.id = b.room_id
    """
    args: tuple = ()
    if g.user["role"] == "student":
        sql += " where b.organizer_id = ?"
        args = (g.user["id"],)
    sql += " order by b.event_date desc, b.start_time"
    return jsonify({"bookings": rows(sql, args)})


def has_conflict(room_id: int, event_date: str, start: str, end: str) -> bool:
    conflict = one(
        """
        select id from bookings
        where room_id = ? and event_date = ? and status in ('pending', 'approved')
        and not (end_time <= ? or start_time >= ?)
        limit 1
        """,
        (room_id, event_date, start, end),
    )
    return conflict is not None


@app.post("/api/bookings")
@require_user
def create_booking():
    data = request.json
    room = one("select * from rooms where id = ?", (data["room_id"],))
    if not room:
        return jsonify({"error": "Room not found"}), 404
    if int(data["participants"]) > room["capacity"]:
        return jsonify({"error": "Participants exceed room capacity"}), 400
    if has_conflict(data["room_id"], data["event_date"], data["start_time"], data["end_time"]):
        alternatives = rows(
            "select * from rooms where id != ? and capacity >= ? and status = 'available' limit 3",
            (data["room_id"], int(data["participants"])),
        )
        return jsonify({"error": "Time conflict found", "alternatives": alternatives}), 409

    now = datetime.now().isoformat(timespec="seconds")
    conn = db()
    conn.execute(
        """
        insert into bookings
        (event_name, organizer, organizer_id, department, room_id, purpose, participants,
         event_date, start_time, end_time, requirements, status, current_stage, remarks, created_at)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'faculty', '', ?)
        """,
        (
            data["event_name"],
            g.user["name"],
            g.user["id"],
            data["department"],
            data["room_id"],
            data["purpose"],
            data["participants"],
            data["event_date"],
            data["start_time"],
            data["end_time"],
            data.get("requirements", ""),
            now,
        ),
    )
    faculty = one("select id from users where role = 'faculty' limit 1")
    if faculty:
        conn.execute(
            "insert into notifications (user_id, title, message, created_at) values (?, ?, ?, ?)",
            (faculty["id"], "New room request", f"{data['event_name']} needs review.", now),
        )
    conn.commit()
    return jsonify({"ok": True})


@app.post("/api/bookings/<int:booking_id>/approve")
@require_roles("faculty", "hod", "admin")
def approve_booking(booking_id: int):
    booking = one("select * from bookings where id = ?", (booking_id,))
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    stage = "hod" if g.user["role"] == "faculty" else "approved"
    status = "pending" if stage == "hod" else "approved"
    remark = request.json.get("remarks", "")
    conn = db()
    conn.execute(
        "update bookings set current_stage = ?, status = ?, remarks = ? where id = ?",
        (stage, status, remark, booking_id),
    )
    conn.execute(
        "insert into notifications (user_id, title, message, created_at) values (?, ?, ?, ?)",
        (
            booking["organizer_id"],
            "Booking updated",
            f"{booking['event_name']} moved to {stage}.",
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    return jsonify({"ok": True, "stage": stage})


@app.post("/api/bookings/<int:booking_id>/reject")
@require_roles("faculty", "hod", "admin")
def reject_booking(booking_id: int):
    remark = request.json.get("remarks", "Rejected")
    conn = db()
    conn.execute(
        "update bookings set current_stage = 'rejected', status = 'rejected', remarks = ? where id = ?",
        (remark, booking_id),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.get("/api/notifications")
@require_user
def notifications():
    return jsonify(
        {
            "notifications": rows(
                "select * from notifications where user_id = ? order by created_at desc",
                (g.user["id"],),
            )
        }
    )


@app.get("/api/analytics")
@require_roles("hod", "admin")
def analytics():
    return jsonify(
        {
            "room_usage": rows(
                """
                select r.name, count(b.id) as bookings
                from rooms r left join bookings b on b.room_id = r.id
                group by r.id order by bookings desc
                """
            ),
            "department_usage": rows(
                "select department, count(*) as bookings from bookings group by department"
            ),
        }
    )


@app.post("/api/admin/rooms")
@require_roles("admin")
def add_room():
    data = request.json
    db().execute(
        """
        insert into rooms (name, building, floor, department, type, capacity, equipment, image, status)
        values (?, ?, ?, ?, ?, ?, ?, ?, 'available')
        """,
        (
            data["name"],
            data["building"],
            data["floor"],
            data["department"],
            data["type"],
            data["capacity"],
            data.get("equipment", ""),
            data.get("image", "https://www.rvitm.edu.in/wp-content/uploads/2023/12/Logo-1-white.png"),
        ),
    )
    db().commit()
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
