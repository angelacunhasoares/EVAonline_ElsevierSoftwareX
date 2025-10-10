"""
Análise dos resultados MATOPIBA salvos no Redis.
"""
import json
import pickle

import pandas as pd
import redis

# Conectar Redis
redis_client = redis.from_url("redis://default:evaonline@localhost:6379/0")

print("\n" + "="*70)
print("ANÁLISE DOS DADOS MATOPIBA NO REDIS")
print("="*70 + "\n")

# 1. Metadata
print("1. METADATA")
print("-"*70)
metadata_raw = redis_client.get("matopiba:metadata")
if metadata_raw:
    metadata = json.loads(metadata_raw)
    print(f"✅ Metadata encontrada:")
    print(json.dumps(metadata, indent=2, default=str))
else:
    print("❌ Metadata não encontrada")

# 2. Forecasts
print("\n2. FORECASTS (primeiras 3 cidades)")
print("-"*70)
forecasts_raw = redis_client.get("matopiba:forecasts:today_tomorrow")
if forecasts_raw:
    forecasts = pickle.loads(forecasts_raw)
    
    # Verificar tipo
    print(f"Tipo: {type(forecasts)}")
    
    if isinstance(forecasts, dict):
        print(f"✅ Estrutura: dicionário")
        print(f"Chaves: {list(forecasts.keys())}")
        
        # Se for dicionário com 'forecasts' e 'validation'
        if 'forecasts' in forecasts:
            cities = forecasts['forecasts']
            print(f"\n✅ {len(cities)} cidades")
            print(f"Tipo cities: {type(cities)}\n")
            
            # Se cities é dicionário, converter para lista
            if isinstance(cities, dict):
                cities_list = list(cities.values())
            else:
                cities_list = cities
            
            for i, city in enumerate(cities_list[:3]):
                print(f"Cidade {i+1}:")
                print(f"   Tipo: {type(city)}")
                if isinstance(city, dict):
                    print(f"   Chaves: {list(city.keys())}")
                else:
                    print(f"   Valor: {city[:100] if len(str(city)) > 100 else city}")
                print()
                
        else:
            print("Estrutura inesperada")
            print(json.dumps(str(forecasts)[:500], indent=2))
    else:
        print(f"Tipo inesperado: {type(forecasts)}")
        
else:
    print("❌ Forecasts não encontrados")

# 3. Análise detalhada da validação
print("\n3. ANÁLISE DE VALIDAÇÃO (todas as 337 cidades)")
print("-"*70)
if forecasts_raw:
    # Coletar todos os valores
    all_eto_eva = []
    all_eto_om = []
    
    for city in forecasts:
        df = pd.DataFrame(city['data'])
        if 'ETo_EVAonline' in df.columns and 'ETo_OpenMeteo' in df.columns:
            all_eto_eva.extend(df['ETo_EVAonline'].values)
            all_eto_om.extend(df['ETo_OpenMeteo'].values)
    
    all_eto_eva = pd.Series(all_eto_eva)
    all_eto_om = pd.Series(all_eto_om)
    
    print(f"Total de amostras: {len(all_eto_eva)}")
    print(f"\nETo EVAonline:")
    print(f"   Min: {all_eto_eva.min():.3f} mm/dia")
    print(f"   Max: {all_eto_eva.max():.3f} mm/dia")
    print(f"   Média: {all_eto_eva.mean():.3f} mm/dia")
    print(f"   Mediana: {all_eto_eva.median():.3f} mm/dia")
    
    print(f"\nETo OpenMeteo:")
    print(f"   Min: {all_eto_om.min():.3f} mm/dia")
    print(f"   Max: {all_eto_om.max():.3f} mm/dia")
    print(f"   Média: {all_eto_om.mean():.3f} mm/dia")
    print(f"   Mediana: {all_eto_om.median():.3f} mm/dia")
    
    print(f"\nDiferença (EVAonline - OpenMeteo):")
    diff = all_eto_eva - all_eto_om
    print(f"   Min: {diff.min():.3f} mm/dia")
    print(f"   Max: {diff.max():.3f} mm/dia")
    print(f"   Média: {diff.mean():.3f} mm/dia")
    print(f"   Mediana: {diff.median():.3f} mm/dia")
    
    # Recalcular métricas manualmente
    import numpy as np
    from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                                 r2_score)
    
    print(f"\nMétricas recalculadas:")
    r2_manual = r2_score(all_eto_om, all_eto_eva)
    rmse_manual = np.sqrt(mean_squared_error(all_eto_om, all_eto_eva))
    bias_manual = (all_eto_eva - all_eto_om).mean()
    mae_manual = mean_absolute_error(all_eto_om, all_eto_eva)
    
    print(f"   R² = {r2_manual:.3f}")
    print(f"   RMSE = {rmse_manual:.3f} mm/dia")
    print(f"   Bias = {bias_manual:.3f} mm/dia")
    print(f"   MAE = {mae_manual:.3f} mm/dia")

print("\n" + "="*70)
