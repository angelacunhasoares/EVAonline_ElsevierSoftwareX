import os
from loguru import logger
from sqlalchemy import create_engine, text
from api.services.database import get_db_context


def save_eto_data(data: dict, db_path: str = None):
    """
    Salva dados de ETo no banco de dados PostgreSQL.
    
    Args:
        data (dict): Dicionário com dados de ETo
        db_path (str, optional): Parâmetro mantido para compatibilidade, não é utilizado
    """
    try:
        # Usa o context manager para obter uma sessão do banco
        with get_db_context() as db:
            # Prepara valores para inserção
            values = []
            for d in data:
                values.append({
                    "lat": d["lat"], 
                    "lng": d["lng"], 
                    "elevation": d["elev"], 
                    "date": d["date"], 
                    "t2m_max": d["T2M_MAX"], 
                    "t2m_min": d["T2M_MIN"], 
                    "rh2m": d["RH2M"], 
                    "ws2m": d["WS2M"], 
                    "radiation": d["ALLSKY_SFC_SW_DWN"], 
                    "precipitation": d["PRECTOTCORR"], 
                    "eto": d["ETo"]
                })
            
            # Executa inserção
            if values:
                query = text("""
                    INSERT INTO eto_results (lat, lng, elevation, date, t2m_max, t2m_min, 
                                           rh2m, ws2m, radiation, precipitation, eto)
                    VALUES (:lat, :lng, :elevation, :date, :t2m_max, :t2m_min, 
                           :rh2m, :ws2m, :radiation, :precipitation, :eto)
                """)
                
                for value in values:
                    db.execute(query, value)
                
                db.commit()
                logger.info(f"Dados salvos no PostgreSQL: {len(values)} registros")
    except Exception as e:
        logger.error(f"Erro ao salvar dados no PostgreSQL: {e}")