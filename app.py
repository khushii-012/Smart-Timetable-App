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

# ════════════════════════════════════════════
#  FIREBASE INIT
# ════════════════════════════════════════════
if not firebase_admin._apps:
    raw = os.environ.get("FIREBASE_CRED")
    if not raw:
        raise Exception("FIREBASE_CRED not found in environment variables")
    firebase_config = json.loads(raw)
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ════════════════════════════════════════════
#  PAGE CONFIG
# ════════════════════════════════════════════
st.set_page_config(
    page_title="Smart Timetable",
    page_icon="📅",
    layout="wide"
)

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
    st.title("📅 Smart Timetable Generator")
    st.markdown("---")

    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

    with tab_login:
        st.subheader("Login to your account")
        email    = st.text_input("Email", key="li_email")
        password = st.text_input("Password", type="password", key="li_pass")

        if st.button("Login", use_container_width=True):
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
        st.subheader("Create a new account")
        st.info("⚠️ Registration is open for testing. In production, restrict role selection to Admin only.")
        r_name  = st.text_input("Full Name",  key="reg_name")
        r_email = st.text_input("Email",      key="reg_email")
        r_pass  = st.text_input("Password",   type="password", key="reg_pass")
        r_role  = st.selectbox("Role", ["student", "teacher", "admin"], key="reg_role")

        if st.button("Register", use_container_width=True):
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

    tab1, tab2, tab3, tab4 = st.tabs(
        ["➕ Subjects", "⚙️ Generate", "📅 View Timetable", "✅ Change Requests"]
    )

    # ── TAB 1: SUBJECTS ──
    with tab1:
        st.subheader("Add Subject")
        c1, c2 = st.columns(2)
        sub_name = c1.text_input("Subject Name")
        faculty  = c2.text_input("Faculty Name")
        c3, c4, c5 = st.columns(3)
        hours    = c3.number_input("Hours/Week", 1, 10, 3)
        room     = c4.text_input("Room Number")
        type_    = c5.selectbox("Type", ["Theory", "Lab"])

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

        st.subheader("Current Subjects")
        subjects = get_subjects(sem_id)
        if not subjects:
            st.info("No subjects added yet for this semester.")
        for doc_id, d in subjects:
            cc = st.columns([3, 2, 1, 2, 1, 1])
            cc[0].write(d.get("subject", ""))
            cc[1].write(d.get("faculty", ""))
            cc[2].write(f"{d.get('hours',0)}h")
            cc[3].write(f"Rm {d.get('room','')}")
            cc[4].write(d.get("type",""))
            if cc[5].button("❌", key=f"del_{doc_id}"):
                db.collection("semesters").document(sem_id)\
                  .collection("subjects").document(doc_id).delete()
                st.rerun()

    # ── TAB 2: GENERATE ──
    with tab2:
        st.subheader("Generate Timetable")
        subjects = get_subjects(sem_id)
        if not subjects:
            st.warning("Add subjects first.")
        else:
            st.write(f"Found **{len(subjects)}** subjects for {sem}.")
            if st.button("🔄 Generate Timetable", use_container_width=True):
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
            df = pd.DataFrame(tt).T
            df.index.name = "Day"
            st.dataframe(df, use_container_width=True)

            st.subheader("✏️ Edit a Cell")
            e_day  = st.selectbox("Day",  DAYS,  key="e_day")
            e_time = st.selectbox("Time", [t for t in TIMES if t not in ["BREAK","LUNCH"]], key="e_time")
            current_val = tt.get(e_day, {}).get(e_time, "")
            new_val = st.text_input("New value", value=current_val, key="e_val")
            if st.button("Save Change"):
                tt[e_day][e_time] = new_val
                save_timetable(sem_id, tt)
                st.success("Saved!")
                st.rerun()

    # ── TAB 4: CHANGE REQUESTS ──
    with tab4:
        st.subheader("Pending Change Requests")
        reqs = get_pending_requests()
        if not reqs:
            st.success("No pending requests.")
        for req_id, req in reqs:
            with st.expander(f"📌 {req['sem_id']} | {req['day']} {req['time_slot']} — {req['requested_by']}"):
                st.write(f"**Reason:** {req['reason']}")
                st.write(f"**Submitted:** {req['timestamp'][:16]}")
                new_v = st.text_input("Replacement class (leave blank to free slot)",
                                      key=f"rv_{req_id}")
                cc = st.columns(2)
                if cc[0].button("✅ Approve", key=f"ap_{req_id}"):
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
                if cc[1].button("❌ Reject", key=f"rj_{req_id}"):
                    reject_change(req_id)
                    st.rerun()

        st.markdown("---")
        st.subheader("📣 Send Quick Announcement")
        ann_title = st.text_input("Title")
        ann_body  = st.text_area("Message")
        ann_sem   = st.selectbox("Send to", ["All users"] + SEMESTERS, key="ann_sem")
        if st.button("Send Notification", use_container_width=True):
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

        st.markdown("---")
        st.subheader("📜 Notification History")
        notifs = db.collection("notifications")\
                   .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                   .limit(20).stream()
        for n in notifs:
            nd = n.to_dict()
            st.write(f"**{nd['title']}** — {nd['body'][:60]}  "
                     f"_({nd['type']}, {nd['timestamp'][:16]})_")

