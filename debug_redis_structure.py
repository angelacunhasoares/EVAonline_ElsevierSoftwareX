#!/usr/bin/env python
"""Debug: Verificar estrutura dos dados no Redis"""
import json
from datetime import datetime

import redis

# Conectar ao Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Buscar dados
cached = r.get('matopiba:forecasts:latest')
if not cached:
    print("❌ Nenhum dado no Redis!")
    exit(1)

data = json.loads(cached)
print("✅ Dados carregados do Redis")
print(f"Keys na raiz: {list(data.keys())}")

# Pegar primeira cidade
forecasts = data.get('forecasts', {})
if not forecasts:
    print("❌ Nenhuma previsão!")
    exit(1)

sample_code = list(forecasts.keys())[0]
city_data = forecasts[sample_code]

print(f"\n📍 Cidade exemplo: {sample_code}")
print(f"Keys na cidade: {list(city_data.keys())[:15]}")

# Verificar se tem datas
dates = [k for k in city_data.keys() if '-' in k]
if dates:
    print(f"\n📅 Datas disponíveis: {dates[:5]}")
    first_date = dates[0]
    print(f"\n📊 Dados para {first_date}:")
    print(f"Keys: {list(city_data[first_date].keys())[:10]}")
    print(f"ETo: {city_data[first_date].get('eto')}")
    print(f"Precip: {city_data[first_date].get('precipitation')}")
else:
    print("❌ Nenhuma data encontrada nas keys diretas!")
    # Verificar se tem 'forecast' key
    if 'forecast' in city_data:
        print("\n✅ Encontrado 'forecast' key!")
        forecast_data = city_data['forecast']
        print(f"Type de forecast: {type(forecast_data)}")
        if isinstance(forecast_data, dict):
            print(f"Keys em forecast: {list(forecast_data.keys())[:10]}")
            # Verificar datas dentro de forecast
            forecast_dates = [k for k in forecast_data.keys() if '-' in str(k)]
            if forecast_dates:
                print(f"\n📅 Datas em forecast: {forecast_dates[:5]}")
                first_date = forecast_dates[0]
                print(f"\n📊 Dados para {first_date}:")
                print(f"Keys: {list(forecast_data[first_date].keys())[:10]}")
                print(f"ETo: {forecast_data[first_date].get('eto')}")
                print(f"Precip: {forecast_data[first_date].get('precipitation')}")

# Verificar metadata
if 'metadata' in city_data:
    print(f"\n📋 Metadata:")
    print(f"  City name: {city_data['metadata'].get('city_name')}")
    print(f"  State: {city_data['metadata'].get('state')}")
    print(f"  Lat/Lon: {city_data['metadata'].get('latitude')}, {city_data['metadata'].get('longitude')}")

# Verificar data de hoje
today = datetime.now().strftime("%Y-%m-%d")
print(f"\n🕒 Data de hoje: {today}")
print(f"Existe chave '{today}' nos dados? {today in city_data}")
