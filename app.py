import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import pandas as pd
import random
import datetime
import os
import json
import requests
import threading
import time

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return None

# Load env variables from .env if present
load_dotenv()

# ════════════════════════════════════════════
#  FIREBASE INIT
# ════════════════════════════════════════════
if not firebase_admin._apps:
    raw = os.environ.get("FIREBASE_CRED")
    if raw:
        firebase_config = json.loads(raw)
        cred = credentials.Certificate(firebase_config)
    elif os.path.exists("firebase_key.json"):
        cred = credentials.Certificate("firebase_key.json")
    else:
        raise Exception("Neither FIREBASE_CRED env var nor firebase_key.json file found.")
    firebase_admin.initialize_app(cred)


db = firestore.client()




import streamlit as st

st.set_page_config(
    page_title="Smart Timetable App",
    page_icon="📅",
    layout="wide"
)

# Optional: hide default Streamlit header/footer
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)



# ════════════════════════════════════════════
#  PAGE CONFIG & CUSTOM STYLING
# ════════════════════════════════════════════
st.set_page_config(
    page_title="Smart Timetable",
    page_icon="📅",
    layout="wide"
)

def inject_custom_css():
    # Use your GitHub background.jpg as full-page background
    bg_url = "https://github.com/khushii-012/Smart-Timetable-App/raw/main/background.jpg"

    st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        /* Global styling with image + gradients */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-image:
                linear-gradient(135deg, rgba(60, 90, 200, 0.35), rgba(240, 98, 146, 0.35)),
                url("{bg_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #f1f5f9 !important;
            font-family: 'Inter', sans-serif !important;
        }}

        /* Custom typography */
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            color: #ffffff !important;
            letter-spacing: -0.5px;
        }}

        /* Modern Title Styling */
        h1 {{
            background: linear-gradient(135deg, #a5b4fc, #e9d5ff) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            margin-bottom: 0.5rem !important;
        }}

        /* Sidebar layout & glassmorphism */
        [data-testid="stSidebar"] {{
            background-color: rgba(15, 23, 42, 0.92) !important;
            backdrop-filter: blur(16px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.10) !important;
        }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
            color: #cbd5e1 !important;
        }}

        /* Styled Input Controls */
        div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
            background-color: rgba(15, 23, 42, 0.8) !important;
            border: 1px solid rgba(148, 163, 184, 0.4) !important;
            border-radius: 10px !important;
            transition: all 0.3s ease !important;
            color: #ffffff !important;
        }}
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, div[data-baseweb="textarea"]:focus-within {{
            border-color: #818cf8 !important;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.4) !important;
        }}
        div[data-baseweb="select"] span {{
            color: #ffffff !important;
        }}

        /* Streamlit Tabs styling */
        div[data-testid="stTabBar"] {{
            background-color: rgba(15, 23, 42, 0.75) !important;
            border-radius: 12px !important;
            padding: 6px !important;
            border: 1px solid rgba(148, 163, 184, 0.5) !important;
            gap: 6px !important;
        }}
        button[data-baseweb="tab"] {{
            border-radius: 999px !important;
            color: #94a3b8 !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            background-color: transparent !important;
            transition: all 0.2s ease !important;
            border-bottom: none !important;
            padding: 8px 18px !important;
        }}
        button[data-baseweb="tab"]:hover {{
            color: #cbd5e1 !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            background: linear-gradient(135deg, #6366f1, #a855f7) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 16px rgba(79, 70, 229, 0.45) !important;
            border: 1px solid rgba(129, 140, 248, 0.7) !important;
        }}

        /* Action buttons styles */
        div.stButton > button {{
            background: linear-gradient(135deg, #6366f1, #a855f7) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px 24px !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            box-shadow: 0 6px 18px rgba(79, 70, 229, 0.45) !important;
            transition: all 0.25s ease !important;
            width: 100% !important;
        }}
        div.stButton > button:hover {{
            background: linear-gradient(135deg, #4f46e5, #9333ea) !important;
            transform: translateY(-1.5px) !important;
        }}
        div.stButton > button:active {{
            transform: translateY(0) !important;
            box-shadow: 0 3px 12px rgba(79, 70, 229, 0.35) !important;
        }}

        /* Glass card wrapper for sections */
        .glass-card {{
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.5);
            border-radius: 18px;
            padding: 20px 24px;
            margin-bottom: 20px;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(16px);
        }}

        /* Divider overrides */
        hr {{
            border-color: rgba(148, 163, 184, 0.5) !important;
            margin: 1.5rem 0 !important;
        }}

        /* Styled Alert/Notification boxes */
        div[data-testid="stNotification"] {{
            background-color: rgba(15, 23, 42, 0.9) !important;
            border: 1px solid rgba(148, 163, 184, 0.5) !important;
            border-radius: 12px !important;
            color: #e2e8f0 !important;
        }}

        /* Hide native decoration and bars */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# Helper function to generate stats/KPI cards
def render_kpi_card(title, value, icon, gradient="linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15))"):
    st.markdown(f"""
    <div style="background: {gradient}; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 15px rgba(0,0,0,0.15); margin-bottom: 15px; border-left: 4px solid #6366f1;">
        <div>
            <div style="font-family: 'Outfit', sans-serif; font-size: 0.85rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.75px; margin-bottom: 4px;">{title}</div>
            <div style="font-family: 'Outfit', sans-serif; font-size: 1.8rem; font-weight: 700; color: #ffffff; line-height: 1.1;">{value}</div>
        </div>
        <div style="font-size: 2.2rem; filter: drop-shadow(0 0 8px rgba(255,255,255,0.1));">{icon}</div>
    </div>
    """, unsafe_allow_html=True)

# Helper to render notification alert feed items
def render_announcement_card(title, body, sender, timestamp, notif_type):
    icons = {
        "announcement": "📢",
        "substitution": "🔄",
        "teacher_alert": "⚠️"
    }
    icon = icons.get(notif_type, "🔔")
    
    border_colors = {
        "announcement": "#3b82f6",
        "substitution": "#10b981",
        "teacher_alert": "#f59e0b"
    }
    b_color = border_colors.get(notif_type, "#6366f1")
    
    # Format time
    try:
        dt = datetime.datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%b %d, %H:%M")
    except Exception:
        time_str = timestamp[:16]
        
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.35); border: 1px solid rgba(255, 255, 255, 0.06); border-left: 4px solid {b_color}; border-radius: 10px; padding: 16px; margin-bottom: 12px; display: flex; gap: 14px; align-items: flex-start; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
        <div style="font-size: 1.5rem; background: rgba(255,255,255,0.05); width: 42px; height: 42px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.05);">{icon}</div>
        <div style="flex-grow: 1;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 6px; gap: 8px;">
                <span style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1rem; color: #ffffff;">{title}</span>
                <span style="font-size: 0.72rem; color: #64748b; font-weight: 500;">{time_str}</span>
            </div>
            <p style="margin: 0 0 6px 0; color: #cbd5e1; font-size: 0.88rem; line-height: 1.45; font-family: 'Inter', sans-serif;">{body}</p>
            <div style="font-size: 0.72rem; color: #818cf8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.25px;">👤 {sender}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Helper function to generate custom colored HTML timetable grid
