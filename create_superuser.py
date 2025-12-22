from app.database import SessionLocal
from app.models import User
from app.auth import hash_password

db = SessionLocal()

superuser = User(
    email="admin@gmail.com",
    username="admin",
    mobile_number="9999999999",
    hashed_password=hash_password("StrongPassword123"),
    is_active=True,
    is_email_verified=True,
    is_superuser=True,
)

db.add(superuser)
db.commit()

print("✅ Superuser created")