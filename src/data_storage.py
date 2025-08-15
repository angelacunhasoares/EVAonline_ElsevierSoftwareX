import sqlite3
from loguru import logger


def save_eto_data(data: dict, db_path: str = "data/eto_database.db"):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eto_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lat REAL, lng REAL, elevation REAL,
                date TEXT, t2m_max REAL, t2m_min REAL,
                rh2m REAL, ws2m REAL, radiation REAL,
                precipitation REAL, eto REAL
            )
        """)
        cursor.executemany("""
            INSERT INTO eto_results (lat, lng, elevation, date, t2m_max, t2m_min, rh2m, ws2m, radiation, precipitation, eto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(d["lat"], d["lng"], d["elev"], d["date"], d["T2M_MAX"], d["T2M_MIN"], d["RH2M"], d["WS2M"], d["ALLSKY_SFC_SW_DWN"], d["PRECTOTCORR"], d["ETo"]) for d in data])
        conn.commit()
        logger.info("Dados salvos no SQLite")
    except Exception as e:
        logger.error(f"Erro ao salvar dados no SQLite: {e}")
    finally:
        if conn is not None:
            conn.close()