def get_custom_timetable_html(tt):
    if not tt:
        return "<div class='glass-card' style='text-align: center; color: #94a3b8;'>No timetable generated yet.</div>"
    
    # Elegant subject color mapping
    subject_colors = [
        "linear-gradient(135deg, #e0f2fe, #bae6fd)", # sky
        "linear-gradient(135deg, #f0fdf4, #dcfce7)", # green
        "linear-gradient(135deg, #faf5ff, #f3e8ff)", # purple
        "linear-gradient(135deg, #fef2f2, #fee2e2)", # red
        "linear-gradient(135deg, #fffbeb, #fef3c7)", # amber
        "linear-gradient(135deg, #fdf4ff, #fae8ff)", # fuchsia
        "linear-gradient(135deg, #f0fdfa, #ccfbf1)", # teal
        "linear-gradient(135deg, #eff6ff, #dbeafe)"  # blue
    ]
    
    unique_subs = set()
    for day in DAYS:
        if day in tt:
            for t in TIMES:
                val = tt[day].get(t, "")
                if val and val not in ["☕ BREAK", "🍴 LUNCH", "BREAK", "LUNCH"]:
                    # Extract subject name
                    sub_name = val.split(" (")[0]
                    unique_subs.add(sub_name)
                    
    sub_color_map = {}
    for idx, sub in enumerate(sorted(list(unique_subs))):
        sub_color_map[sub] = subject_colors[idx % len(subject_colors)]
        
    html = """
    <div style="width: 100%; overflow-x: auto; border-radius: 12px; background: rgba(30, 41, 59, 0.25); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.06); padding: 12px; box-sizing: border-box; margin-bottom: 25px;">
        <table style="width: 100%; border-collapse: separate; border-spacing: 8px; font-family: 'Outfit', sans-serif; color: #ffffff; min-width: 1000px;">
            <thead>
                <tr>
                    <th style="background: rgba(15, 23, 42, 0.6); border-radius: 8px; padding: 14px; font-weight: 700; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.75px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.05); color: #94a3b8; width: 100px;">Day</th>
    """
    
    time_display = {
        "9:30": "09:30 AM",
        "10:30": "10:30 AM",
        "LUNCH": "🍱 LUNCH",
        "12:00": "12:00 PM",
        "13:00": "01:00 PM",
        "14:00": "02:00 PM",
        "BREAK": "☕ BREAK",
        "14:30": "02:30 PM",
        "15:30": "03:30 PM"
    }
    
    for t in TIMES:
        html += f'<th style="background: rgba(15, 23, 42, 0.6); border-radius: 8px; padding: 14px; font-weight: 700; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.75px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.05); color: #94a3b8;">{time_display.get(t, t)}</th>'
    html += "</tr></thead><tbody>"
    
    for day in DAYS:
        html += f'<tr><td style="background: linear-gradient(135deg, #1e293b, #0f172a); border-radius: 8px; padding: 14px; font-weight: 700; text-align: center; vertical-align: middle; font-size: 0.88rem; border: 1px solid rgba(255, 255, 255, 0.08); color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">{day[:3]}</td>'
        day_slots = tt.get(day, {})
        for t in TIMES:
            val = day_slots.get(t, "")
            if not val or val == "FREE" or val == "Free period":
                html += '<td style="background: rgba(255, 255, 255, 0.01); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.03); padding: 10px; text-align: center; vertical-align: middle; min-width: 110px; color: rgba(255,255,255,0.15); font-size: 0.85rem;">-</td>'
            elif "BREAK" in val or "☕" in val:
                html += '<td style="background: rgba(255, 255, 255, 0.03); border-radius: 8px; border: 1px dashed rgba(255, 255, 255, 0.1); padding: 10px; text-align: center; vertical-align: middle; min-width: 110px; color: #64748b; font-style: italic; font-size: 0.78rem; font-weight: 600;">☕ BREAK</td>'
            elif "LUNCH" in val or "🍴" in val:
                html += '<td style="background: rgba(255, 255, 255, 0.03); border-radius: 8px; border: 1px dashed rgba(255, 255, 255, 0.1); padding: 10px; text-align: center; vertical-align: middle; min-width: 110px; color: #94a3b8; font-style: italic; font-size: 0.78rem; font-weight: 600;">🍱 LUNCH</td>'
            else:
                # E.g.: DBMS (Mrunali Mam, Rm F-35)
                sub_name = val.split(" (")[0]
                fac_room = val.split(" (")[1].replace(")", "") if " (" in val else ""
                fac = fac_room.split(", Rm ")[0] if ", Rm " in fac_room else fac_room
                room = fac_room.split(", Rm ")[1] if ", Rm " in fac_room else ""
                
                color = sub_color_map.get(sub_name, "linear-gradient(135deg, #1e293b, #0f172a)")
                
                html += f"""
                <td style="background: rgba(255, 255, 255, 0.02); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); padding: 8px; text-align: center; vertical-align: middle; min-width: 110px;">
                    <div style="background: {color}; border-radius: 6px; padding: 8px 6px; color: #0f172a; font-weight: 700; box-shadow: 0 4px 10px rgba(0,0,0,0.12); display: flex; flex-direction: column; gap: 3px; height: 100%; justify-content: center; transition: all 0.3s ease;">
                        <div style="font-size: 0.85rem; line-height: 1.15; font-family: 'Outfit', sans-serif;">{sub_name}</div>
                        <div style="font-size: 0.7rem; opacity: 0.8; font-weight: 500; font-family: 'Inter', sans-serif;">👤 {fac}</div>
                        {f'<div style="font-size: 0.7rem; opacity: 0.8; font-weight: 500; font-family: \'Inter\', sans-serif;">📍 Rm {room}</div>' if room else ''}
                    </div>
                </td>
                """
        html += "</tr>"
        
    html += "</tbody></table></div>"
    return html


