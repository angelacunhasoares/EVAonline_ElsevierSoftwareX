"""
Modelos de banco de dados para armazenamento de resultados ETo.
"""
from sqlalchemy import Column, Integer, Float, DateTime
from database.connection import Base
# integrar com a ferramenta Alembic para gerenciar migrações de 
# forma automatizada - REFAZER ESSE SCRIPT

class EToResults(Base):
    """
    Modelo para armazenamento de resultados de cálculo de ETo.
    """
    __tablename__ = "eto_results"

    id = Column(Integer, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    elevation = Column(Float, nullable=True)
    date = Column(DateTime, nullable=False)
    t2m_max = Column(Float, nullable=True)
    t2m_min = Column(Float, nullable=True)
    rh2m = Column(Float, nullable=True)
    ws2m = Column(Float, nullable=True)
    radiation = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    eto = Column(Float, nullable=False)

    def __repr__(self):
        return f"<EToResult(id={self.id}, date={self.date}, eto={self.eto})>"
