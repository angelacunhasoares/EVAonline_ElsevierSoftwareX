"""
Teste do OpenMeteo Client MATOPIBA - Download de dados para CSV.

Testa busca de previsões para algumas cidades e salva resultados em CSV.
"""
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Adicionar projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.api.services.openmeteo_matopiba_client import \
    OpenMeteoMatopibaClient

print("\n" + "="*70)
print("TESTE: OpenMeteo Client MATOPIBA - Download para CSV")
print("="*70 + "\n")

# Inicializar cliente
print("1. Inicializando cliente Open-Meteo...")
client = OpenMeteoMatopibaClient(forecast_days=2)
print(f"✅ Cliente inicializado para {len(client.cities_df)} cidades\n")

# Selecionar 5 cidades para teste (diferentes estados)
print("2. Selecionando 5 cidades para teste...")
test_cities = client.cities_df.head(5)
print("\nCidades selecionadas:")
for idx, city in test_cities.iterrows():
    print(f"  - {city['CITY']} ({city['UF']}) - Código: {city['CODE_CITY']}")

print(f"\n3. Buscando previsões Open-Meteo (2 dias)...")
print("   Aguarde...")

# Buscar previsões para as 5 cidades
cities_data = {}
for idx, city in test_cities.iterrows():
    city_code = str(city['CODE_CITY'])
    print(f"\n   Buscando: {city['CITY']} ({city['UF']})...", end=" ")
    
    try:
        forecast_data, warnings = client.get_forecast_single_city(city_code)
        if forecast_data:
            cities_data[city_code] = forecast_data
            print("✅")
        else:
            print("❌ Sem dados")
    except Exception as e:
        print(f"❌ Erro: {e}")

print(f"\n✅ Total de cidades com dados: {len(cities_data)}\n")

# Converter dados para DataFrame e salvar em CSV
print("4. Convertendo para CSV...")

all_rows = []

for city_code, city_data in cities_data.items():
    city_info = city_data['city_info']
    city_name = city_info['name']
    state = city_info['uf']
    lat = city_info['latitude']
    lon = city_info['longitude']
    
    forecast = city_data['forecast']
    
    for date_str, values in forecast.items():
        row = {
            'city_code': city_code,
            'city_name': city_name,
            'state': state,
            'latitude': lat,
            'longitude': lon,
            'date': date_str,
        }
        
        # Adicionar todas as variáveis
        for var_name, var_value in values.items():
            row[var_name] = var_value
        
        all_rows.append(row)

# Criar DataFrame
df = pd.DataFrame(all_rows)

# Reordenar colunas
column_order = [
    'city_code', 'city_name', 'state', 'latitude', 'longitude', 'date',
    'T2M_MAX', 'T2M_MIN', 'RH2M', 'WS2M', 
    'ALLSKY_SFC_SW_DWN', 'PRECTOTCORR', 'ETo_OpenMeteo'
]

# Manter apenas colunas que existem
column_order = [col for col in column_order if col in df.columns]
df = df[column_order]

# Salvar CSV
output_file = "temp/openmeteo_test_5cities.csv"
Path("temp").mkdir(exist_ok=True)
df.to_csv(output_file, index=False, float_format='%.4f')

print(f"✅ CSV salvo em: {output_file}")
print(f"   Total de registros: {len(df)}")
print(f"   Cidades: {df['city_name'].nunique()}")
print(f"   Datas: {df['date'].nunique()}")

# Mostrar resumo estatístico
print("\n5. RESUMO ESTATÍSTICO DOS DADOS")
print("="*70)

print("\n📊 Variáveis Meteorológicas:")
for col in ['T2M_MAX', 'T2M_MIN', 'RH2M', 'WS2M', 
            'ALLSKY_SFC_SW_DWN', 'PRECTOTCORR', 'ETo_OpenMeteo']:
    if col in df.columns:
        values = df[col].dropna()
        print(f"\n{col}:")
        print(f"  Mín:    {values.min():.2f}")
        print(f"  Máx:    {values.max():.2f}")
        print(f"  Média:  {values.mean():.2f}")
        print(f"  Mediana: {values.median():.2f}")
        print(f"  NaN:    {df[col].isna().sum()} de {len(df)}")

# Mostrar primeiros registros
print("\n6. PRIMEIROS 5 REGISTROS")
print("="*70)
print(df.head().to_string())

print("\n" + "="*70)
print("✅ TESTE CONCLUÍDO!")
print(f"📁 Verifique o arquivo: {output_file}")
print("="*70 + "\n")

# Verificar se há dados suspeitos
print("7. VERIFICAÇÃO DE QUALIDADE DOS DADOS")
print("="*70)

warnings = []

# Verificar ETo
if 'ETo_OpenMeteo' in df.columns:
    eto_values = df['ETo_OpenMeteo'].dropna()
    if len(eto_values) > 0:
        if eto_values.min() < 0:
            warnings.append(f"⚠️ ETo negativa encontrada: {eto_values.min():.2f}")
        if eto_values.max() > 15:
            warnings.append(f"⚠️ ETo muito alta: {eto_values.max():.2f}")
        if eto_values.mean() < 1 or eto_values.mean() > 10:
            warnings.append(f"⚠️ ETo média suspeita: {eto_values.mean():.2f}")

# Verificar temperatura
if 'T2M_MAX' in df.columns and 'T2M_MIN' in df.columns:
    tmax = df['T2M_MAX'].dropna()
    tmin = df['T2M_MIN'].dropna()
    if len(tmax) > 0 and len(tmin) > 0:
        if tmax.min() < tmin.max():
            # Verificar se há casos onde Tmin > Tmax
            invalid = df[df['T2M_MIN'] > df['T2M_MAX']]
            if len(invalid) > 0:
                warnings.append(f"⚠️ {len(invalid)} registros com Tmin > Tmax")

# Verificar radiação
if 'ALLSKY_SFC_SW_DWN' in df.columns:
    rad = df['ALLSKY_SFC_SW_DWN'].dropna()
    if len(rad) > 0:
        if rad.min() < 0:
            warnings.append(f"⚠️ Radiação negativa: {rad.min():.2f}")

if warnings:
    print("\n⚠️ AVISOS ENCONTRADOS:")
    for warning in warnings:
        print(f"  {warning}")
else:
    print("\n✅ Dados parecem OK! Sem avisos de qualidade.")

print("\n" + "="*70)