# ════════════════════════════════════════════
#  SESSION STATE DEFAULTS
# ════════════════════════════════════════════
for key, val in {
    "logged_in": False,
    "user_email": None,
    "user_role": None,
    "user_uid": None,
    "user_name": None,
    "selected_sem": "Semester 1",
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ════════════════════════════════════════════
#  CONSTANTS
# ════════════════════════════════════════════
SEMESTERS = [f"Semester {i}" for i in range(1, 9)]
DAYS      = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
TIMES     = ["9:30", "10:30", "LUNCH", "12:00", "13:00", "14:00", "BREAK", "14:30", "15:30"]
FCM_KEY   = os.environ.get("FCM_SERVER_KEY", "")   # Add this to Render env vars

# ════════════════════════════════════════════
#  FIREBASE AUTH HELPERS  (REST API)
# ════════════════════════════════════════════
FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_WEB_API_KEY", "")

def sign_in_with_email(email: str, password: str):
    """Authenticate via Firebase Auth REST API, returns user dict or raises."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    r = requests.post(url, json=payload)
    data = r.json()
    if "error" in data:
        raise ValueError(data["error"]["message"])
    return data   # has localId, idToken, email

def register_user(email: str, password: str, name: str, role: str):
    """Create Firebase Auth account + Firestore profile."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    r = requests.post(url, json=payload)
    data = r.json()
    if "error" in data:
        raise ValueError(data["error"]["message"])
    uid = data["localId"]
    db.collection("users").document(uid).set({
        "name": name,
        "email": email,
        "role": role,
        "created_at": datetime.datetime.now().isoformat()
    })
    return uid

def get_user_profile(uid: str):
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None

# ════════════════════════════════════════════
#  FCM PUSH NOTIFICATION HELPER
# ════════════════════════════════════════════
def send_push_to_topic(topic: str, title: str, body: str):
    """Send FCM push notification to a topic (e.g. 'sem1_students')."""
    if not FCM_KEY:
        return False
    headers = {
        "Authorization": f"key={FCM_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": f"/topics/{topic}",
        "notification": {"title": title, "body": body},
        "data": {"click_action": "FLUTTER_NOTIFICATION_CLICK"}
    }
    r = requests.post("https://fcm.googleapis.com/fcm/send",
                      headers=headers, json=payload)
    return r.status_code == 200

def send_push_to_all(title: str, body: str):
    send_push_to_topic("all_users", title, body)

def log_notification(title: str, body: str, sender: str, notif_type: str):
    db.collection("notifications").add({
        "title": title,
        "body": body,
        "sender": sender,
        "type": notif_type,
        "timestamp": datetime.datetime.now().isoformat()
    })

# ════════════════════════════════════════════
#  SCHEDULED NOTIFICATION CHECKER
#  Runs in background thread — fires FCM
#  15 min before each lecture
# ════════════════════════════════════════════
def notification_scheduler():
    while True:
        try:
            now = datetime.datetime.now()
            today = now.strftime("%A")
            current_hm = now.strftime("%H:%M")

            # Check all semesters
            for sem in SEMESTERS:
                sem_id = sem.replace(" ", "_").lower()
                tt_doc = db.collection("timetables").document(sem_id).get()
                if not tt_doc.exists:
                    continue
                tt = tt_doc.to_dict()
                if today not in tt:
                    continue

                day_row = tt[today]
                for time_slot, value in day_row.items():
                    if not value or value in ["☕ BREAK", "🍴 LUNCH"]:
                        continue
                    try:
                        slot_dt = datetime.datetime.strptime(time_slot, "%H:%M")
                        slot_today = now.replace(hour=slot_dt.hour,
                                                  minute=slot_dt.minute, second=0)
                        diff = (slot_today - now).total_seconds()
                        # Fire notification 15 min (900s) before, within a 60s window
                        if 840 < diff <= 900:
                            topic = f"{sem_id}_students"
                            send_push_to_topic(
                                topic,
                                f"📚 Class in 15 min — {sem}",
                                value
                            )
                    except ValueError:
                        pass
        except Exception:
            pass
        time.sleep(60)   # check every minute

# Start scheduler once per process
if "scheduler_started" not in st.session_state:
    t = threading.Thread(target=notification_scheduler, daemon=True)
    t.start()
    st.session_state["scheduler_started"] = True

# ════════════════════════════════════════════
#  TIMETABLE HELPERS
# ════════════════════════════════════════════
def get_subjects(sem_id: str):
    docs = db.collection("semesters").document(sem_id)\
              .collection("subjects").stream()
    return [(doc.id, doc.to_dict()) for doc in docs]

def save_timetable(sem_id: str, timetable: dict):
    db.collection("timetables").document(sem_id).set(timetable)

def load_timetable(sem_id: str):
    doc = db.collection("timetables").document(sem_id).get()
    return doc.to_dict() if doc.exists else None

def generate_timetable(subjects_list):
    timetable = {day: {t: "" for t in TIMES} for day in DAYS}
    slots = []
    for sub in subjects_list:
        if sub["type"] == "Lab":
            for _ in range(sub["hours"] // 2):
                slots.append({"data": sub, "block": 2})
        else:
            for _ in range(sub["hours"]):
                slots.append({"data": sub, "block": 1})

    random.shuffle(slots)

    for day in DAYS:
        i = 0
        day_slots = list(slots)
        random.shuffle(day_slots)
        si = 0
        while i < len(TIMES):
            t = TIMES[i]
            if t == "BREAK":
                timetable[day][t] = "☕ BREAK"
                i += 1
                continue
            if t == "LUNCH":
                timetable[day][t] = "🍴 LUNCH"
                i += 1
                continue
            if si >= len(day_slots):
                i += 1
                continue
            slot = day_slots[si]
            sub  = slot["data"]
            if slot["block"] == 2 and i + 1 < len(TIMES):
                next_t = TIMES[i + 1]
                if next_t not in ["BREAK", "LUNCH"]:
                    val = f"{sub['subject']} ({sub['faculty']}, Rm {sub['room']})"
                    timetable[day][t]      = val
                    timetable[day][next_t] = val
                    si += 1
                    i  += 2
                    continue
            timetable[day][t] = f"{sub['subject']} ({sub['faculty']}, Rm {sub['room']})"
            si += 1
            i  += 1
    return timetable

# ════════════════════════════════════════════
#  CHANGE REQUEST HELPERS
# ════════════════════════════════════════════
def request_change(sem_id, day, time_slot, reason, teacher_email):
    db.collection("change_requests").add({
        "sem_id":       sem_id,
        "day":          day,
        "time_slot":    time_slot,
        "reason":       reason,
        "requested_by": teacher_email,
        "status":       "pending",
        "timestamp":    datetime.datetime.now().isoformat()
    })

def get_pending_requests():
    docs = db.collection("change_requests")\
              .where("status", "==", "pending").stream()
    return [(doc.id, doc.to_dict()) for doc in docs]

def approve_change(req_id, sem_id, day, time_slot, new_value):
    tt = load_timetable(sem_id) or {}
    if day in tt:
        tt[day][time_slot] = new_value
        save_timetable(sem_id, tt)
    db.collection("change_requests").document(req_id).update({
        "status": "approved",
        "approved_at": datetime.datetime.now().isoformat()
    })

def reject_change(req_id):
    db.collection("change_requests").document(req_id).update({
        "status": "rejected"
    })

def can_edit_today(target_day: str) -> bool:
    """Allow edits only if today is the day BEFORE the target day."""
    day_order = DAYS
    if target_day not in day_order:
        return False
    idx = day_order.index(target_day)
    yesterday_idx = (idx - 1) % len(day_order)
    today_name = datetime.datetime.now().strftime("%A")
    return today_name == day_order[yesterday_idx]

# ════════════════════════════════════════════
#  UI — LOGIN PAGE
# ════════════════════════════════════════════
def render_login():
    st.markdown("""
    <div style="text-align: center; padding: 30px 0 15px 0;">
        <span style="font-size: 3.5rem; filter: drop-shadow(0 0 12px rgba(99,102,241,0.3));">📅</span>
        <h1 style="margin-top: 15px; font-size: 2.6rem; font-weight: 800; background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family: 'Outfit', sans-serif;">Smart Timetable</h1>
        <p style="color: #94a3b8; font-size: 1.05rem; margin-top: -5px; font-family: 'Inter', sans-serif;">Conflict-free scheduling, live updates, and instant alerts.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='margin: 0 0 25px 0 !important;'>", unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔐 Login Portal", "📝 Register Account"])

    with tab_login:
        st.subheader("Sign In")
        email    = st.text_input("Email Address", key="li_email")
        password = st.text_input("Password", type="password", key="li_pass")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Sign In", use_container_width=True):
            if not FIREBASE_WEB_API_KEY:
                st.error("FIREBASE_WEB_API_KEY env var not set on Render.")
                return
            try:
                user_data = sign_in_with_email(email, password)
                uid       = user_data["localId"]
                profile   = get_user_profile(uid)
                if not profile:
                    st.error("User profile not found. Please register first.")
                    return
                st.session_state.logged_in  = True
                st.session_state.user_uid   = uid
                st.session_state.user_email = email
                st.session_state.user_role  = profile["role"]
                st.session_state.user_name  = profile.get("name", email)
                st.rerun()
            except ValueError as e:
                st.error(f"Login failed: {e}")

    with tab_register:
        st.subheader("Register Profile")
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px; padding: 12px; margin-bottom: 20px; color: #fcd34d; font-size: 0.85rem; font-family: 'Inter', sans-serif; line-height: 1.45;">
            ⚠️ <strong>Testing Environment:</strong> Registration is currently open for testing. In active production, role management should be restricted to administrators.
        </div>
        """, unsafe_allow_html=True)
        r_name  = st.text_input("Full Name",  key="reg_name")
        r_email = st.text_input("Email Address",      key="reg_email")
        r_pass  = st.text_input("Password",   type="password", key="reg_pass")
        r_role  = st.selectbox("Select Role", ["student", "teacher", "admin"], key="reg_role")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Register Account", use_container_width=True):
            if not FIREBASE_WEB_API_KEY:
                st.error("FIREBASE_WEB_API_KEY env var not set on Render.")
                return
            try:
                register_user(r_email, r_pass, r_name, r_role)
                st.success("✅ Account created! Please login.")
            except ValueError as e:
                st.error(f"Registration failed: {e}")

# ════════════════════════════════════════════
#  UI — SIDEBAR
# ════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        st.markdown(f"**Role:** `{st.session_state.user_role.upper()}`")
        st.markdown(f"**Email:** {st.session_state.user_email}")
        st.markdown("---")

        st.session_state.selected_sem = st.selectbox(
            "📚 Semester", SEMESTERS, key="sem_select"
        )

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["logged_in","user_email","user_role","user_uid","user_name"]:
                st.session_state[k] = None if k != "logged_in" else False
            st.rerun()

# ════════════════════════════════════════════
#  UI — ADMIN DASHBOARD
# ════════════════════════════════════════════
def render_admin():
    sem    = st.session_state.selected_sem
    sem_id = sem.replace(" ", "_").lower()

    st.title(f"🛠️ Admin Dashboard — {sem}")

    # Top KPI Metrics row
    c_stats1, c_stats2, c_stats3 = st.columns(3)
    subjects = get_subjects(sem_id)
    reqs = get_pending_requests()
    
    with c_stats1:
        render_kpi_card("Active Semester", sem, "📚", "linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(168, 85, 247, 0.12))")
    with c_stats2:
        render_kpi_card("Subjects Registered", f"{len(subjects)} Course(s)", "➕", "linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(5, 150, 105, 0.12))")
    with c_stats3:
        render_kpi_card("Substitution Requests", f"{len(reqs)} Pending Action", "⚠️", "linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(217, 119, 6, 0.12))")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["➕ Add Subjects", "⚙️ Timetable Generator", "📅 Schedule Grid", "✅ Change Requests"]
    )

    # ── TAB 1: SUBJECTS ──
    with tab1:
        st.subheader("Register Subject Details")
        c1, c2 = st.columns(2)
        sub_name = c1.text_input("Subject Name")
        faculty  = c2.text_input("Faculty Name")
        c3, c4, c5 = st.columns(3)
        hours    = c3.number_input("Hours/Week", 1, 10, 3)
        room     = c4.text_input("Room Number")
        type_    = c5.selectbox("Type", ["Theory", "Lab"])

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Add Subject", use_container_width=True):
            if sub_name and faculty and room:
                db.collection("semesters").document(sem_id)\
                  .collection("subjects").add({
                      "subject": sub_name, "faculty": faculty,
                      "hours": hours, "room": room, "type": type_
                  })
                st.success("✅ Subject added!")
                st.rerun()
            else:
                st.warning("Fill all fields")

        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        st.subheader("Current Registered Subjects")
        if not subjects:
            st.info("No subjects added yet for this semester.")
        
        for doc_id, d in subjects:
            c_card, c_del = st.columns([6, 1])
            with c_card:
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.35); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 14px 18px; border-left: 4px solid #818cf8; margin-bottom: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.05rem; color: #ffffff;">{d.get('subject','')} <span style="font-size: 0.72rem; background: rgba(99,102,241,0.2); color: #a5b4fc; padding: 3px 10px; border-radius: 12px; font-weight: 600; margin-left: 8px; text-transform: uppercase; letter-spacing: 0.5px;">{d.get('type','')}</span></div>
                    <div style="font-size: 0.84rem; color: #94a3b8; margin-top: 4px; font-family: 'Inter', sans-serif;">👨‍🏫 {d.get('faculty','')} &nbsp;|&nbsp; 🕒 {d.get('hours',0)} hrs/week &nbsp;|&nbsp; 📍 Room {d.get('room','')}</div>
                </div>
                """, unsafe_allow_html=True)
            with c_del:
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("❌", key=f"del_{doc_id}", use_container_width=True):
                    db.collection("semesters").document(sem_id)\
                      .collection("subjects").document(doc_id).delete()
                    st.rerun()

    # ── TAB 2: GENERATE ──
    with tab2:
        st.subheader("Generate Semester Timetable")
        st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #a5b4fc; font-family: 'Inter', sans-serif; font-size: 0.88rem; line-height: 1.45;">
            ℹ️ <strong>Auto-Allocation Engine:</strong> The system assigns laboratory sessions in continuous blocks and distributes theory classes evenly to resolve conflicts.
        </div>
        """, unsafe_allow_html=True)
        
        if not subjects:
            st.warning("Add subjects first.")
        else:
            st.write(f"Found **{len(subjects)}** subjects registered for {sem}.")
            if st.button("🔄 Generate conflict-free timetable", use_container_width=True):
                subject_list = [d for _, d in subjects]
                tt = generate_timetable(subject_list)
                save_timetable(sem_id, tt)
                st.success("✅ Timetable generated and saved!")
                st.rerun()

    # ── TAB 3: VIEW TIMETABLE ──
    with tab3:
        tt = load_timetable(sem_id)
        if not tt:
            st.info("No timetable generated yet for this semester.")
        else:
            # Styled Custom Timetable View
            st.markdown(get_custom_timetable_html(tt), unsafe_allow_html=True)

            st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
            st.subheader("✏️ Manual Cell Editor")
            e_day  = st.selectbox("Select Target Day",  DAYS,  key="e_day")
            e_time = st.selectbox("Select Time Slot", [t for t in TIMES if t not in ["BREAK","LUNCH"]], key="e_time")
            current_val = tt.get(e_day, {}).get(e_time, "")
            new_val = st.text_input("Edit Cell Value", value=current_val, key="e_val")
            if st.button("Save Manual Override", use_container_width=True):
                tt[e_day][e_time] = new_val
                save_timetable(sem_id, tt)
                st.success("Saved override!")
                st.rerun()

    # ── TAB 4: CHANGE REQUESTS ──
    with tab4:
        st.subheader("Pending Substitution Requests")
        if not reqs:
            st.success("No pending change requests.")
        for req_id, req in reqs:
            with st.expander(f"📌 {req['sem_id'].upper().replace('_', ' ')} | {req['day']} {req['time_slot']} — Requested by {req['requested_by']}"):
                st.write(f"**Reason:** {req['reason']}")
                st.write(f"**Submitted:** {req['timestamp'][:16]}")
                new_v = st.text_input("Replacement class (leave blank to free slot)",
                                      key=f"rv_{req_id}")
                cc = st.columns(2)
                if cc[0].button("✅ Approve Request", key=f"ap_{req_id}"):
                    approve_change(req_id, req["sem_id"],
                                   req["day"], req["time_slot"],
                                   new_v or "FREE")
                    send_push_to_topic(
                        f"{req['sem_id']}_students",
                        "📢 Timetable Change",
                        f"{req['day']} {req['time_slot']} updated: {new_v or 'Free period'}"
                    )
                    log_notification("Timetable Change",
                                     f"{req['day']} {req['time_slot']}: {new_v or 'Free period'}",
                                     "admin", "substitution")
                    st.success("Approved & notification sent!")
                    st.rerun()
                if cc[1].button("❌ Reject Request", key=f"rj_{req_id}"):
                    reject_change(req_id)
                    st.rerun()

        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        st.subheader("📣 Send Quick Announcement")
        ann_title = st.text_input("Title")
        ann_body  = st.text_area("Message")
        ann_sem   = st.selectbox("Send to Audience", ["All users"] + SEMESTERS, key="ann_sem")
        if st.button("Send Announcement Alert", use_container_width=True):
            if ann_title and ann_body:
                topic = "all_users" if ann_sem == "All users" \
                        else ann_sem.replace(" ","_").lower() + "_students"
                ok = send_push_to_topic(topic, ann_title, ann_body)
                log_notification(ann_title, ann_body,
                                 st.session_state.user_email, "announcement")
                st.success("✅ Notification sent!" if ok else
                           "⚠️ Logged (FCM key not set — push skipped)")
            else:
                st.warning("Fill title and message.")

        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        st.subheader("📜 Notification History Logs")
        notifs = db.collection("notifications")\
                   .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                   .limit(20).stream()
        for n in notifs:
            nd = n.to_dict()
            render_announcement_card(
                nd.get("title", "Announcement"),
                nd.get("body", ""),
                nd.get("sender", "Admin"),
                nd.get("timestamp", ""),
                nd.get("type", "announcement")
            )

