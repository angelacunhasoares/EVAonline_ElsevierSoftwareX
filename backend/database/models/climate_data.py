"""
Modelos de banco de dados para armazenamento de resultados ETo.
"""
from sqlalchemy import Column, DateTime, Float, Integer

from ..connection import Base


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
    t2m_max = Column(Float, nullable=True)  # Temperatura máxima
    t2m_min = Column(Float, nullable=True)  # Temperatura mínima
    rh2m = Column(Float, nullable=True)     # Umidade relativa
    ws2m = Column(Float, nullable=True)     # Velocidade do vento
    radiation = Column(Float, nullable=True)  # Radiação solar
    precipitation = Column(Float, nullable=True)  # Precipitação
    eto = Column(Float, nullable=False)     # Evapotranspiração de referência

    def __repr__(self):
        return f"<EToResult(id={self.id}, lat={self.lat}, lng={self.lng}, date={self.date}, eto={self.eto})>"
