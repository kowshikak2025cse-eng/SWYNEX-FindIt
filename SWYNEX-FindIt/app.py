import os
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-before-deployment")
db_url = os.getenv("DATABASE_URL", "sqlite:///findit.db")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    report_type = db.Column(db.String(10), nullable=False)  # LOST / FOUND
    title = db.Column(db.String(140), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(180), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="OPEN")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner = db.relationship("User", backref="items")

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    private_proof = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    item = db.relationship("Item", backref="claims")
    claimant = db.relationship("User", backref="claims")

class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="OPEN")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    item = db.relationship("Item")
    reporter = db.relationship("User")

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_user():
    return {"current_user": User.query.get(session.get("user_id")) if session.get("user_id") else None}

@app.route("/")
def home():
    latest = Item.query.filter_by(status="OPEN").order_by(Item.created_at.desc()).limit(6).all()
    lost_count = Item.query.filter_by(report_type="LOST", status="OPEN").count()
    found_count = Item.query.filter_by(report_type="FOUND", status="OPEN").count()
    return render_template("index.html", latest=latest, lost_count=lost_count, found_count=found_count)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email and a password of at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user); db.session.commit()
            session.update(user_id=user.id, name=user.name, role=user.role)
            flash("Welcome to FindIt! Your account is ready.", "success")
            return redirect(url_for("home"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.update(user_id=user.id, name=user.name, role=user.role)
            flash("You are signed in.", "success")
            return redirect(request.args.get("next") or url_for("home"))
        flash("Email or password is incorrect.", "error")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("home"))

@app.route("/items")
def items():
    query = Item.query.filter_by(status="OPEN")
    q = request.args.get("q", "").strip()
    kind = request.args.get("type", "").upper()
    category = request.args.get("category", "")
    location = request.args.get("location", "").strip()
    if q:
        query = query.filter(db.or_(Item.title.ilike(f"%{q}%"), Item.description.ilike(f"%{q}%")))
    if kind in ("LOST", "FOUND"):
        query = query.filter_by(report_type=kind)
    if category:
        query = query.filter_by(category=category)
    if location:
        query = query.filter(Item.location.ilike(f"%{location}%"))
    results = query.order_by(Item.created_at.desc()).all()
    return render_template("items.html", items=results, q=q, kind=kind, category=category, location=location)

@app.route("/items/<int:item_id>")
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    if item.status == "HIDDEN" and session.get("role") != "admin":
        abort(404)
    return render_template("item_detail.html", item=item)

@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        location = request.form.get("location", "").strip()
        kind = request.form.get("report_type", "").upper()
        try:
            event_date = date.fromisoformat(request.form.get("event_date", ""))
        except ValueError:
            event_date = None
        if not all([title, description, category, location, event_date]) or kind not in ("LOST", "FOUND"):
            flash("Please complete all required fields.", "error")
            return render_template("report.html")
        image_name = None
        upload = request.files.get("image")
        if upload and upload.filename:
            if not allowed_file(upload.filename):
                flash("Please upload a PNG, JPG or WEBP image.", "error")
                return render_template("report.html")
            safe = secure_filename(upload.filename)
            image_name = f"{session['user_id']}_{int(datetime.utcnow().timestamp())}_{safe}"
            upload.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))
        item = Item(user_id=session["user_id"], report_type=kind, title=title,
                    description=description, category=category, location=location,
                    event_date=event_date, image=image_name)
        db.session.add(item); db.session.commit()
        flash("Your report is now live.", "success")
        return redirect(url_for("item_detail", item_id=item.id))
    return render_template("report.html")

@app.route("/items/<int:item_id>/claim", methods=["POST"])
@login_required
def submit_claim(item_id):
    item = Item.query.get_or_404(item_id)
    if item.report_type != "FOUND" or item.user_id == session["user_id"]:
        flash("A claim can only be submitted on another user's found-item report.", "error")
        return redirect(url_for("item_detail", item_id=item.id))
    message = request.form.get("message", "").strip()
    proof = request.form.get("private_proof", "").strip()
    if not message or not proof:
        flash("Please provide both a message and private ownership details.", "error")
    elif Claim.query.filter_by(item_id=item.id, claimant_id=session["user_id"], status="PENDING").first():
        flash("You already have a pending claim for this item.", "info")
    else:
        db.session.add(Claim(item_id=item.id, claimant_id=session["user_id"], message=message, private_proof=proof))
        db.session.commit()
        flash("Your claim was sent privately to the finder.", "success")
    return redirect(url_for("item_detail", item_id=item.id))

