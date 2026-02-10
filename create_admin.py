import os
from app.database.db import SessionLocal
from app.models import User
from app.auth import hash_password

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_EMAIL or not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_EMAIL / ADMIN_PASSWORD not set")

db = SessionLocal()

try:
    existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if existing:
        print("Admin already exists")
        exit(0)

    admin = User(
        email=ADMIN_EMAIL,
        username="admin",
        mobile_number="+91 3456767890",
        hashed_password=hash_password(ADMIN_PASSWORD),
        is_active=True,
        is_admin=True,        # 👈 IMPORTANT
        is_staff=True,
    )

    db.add(admin)
    db.commit()

    print("✅ Admin created successfully")

finally:
    db.close()
