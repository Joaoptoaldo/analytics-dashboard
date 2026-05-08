from sqlalchemy import Boolean, Column, Date, Float, Index, Integer, String, UniqueConstraint

from backend.db import Base


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
    is_synthetic = Column(Boolean, default=False, comment="True if record is from seed data (test), False if from external sync (real)")
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_external_id"),
        Index("ix_products_date_category_status", "date", "category", "status"),
    )

    def to_dict(self):
        """_summary_: Converte o modelo Product para dicionario serializavel.

        Returns:
            _type_: _description_: Dicionario com `id`, `client`, `category`, `revenue`, `status` e `date` (`YYYY-MM-DD` ou `None`).
        """
        # defensive conversions: external_id may be malformed (string 'NaN')
        try:
            ext_id = int(self.external_id) if self.external_id is not None else None
        except Exception:
            ext_id = None

        # revenue may contain NaN/inf coming from external data; normalize to 0.0
        try:
            rev = float(self.revenue) if self.revenue is not None else 0.0
            from math import isfinite
            if not isfinite(rev):
                rev = 0.0
        except Exception:
            rev = 0.0

        return {
            "id": ext_id if ext_id is not None else (int(self.id) if self.id is not None else None),
            "client": self.client,
            "category": self.category,
            "revenue": rev,
            "status": self.status,
            "date": self.date.strftime("%Y-%m-%d") if self.date else None,
        }
