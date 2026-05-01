from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint
from backend.db import Base
import datetime


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, index=True)
    client = Column(String(255))
    category = Column(String(100))
    revenue = Column(Float)
    status = Column(String(50))
    region = Column(String(50), nullable=True, comment="deprecated: kept temporarily for backward compatibility")
    date = Column(Date)
    __table_args__ = (UniqueConstraint("external_id", name="uq_external_id"),)

    def to_dict(self):
        return {
            "id": self.external_id or self.id,
            "client": self.client,
            "category": self.category,
            "revenue": float(self.revenue) if self.revenue is not None else 0.0,
            "status": self.status,
            "date": self.date.strftime("%Y-%m-%d") if self.date else None,
        }
