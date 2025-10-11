"""Teste rápido de timing da API Open-Meteo"""
from datetime import datetime

import requests

print("🔍 Testando velocidade da API Open-Meteo...\n")

url = "https://api.open-meteo.com/v1/forecast"
params = {
    'latitude': -6.5472,
    'longitude': -47.4705,
    'hourly': 'temperature_2m,et0_fao_evapotranspiration',
    'start_date': '2025-10-09',
    'end_date': '2025-10-22',
    'timezone': 'UTC'
}

start = datetime.now()
print(f"⏱️  Início: {start.strftime('%H:%M:%S.%f')[:-3]}")

try:
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    
    end = datetime.now()
    elapsed = (end - start).total_seconds()
    
    print(f"⏱️  Fim: {end.strftime('%H:%M:%S.%f')[:-3]}")
    print(f"\n✅ Sucesso!")
    print(f"   Tempo: {elapsed:.3f} segundos")
    print(f"   Horas recebidas: {len(data['hourly']['time'])}")
    print(f"   Primeiro: {data['hourly']['time'][0]}")
    print(f"   Último: {data['hourly']['time'][-1]}")
    
    # Verificar alguns valores de ETo
    eto_values = data['hourly']['et0_fao_evapotranspiration']
    print(f"\n📊 Amostra de ETo Open-Meteo (horária):")
    print(f"   Hora 0: {eto_values[0]} mm")
    print(f"   Hora 100: {eto_values[100]} mm")
    print(f"   Hora 200: {eto_values[200]} mm")
    print(f"   Hora 300: {eto_values[300]} mm")
    
    # Verificar se há valores None/null
    none_count = sum(1 for v in eto_values if v is None)
    print(f"\n   Valores None: {none_count}/{len(eto_values)}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
