
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    user = User.query.filter_by(
        email="admin@findit.local"
    ).first()

    if user:
        user.password_hash = generate_password_hash("FindIt@12345")
        db.session.commit()
        print("Admin password reset successfully!")
    else:
        print("Admin account not found!")
