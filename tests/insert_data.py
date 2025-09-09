#!/usr/bin/env python3
"""
Script para inserir todos os dados do CSV na tabela eto_results
"""

import csv
from datetime import datetime

# Dados para inserir (baseado no CSV)
dados = [
    (1, -22.2964, -48.5578, 0, '2025-09-08 00:00:00', 19.9, 19.9, 73, 13, 0, 0, 0.04),
    (2, -22.2964, -48.5578, 0, '2025-09-08 01:00:00', 19.5, 19.5, 75, 12.2, 0, 0, 0.03),
    (3, -22.2964, -48.5578, 0, '2025-09-08 02:00:00', 19.2, 19.2, 76, 12, 0, 0, 0.03),
    (4, -22.2964, -48.5578, 0, '2025-09-08 03:00:00', 18.6, 18.6, 80, 11.2, 0, 0, 0.02),
    (5, -22.2964, -48.5578, 0, '2025-09-08 04:00:00', 18.3, 18.3, 81, 10.9, 0, 0, 0.01),
    (6, -22.2964, -48.5578, 0, '2025-09-08 05:00:00', 18.3, 18.3, 81, 11, 0, 0, 0.01),
    (7, -22.2964, -48.5578, 0, '2025-09-08 06:00:00', 18.4, 18.4, 80, 10.3, 0, 0, 0.01),
    (8, -22.2964, -48.5578, 0, '2025-09-08 07:00:00', 18.8, 18.8, 78, 9.2, 19, 0, 0.04),
    (9, -22.2964, -48.5578, 0, '2025-09-08 08:00:00', 20.8, 20.8, 69, 11, 156, 0, 0.12),
    (10, -22.2964, -48.5578, 0, '2025-09-08 09:00:00', 23.7, 23.7, 58, 12.6, 378, 0, 0.25)
]

# Gerar INSERT statements
insert_statements = []
for dado in dados:
    values = ", ".join([str(x) if isinstance(x, (int, float)) else f"'{x}'" for x in dado])
    insert_statements.append(f"({values})")

sql = f"""
INSERT INTO eto_results (id, lat, lng, elevation, date, t2m_max, t2m_min, rh2m, ws2m, radiation, precipitation, eto)
VALUES {", ".join(insert_statements[:10])};
"""

print("SQL gerado:")
print(sql)
