from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime
import os
from werkzeug.utils import secure_filename   # ✅ for safe file names

# ---------------------------------
# App Setup
# ---------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lostfound.db"
app.config["UPLOAD_FOLDER"] = "static/images"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Token Serializer (for reset password)
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# ---------------------------------
# Models
# ---------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # ✅ Relationship
    items = db.relationship("Item", backref="user", lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Lost or Found
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)

    # ✅ Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# ---------------------------------
# User Loader
# ---------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------------
# Routes
# ---------------------------------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method="pbkdf2:sha256"),
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    items = Item.query.filter_by(user_id=current_user.id).order_by(Item.date_reported.desc()).all()
    all_items = Item.query.order_by(Item.date_reported.desc()).limit(12).all()  # latest 12 items

    stats = {
        "total": Item.query.count(),
        "lost": Item.query.filter_by(type="Lost").count(),
        "found": Item.query.filter_by(type="Found").count(),
        "resolved": Item.query.filter_by(is_resolved=True).count(),
        "mine": Item.query.filter_by(user_id=current_user.id).count(),
    }

    return render_template("dashboard.html", items=items, all_items=all_items, stats=stats)

# ---------------------------------
# Add Item Route
# ---------------------------------
@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        title = request.form["title"]
        type_ = request.form["type"]
        location = request.form["location"]
        description = request.form["description"]

        # ✅ Handle Image Upload
        image_file = request.files.get("image")
        image_filename = None
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)
            image_filename = filename

        new_item = Item(
            title=title,
            type=type_,
            location=location,
            description=description,
            image=image_filename,
            user_id=current_user.id
        )
        db.session.add(new_item)
        db.session.commit()
        flash("Item reported successfully ✅", "success")
        return redirect(url_for("dashboard"))

    return render_template("post_item.html")

# ---------------------------------
# Forgot Password Routes
# ---------------------------------
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.id, salt="password-reset")
            reset_url = url_for("reset_password", token=token, _external=True)
            print(f"\n🔑 Password reset link for {email}: {reset_url}\n")  # Console only
            flash("Password reset link has been generated (check server console).", "info")
        else:
            flash("Email not found!", "danger")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        user_id = serializer.loads(token, salt="password-reset", max_age=3600)  # valid 1 hr
    except (SignatureExpired, BadSignature):
        flash("Invalid or expired reset link!", "danger")
        return redirect(url_for("login"))

    user = User.query.get(user_id)
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(request.url)

        user.password = generate_password_hash(new_password, method="pbkdf2:sha256")
        db.session.commit()
        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

# ---------------------------------
# Item Detail Route
# ---------------------------------
@app.route("/item/<int:item_id>")
@login_required
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template("item_detail.html", item=item)

# ---------------------------------
# Update Status (Mark Resolved / Pending)
# ---------------------------------
@app.route("/update_status/<int:item_id>", methods=["POST"])
@login_required
def update_status(item_id):
    item = Item.query.get_or_404(item_id)

    # Only owner can update
    if item.user_id != current_user.id:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Not allowed"}), 403
        flash("You are not allowed to update this item.", "danger")
        return redirect(url_for("dashboard"))

    # Toggle status
    item.is_resolved = not item.is_resolved
    db.session.commit()

    # AJAX request → return JSON (no flash)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"is_resolved": item.is_resolved})

    # Normal request → safe redirect
    flash("Item status updated ✅", "success")
    return redirect(url_for("dashboard"))


# ---------------------------------
# Delete Item
# ---------------------------------
@app.route("/delete_item/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        flash("You are not allowed to delete this item.", "danger")
        return redirect(url_for("dashboard"))

    db.session.delete(item)
    db.session.commit()
    flash("Item deleted successfully 🗑", "success")
    return redirect(url_for("dashboard"))

# ---------------------------------
# Run
# ---------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
