# 🕵️ Lost & Found System

A **Flask-based web application** that helps users report **lost items**, list **found items**, and track their status.  
It includes **user authentication**, **item management**, and a simple dashboard for reporting and searching.

---

## ✨ Features
- 🔐 User Registration & Login (with password hashing)
- 📝 Report Lost or Found items
- 📷 Upload item images
- 📊 Dashboard with quick stats (total, lost, found, resolved)
- ✅ Mark items as resolved/unresolved
- 🔄 Forgot/Reset Password functionality
- 🗑 Delete items (only by the owner)

---

## 🛠️ Tech Stack
- **Backend:** Flask, Flask-Login, SQLAlchemy
- **Database:** SQLite (default)
- **Frontend:** HTML, CSS, Bootstrap (via templates)
- **Other:** Werkzeug Security, ItsDangerous (for password reset tokens)

---

## ⚡ Installation

1. Clone the repo:
   git clone https://github.com/vaishnavi-daggula04/lost-found-system.git
   cd lost-found-system
Create a virtual environment:
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
Install dependencies:
pip install -r requirements.txt
Run the app:
python app.py

Visit:
👉 http://127.0.0.1:5000

🚀 Deployment
You can deploy this app on:

Streamlit Cloud (for quick demos)

Render / Railway (Flask hosting)

Heroku (classic option)

👩‍💻 Author
Vaishnavi Daggula
📌 GitHub: vaishnavi-daggula04
