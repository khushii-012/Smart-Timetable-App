import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import random
import datetime
import os
import json

# ---------------- FIREBASE INIT ---------------- #
# ---------------- FIREBASE INIT ---------------- #
if not firebase_admin._apps:

    raw = os.environ.get("FIREBASE_CRED")

    if not raw:
        raise Exception("FIREBASE_CRED not found in environment variables")

    firebase_config = json.loads(raw)

    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()
# ---------------- TITLE ---------------- #
st.title("📅 Smart Auto Timetable Generator")

# ---------------- ADD SUBJECT ---------------- #
st.subheader("➕ Add Subject Details")

subject_name = st.text_input("Subject Name", key="sub_name")
faculty = st.text_input("Faculty Name", key="faculty")
hours = st.number_input("Hours per Week", min_value=1, max_value=10, key="hours")
room = st.text_input("Room Number", key="room")
type_ = st.selectbox("Type", ["Theory", "Lab"], key="type")

if st.button("Add Subject"):
    if subject_name and faculty and room:
        db.collection("subjects").add({
            "subject": subject_name,
            "faculty": faculty,
            "hours": hours,
            "room": room,
            "type": type_
        })
        st.success("✅ Subject Added!")
    else:
        st.warning("⚠️ Fill all fields")

# ---------------- SHOW SUBJECTS + DELETE ---------------- #
st.subheader("📚 Subjects (Manage)")

docs = db.collection("subjects").stream()

for doc in docs:
    d = doc.to_dict()
    doc_id = doc.id

    col1, col2, col3, col4, col5 = st.columns([2,2,1,2,1])

    col1.write(d['subject'])
    col2.write(d['faculty'])
    col3.write(f"{d['hours']} hrs")
    col4.write(f"Room {d['room']}")

    if col5.button("❌", key=doc_id):
        db.collection("subjects").document(doc_id).delete()
        st.rerun()

# ---------------- GENERATE TIMETABLE ---------------- #
st.subheader("⚙ Generate Timetable")

if st.button("Generate Timetable"):

    # ✅ FETCH SUBJECTS
    docs = db.collection("subjects").stream()
    subjects = []
    for doc in docs:
        subjects.append(doc.to_dict())

    # ✅ DEFINE DAYS & TIMES (FIXED ERROR)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    times = ["9.30:00-", "10:30", "LUNCH", "12:00", "1.00", "2:00", "BREAK", "2.30","3.30"]

    # ✅ CREATE EMPTY TIMETABLE
    timetable = {day: {time: "" for time in times} for day in days}

    # ✅ PREPARE SLOTS
    slots = []
    for sub in subjects:
        if sub["type"] == "Lab":
            for _ in range(sub["hours"] // 2):
                slots.append({"data": sub, "block": 2})
        else:
            for _ in range(sub["hours"]):
                slots.append({"data": sub, "block": 1})

    random.shuffle(slots)

    # ---------------- ALLOCATION LOGIC ---------------- #
    for day in days:
        i = 0
        while i < len(times):

            time = times[i]

            # ✅ HANDLE BREAK/LUNCH
            if time == "BREAK":
                timetable[day][time] = "☕ BREAK"
                i += 1
                continue

            if time == "LUNCH":
                timetable[day][time] = "🍴 LUNCH"
                i += 1
                continue

            if not slots:
                break

            slot = slots[0]
            sub = slot["data"]

            # ✅ LAB (2 CONTINUOUS)
            if slot["block"] == 2:
                if i + 1 < len(times):
                    next_time = times[i+1]

                    if next_time not in ["BREAK", "LUNCH"]:
                        value = f"{sub['subject']} ({sub['faculty']}, {sub['room']})"

                        timetable[day][time] = value
                        timetable[day][next_time] = value

                        slots.pop(0)
                        i += 2
                        continue

            # ✅ THEORY
            timetable[day][time] = f"{sub['subject']} ({sub['faculty']}, {sub['room']})"
            slots.pop(0)
            i += 1

    # ---------------- DISPLAY ---------------- #
    df = pd.DataFrame(timetable).T
    df.index.name = "Day"
    df.columns.name = "Time"

    st.subheader("📅 Generated Timetable")
    st.dataframe(df, use_container_width=True)

    # ---------------- 🔔 NOTIFICATION ---------------- #
    st.subheader("🔔 Smart Notifications")

    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M")
    today = now.strftime("%A")

    current_class = None
    next_class = None

    if today in df.index:
        day_schedule = df.loc[today]

        for time_slot in df.columns:
            value = day_schedule[time_slot]

            if value and value not in ["☕ BREAK", "🍴 LUNCH"]:

                if time_slot <= current_time:
                    current_class = value
                elif time_slot > current_time and next_class is None:
                    next_class = value

    if current_class:
        st.success(f"📍 Now: {current_class}")
        st.toast(f"🔔 You have class now!")

    if next_class:
        st.info(f"⏭ Next: {next_class}")