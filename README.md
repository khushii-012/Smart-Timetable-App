# 📅 Smart Auto Timetable Generator

![Python](https://img.shields.io/badge/Python-3-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Firebase](https://img.shields.io/badge/Firebase-Backend-orange)
![Render](https://img.shields.io/badge/Deployed-Render-green)

---

## 🚀 Project Overview

Smart Auto Timetable Generator is a web-based application that automatically generates a class timetable based on subjects, faculty, and available slots. It uses intelligent allocation logic to avoid conflicts and manage lab/theory sessions efficiently.

---

## 🚀 Features

* ➕ Add and manage subjects
* 🧠 Automatic timetable generation
* 🔄 Lab and theory slot handling
* 🏫 Room allocation system
* 🔔 Smart notifications for current & next class
* ☁️ Firebase integration for real-time data

---


## 🛠 Tech Stack

* Python
* Streamlit
* Firebase (Firestore)
* Pandas

---

## 🌐 Live Demo

👉 https://smart-timetable-app-hl0x.onrender.com
---

## ⚙️ How It Works

* User enters subject details (faculty, hours, type, room)
* Data is stored in Firebase Firestore
* Algorithm randomly assigns slots while maintaining constraints
* Labs are scheduled in continuous blocks
* Final timetable is generated dynamically and displayed

---

## ⚙️ Installation (Run Locally)

```bash
git clone https://github.com/khushii-012/Smart-Timetable-App.git
cd Smart-Timetable-App
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔐 Environment Variables

Create an environment variable:

```
FIREBASE_CRED = your_firebase_json
```

---

## 📂 Project Structure

```
Smart-Timetable-App/
│── app.py
│── requirements.txt
│── README.md
│── assets/   (for screenshots)
```

---

## 🚀 Future Improvements

* Export timetable as PDF
* User login system
* UI improvements
* Conflict detection optimization

---

## 👩‍💻 Author

**Khushi Lanjewar**

---


