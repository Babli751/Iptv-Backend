from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# SQLAlchemy veritabanı bağlantısını oluştur
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True  # Bağlantı sorunlarını otomatik çözmek için
)

# SessionLocal fabrikasını oluştur
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency (Bağımlılık) fonksiyonu
def get_db():
    """
    Her request için yeni bir DB sessionı oluşturur
    ve işlem bitince otomatik kapatır
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()