# ════════════════════════════════════════════
#  UI — TEACHER DASHBOARD
# ════════════════════════════════════════════
def render_teacher():
    sem    = st.session_state.selected_sem
    sem_id = sem.replace(" ", "_").lower()

    st.title(f"👩‍🏫 Teacher Dashboard — {sem}")

    tab1, tab2, tab3 = st.tabs(
        ["📅 Schedule Overview", "🔄 Substitution Request", "📣 Quick Alert"]
    )

    with tab1:
        tt = load_timetable(sem_id)
        if not tt:
            st.info("No timetable available yet.")
        else:
            st.markdown(get_custom_timetable_html(tt), unsafe_allow_html=True)

            # Today's schedule highlight
            today = datetime.datetime.now().strftime("%A")
            if today in tt:
                st.markdown(f"<h3 style='margin-top: 20px;'>📍 Your Schedule Today — {today}</h3>", unsafe_allow_html=True)
                has_classes = False
                
                # Sort TIMES
                slot_times = []
                for slot in TIMES:
                    try:
                        t_parsed = datetime.datetime.strptime(slot, "%H:%M").time()
                        slot_times.append((t_parsed, slot))
                    except ValueError:
                        pass
                slot_times.sort()
                
                for _, t_slot in slot_times:
                    val = tt[today].get(t_slot, "")
                    if val and val not in ["☕ BREAK", "🍴 LUNCH", "BREAK", "LUNCH"]:
                        # Check if this teacher is teaching this class
                        teacher_name = st.session_state.user_name.lower()
                        teacher_email_prefix = st.session_state.user_email.split("@")[0].lower()
                        val_lower = val.lower()
                        
                        if teacher_name in val_lower or teacher_email_prefix in val_lower:
                            has_classes = True
                            sub_name = val.split(" (")[0]
                            fac_room = val.split(" (")[1].replace(")", "") if " (" in val else ""
                            room = fac_room.split(", Rm ")[1] if ", Rm " in fac_room else ""
                            
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(168, 85, 247, 0.12)); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 18px; margin-bottom: 12px; border-left: 5px solid #818cf8; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                                <div>
                                    <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.1rem; color: #ffffff;">{sub_name}</div>
                                    <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px; font-family: 'Inter', sans-serif;">📍 Room {room if room else '-'}</div>
                                </div>
                                <div style="font-family: 'Outfit', sans-serif; font-weight: 600; font-size: 0.88rem; color: #e9d5ff; background: rgba(99,102,241,0.25); padding: 4px 14px; border-radius: 20px;">🕒 {t_slot}</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                if not has_classes:
                    st.markdown("""
                    <div style="background: rgba(30, 41, 59, 0.2); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 20px; text-align: center; color: #94a3b8; font-family: 'Inter', sans-serif;">
                        🎉 No teaching hours scheduled for you today. Have a productive day!
                    </div>
                    """, unsafe_allow_html=True)

    with tab2:
        st.subheader("Request Timetable Change")
        st.markdown("""
        <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.15); border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #93c5fd; font-family: 'Inter', sans-serif; font-size: 0.88rem; line-height: 1.45;">
            ℹ️ <strong>Substitution System:</strong> You can submit a change request for tomorrow's classes. Once approved by the administrator, students will receive an instant push notification and the schedule will update.
        </div>
        """, unsafe_allow_html=True)
        
        tt = load_timetable(sem_id)
        if not tt:
            st.warning("No timetable loaded.")
        else:
            tomorrow_idx = (DAYS.index(datetime.datetime.now().strftime("%A")) + 1) % len(DAYS)
            tomorrow = DAYS[tomorrow_idx]
            st.markdown(f"##### Target Day: **{tomorrow}**")
            avail_slots = [t for t in TIMES
                           if tt.get(tomorrow, {}).get(t, "") not in
                           ["", "☕ BREAK", "🍴 LUNCH", "BREAK", "LUNCH"]]
            if not avail_slots:
                st.info("No classes scheduled for tomorrow.")
            else:
                r_slot   = st.selectbox("Class to change", avail_slots)
                r_reason = st.selectbox("Reason",
                    ["Absent", "Official meeting", "Medical leave", "Other"])
                r_note   = st.text_area("Additional note (optional)")

                if st.button("Submit Change Request", use_container_width=True):
                    request_change(
                        sem_id, tomorrow, r_slot,
                        f"{r_reason}: {r_note}",
                        st.session_state.user_email
                    )
                    st.success("✅ Request submitted. Admin will review it.")

    with tab3:
        st.subheader("Send Quick Alert to Students")
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #fcd34d; font-family: 'Inter', sans-serif; font-size: 0.88rem; line-height: 1.45;">
            ⚠️ <strong>Alert Broadcast:</strong> This will publish an announcement card to the student feed and trigger push notifications for all students in this semester.
        </div>
        """, unsafe_allow_html=True)
        
        al_title = st.text_input("Alert title")
        al_body  = st.text_area("Message")
        if st.button("Send Alert", use_container_width=True):
            if al_title and al_body:
                topic = f"{sem_id}_students"
                ok = send_push_to_topic(topic, al_title, al_body)
                log_notification(al_title, al_body,
                                 st.session_state.user_email, "teacher_alert")
                st.success("✅ Alert sent!" if ok else
                           "⚠️ Logged (FCM key needed for real push)")
            else:
                st.warning("Fill both fields.")

# ════════════════════════════════════════════
#  UI — STUDENT DASHBOARD
# ════════════════════════════════════════════
def render_student():
    sem    = st.session_state.selected_sem
    sem_id = sem.replace(" ", "_").lower()

    st.title(f"🎓 Student Dashboard — {sem}")

    tab1, tab2 = st.tabs(["📅 Custom Timetable", "🔔 Recent Notifications"])

    with tab1:
        tt = load_timetable(sem_id)
        if not tt:
            st.info("Timetable not published yet for this semester.")
        else:
            # Render styled HTML timetable
            st.markdown(get_custom_timetable_html(tt), unsafe_allow_html=True)

            # Today & next class
            now   = datetime.datetime.now()
            today = now.strftime("%A")

            if today in tt:
                st.subheader(f"📍 Class Schedule — {today}")
                
                # Use our proper datetime parser helper
                day_tt = tt[today]
                
                # Parse slot times
                slot_times = []
                for slot in TIMES:
                    try:
                        t_parsed = datetime.datetime.strptime(slot, "%H:%M").time()
                        slot_times.append((t_parsed, slot))
                    except ValueError:
                        pass
                slot_times.sort()
                
                current_class = None
                next_class = None
                
                for idx, (t_parsed, slot) in enumerate(slot_times):
                    val = day_tt.get(slot, "")
                    if not val or val in ["☕ BREAK", "🍴 LUNCH", "BREAK", "LUNCH"]:
                        continue
                    
                    # Assume class duration is 1 hour
                    start_dt = datetime.datetime.combine(now.date(), t_parsed)
                    end_dt = start_dt + datetime.timedelta(hours=1)
                    
                    if start_dt <= now < end_dt:
                        current_class = (slot, val)
                    elif start_dt > now and next_class is None:
                        next_class = (slot, val)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if current_class:
                        slot, val = current_class
                        sub_name = val.split(" (")[0]
                        fac_room = val.split(" (")[1].replace(")", "") if " (" in val else ""
                        fac = fac_room.split(", Rm ")[0] if ", Rm " in fac_room else fac_room
                        room = fac_room.split(", Rm ")[1] if ", Rm " in fac_room else ""
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(5, 150, 105, 0.12)); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(16,185,129,0.15); border-left: 5px solid #10b981; height: 100%;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 0.9rem; color: #10b981; text-transform: uppercase; letter-spacing: 0.5px;">🟢 ACTIVE CLASS</span>
                                <span style="font-family: 'Outfit', sans-serif; font-size: 0.85rem; color: #a7f3d0; background: rgba(16,185,129,0.15); padding: 3px 10px; border-radius: 20px; font-weight: 600;">{slot}</span>
                            </div>
                            <h4 style="margin: 12px 0 6px 0; color: #ffffff; font-family: 'Outfit', sans-serif; font-size: 1.2rem; font-weight: 700;">{sub_name}</h4>
                            <div style="font-size: 0.88rem; color: #cbd5e1; font-family: 'Inter', sans-serif; margin-bottom: 2px;">👤 {fac}</div>
                            {f'<div style="font-size: 0.88rem; color: #cbd5e1; font-family: \'Inter\', sans-serif;">📍 Room {room}</div>' if room else ''}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="background: rgba(30, 41, 59, 0.25); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 20px; text-align: center; color: #94a3b8; font-family: 'Inter', sans-serif; border-left: 5px solid rgba(255, 255, 255, 0.1); height: 100%; display: flex; align-items: center; justify-content: center; min-height: 120px;">
                            <div>☕ No Active Lecture at this time</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                with col2:
                    if next_class:
                        slot, val = next_class
                        sub_name = val.split(" (")[0]
                        fac_room = val.split(" (")[1].replace(")", "") if " (" in val else ""
                        fac = fac_room.split(", Rm ")[0] if ", Rm " in fac_room else fac_room
                        room = fac_room.split(", Rm ")[1] if ", Rm " in fac_room else ""
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(168, 85, 247, 0.12)); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(99,102,241,0.15); border-left: 5px solid #6366f1; height: 100%;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 0.9rem; color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.5px;">⏭ UP NEXT</span>
                                <span style="font-family: 'Outfit', sans-serif; font-size: 0.85rem; color: #e9d5ff; background: rgba(99,102,241,0.15); padding: 3px 10px; border-radius: 20px; font-weight: 600;">{slot}</span>
                            </div>
                            <h4 style="margin: 12px 0 6px 0; color: #ffffff; font-family: 'Outfit', sans-serif; font-size: 1.2rem; font-weight: 700;">{sub_name}</h4>
                            <div style="font-size: 0.88rem; color: #cbd5e1; font-family: 'Inter', sans-serif; margin-bottom: 2px;">👤 {fac}</div>
                            {f'<div style="font-size: 0.88rem; color: #cbd5e1; font-family: \'Inter\', sans-serif;">📍 Room {room}</div>' if room else ''}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="background: rgba(30, 41, 59, 0.25); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 20px; text-align: center; color: #94a3b8; font-family: 'Inter', sans-serif; border-left: 5px solid rgba(255, 255, 255, 0.1); height: 100%; display: flex; align-items: center; justify-content: center; min-height: 120px;">
                            <div>🎉 No more lectures scheduled today!</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
            st.subheader("📅 Exam Schedule")
            exams = db.collection("exams").where("sem_id", "==", sem_id).stream()
            exam_list = [e.to_dict() for e in exams]
            if exam_list:
                # Custom render exam schedule as a list of styled cards
                cols = st.columns(3)
                for idx, exam in enumerate(exam_list):
                    col_target = cols[idx % 3]
                    with col_target:
                        st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 15px; margin-bottom: 15px; border-top: 3px solid #f43f5e; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                            <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.05rem; color: #ffffff; margin-bottom: 8px;">📝 {exam.get('subject', 'Exam')}</div>
                            <div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 4px; font-family: 'Inter', sans-serif;">📅 <strong>Date:</strong> {exam.get('date', '-')}</div>
                            <div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 4px; font-family: 'Inter', sans-serif;">🕒 <strong>Time:</strong> {exam.get('time', '-')}</div>
                            <div style="font-size: 0.85rem; color: #cbd5e1; font-family: 'Inter', sans-serif;">📍 <strong>Room:</strong> {exam.get('room', '-')}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(30, 41, 59, 0.15); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 15px; text-align: center; color: #64748b; font-family: 'Inter', sans-serif;">
                    No upcoming exams scheduled.
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.subheader("Recent Notifications Feed")
        notifs = db.collection("notifications")\
                   .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                   .limit(15).stream()
        found = False
        
        for n in notifs:
            found = True
            nd = n.to_dict()
            render_announcement_card(
                nd.get("title", "Notification"),
                nd.get("body", ""),
                nd.get("sender", "Admin"),
                nd.get("timestamp", ""),
                nd.get("type", "announcement")
            )
            
        if not found:
            st.markdown("""
            <div style="background: rgba(30, 41, 59, 0.15); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 20px; text-align: center; color: #64748b; font-family: 'Inter', sans-serif;">
                🔔 No notifications yet. You're all caught up!
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════
#  MAIN ROUTER
# ════════════════════════════════════════════
def main():
    inject_custom_css()
    if not st.session_state.logged_in:
        render_login()
        return

    render_sidebar()
    role = st.session_state.user_role

    if role == "admin":
        render_admin()
    elif role == "teacher":
        render_teacher()
    elif role == "student":
        render_student()
    else:
        st.error("Unknown role. Contact admin.")

if __name__ == "__main__":
    main()