@app.route("/dashboard")
@login_required
def dashboard():
    mine = Item.query.filter_by(user_id=session["user_id"]).order_by(Item.created_at.desc()).all()
    claims = Claim.query.filter_by(claimant_id=session["user_id"]).order_by(Claim.created_at.desc()).all()
    received = Claim.query.join(Item).filter(Item.user_id == session["user_id"]).order_by(Claim.created_at.desc()).all()
    return render_template("dashboard.html", mine=mine, claims=claims, received=received)

@app.route("/claims/<int:claim_id>/status", methods=["POST"])
@login_required
def claim_status(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    if claim.item.user_id != session["user_id"] and session.get("role") != "admin":
        abort(403)
    status = request.form.get("status")
    if status not in ("NEEDS_INFO", "ACCEPTED", "REJECTED"):
        abort(400)
    claim.status = status
    if status == "ACCEPTED":
        claim.item.status = "CLAIM_PENDING"
    db.session.commit()
    flash("Claim status updated.", "success")
    return redirect(url_for("dashboard"))

@app.route("/items/<int:item_id>/close", methods=["POST"])
@login_required
def close_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != session["user_id"] and session.get("role") != "admin":
        abort(403)
    item.status = "RETURNED"
    db.session.commit()
    flash("Report marked as returned/closed.", "success")
    return redirect(url_for("dashboard"))

@app.route("/items/<int:item_id>/flag", methods=["POST"])
@login_required
def flag_item(item_id):
    item = Item.query.get_or_404(item_id)
    reason = request.form.get("reason", "Suspicious listing")
    if not Flag.query.filter_by(item_id=item.id, reporter_id=session["user_id"], status="OPEN").first():
        db.session.add(Flag(item_id=item.id, reporter_id=session["user_id"], reason=reason))
        db.session.commit()
    flash("Thanks. The listing was sent to moderation.", "success")
    return redirect(url_for("item_detail", item_id=item.id))

@app.route("/admin")
@admin_required
def admin():
    return render_template("admin.html",
        users=User.query.order_by(User.created_at.desc()).all(),
        items=Item.query.order_by(Item.created_at.desc()).all(),
        flags=Flag.query.filter_by(status="OPEN").order_by(Flag.created_at.desc()).all(),
        claims=Claim.query.order_by(Claim.created_at.desc()).all())

@app.route("/admin/flags/<int:flag_id>", methods=["POST"])
@admin_required
def resolve_flag(flag_id):
    flag = Flag.query.get_or_404(flag_id)
    action = request.form.get("action")
    if action == "hide":
        flag.item.status = "HIDDEN"
    flag.status = "RESOLVED"
    db.session.commit()
    flash("Moderation action saved.", "success")
    return redirect(url_for("admin"))

@app.route("/api/v1/items")
def api_items():
    data = Item.query.filter_by(status="OPEN").order_by(Item.created_at.desc()).limit(100).all()
    return jsonify([{"id": x.id, "type": x.report_type, "title": x.title, "category": x.category,
                     "location": x.location, "date": x.event_date.isoformat(), "status": x.status} for x in data])

@app.errorhandler(403)
def forbidden(_): return render_template("error.html", code=403, message="You do not have permission to view this page."), 403
@app.errorhandler(404)
def not_found(_): return render_template("error.html", code=404, message="We could not find that page."), 404

with app.app_context():
    db.create_all()
    # Seed a demo admin only when the database is empty of admins.
    if not User.query.filter_by(role="admin").first():
        admin_user = User(name="FindIt Admin", email=os.getenv("ADMIN_EMAIL", "admin@findit.local"),
                          password_hash=generate_password_hash(os.getenv("ADMIN_PASSWORD", "Admin@12345")),
                          role="admin")
        db.session.add(admin_user); db.session.commit()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "true").lower() == "true")