# ════════════════════════════════════════════
#  UI — TEACHER DASHBOARD
# ════════════════════════════════════════════
def render_teacher():
    sem    = st.session_state.selected_sem
    sem_id = sem.replace(" ", "_").lower()

    st.title(f"👩‍🏫 Teacher Dashboard — {sem}")

    tab1, tab2, tab3 = st.tabs(
        ["📅 My Timetable", "🔄 Request Change", "📣 Quick Alert"]
    )

    with tab1:
        tt = load_timetable(sem_id)
        if not tt:
            st.info("No timetable available yet.")
        else:
            df = pd.DataFrame(tt).T
            st.dataframe(df, use_container_width=True)

            # Today's schedule highlight
            today = datetime.datetime.now().strftime("%A")
            if today in df.index:
                st.subheader(f"📍 Today — {today}")
                for t_slot in df.columns:
                    val = df.loc[today, t_slot]
                    if val and val not in ["☕ BREAK", "🍴 LUNCH"]:
                        if st.session_state.user_name in val or \
                           st.session_state.user_email.split("@")[0] in val:
                            st.success(f"**{t_slot}** — {val}")

    with tab2:
        st.subheader("Request Timetable Change")
        st.info("You can request a change for tomorrow's classes only.")
        tt = load_timetable(sem_id)
        if not tt:
            st.warning("No timetable loaded.")
        else:
            tomorrow_idx = (DAYS.index(datetime.datetime.now().strftime("%A")) + 1) % 6
            tomorrow = DAYS[tomorrow_idx]
            st.write(f"Requesting change for: **{tomorrow}**")
            avail_slots = [t for t in TIMES
                           if tt.get(tomorrow, {}).get(t, "") not in
                           ["", "☕ BREAK", "🍴 LUNCH"]]
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
        st.warning("This sends a push notification to all students in this semester.")
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

    st.title(f"🎓 Student View — {sem}")

    tab1, tab2 = st.tabs(["📅 Timetable", "🔔 Notifications"])

    with tab1:
        tt = load_timetable(sem_id)
        if not tt:
            st.info("Timetable not published yet for this semester.")
        else:
            df = pd.DataFrame(tt).T
            df.index.name = "Day"
            st.dataframe(df, use_container_width=True)

            # Today & next class
            now   = datetime.datetime.now()
            today = now.strftime("%A")
            current_hm = now.strftime("%H:%M")

            if today in df.index:
                st.subheader(f"📍 Today — {today}")
                current_class = None
                next_class    = None

                for t_slot in df.columns:
                    val = df.loc[today, t_slot]
                    if not val or val in ["☕ BREAK", "🍴 LUNCH"]:
                        continue
                    if t_slot <= current_hm:
                        current_class = (t_slot, val)
                    elif next_class is None:
                        next_class = (t_slot, val)

                if current_class:
                    st.success(f"🟢 **Now ({current_class[0]}):** {current_class[1]}")
                if next_class:
                    st.info(f"⏭ **Next ({next_class[0]}):** {next_class[1]}")
                if not current_class and not next_class:
                    st.info("No more classes today.")

            st.subheader("📅 Exam Schedule")
            exams = db.collection("exams").where("sem_id", "==", sem_id).stream()
            exam_list = [e.to_dict() for e in exams]
            if exam_list:
                st.dataframe(pd.DataFrame(exam_list), use_container_width=True)
            else:
                st.info("No exams scheduled yet.")

    with tab2:
        st.subheader("🔔 Recent Notifications")
        notifs = db.collection("notifications")\
                   .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                   .limit(15).stream()
        found = False
        for n in notifs:
            found = True
            nd = n.to_dict()
            icon = {"announcement":"📢","substitution":"🔄",
                    "teacher_alert":"⚠️"}.get(nd["type"], "🔔")
            st.markdown(
                f"{icon} **{nd['title']}** — {nd['body']}  \n"
                f"_Sent by {nd['sender']} at {nd['timestamp'][:16]}_"
            )
            st.markdown("---")
        if not found:
            st.info("No notifications yet.")

# ════════════════════════════════════════════
#  MAIN ROUTER
# ════════════════════════════════════════════
def main():
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