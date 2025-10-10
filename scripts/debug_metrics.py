"""
Debug: Investigar métricas ruins (R² = -10.1)
Analisa dados do cache Redis para identificar problema.
"""

import json
import os
import pickle
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from redis import Redis


def main():
    print("="*70)
    print("DEBUG: Métricas Ruins (R² = -10.1)")
    print("="*70)
    
    # Conectar Redis
    redis_password = os.getenv("REDIS_PASSWORD", "evaonline")
    redis_url = f"redis://default:{redis_password}@localhost:6379/0"
    redis_client = Redis.from_url(redis_url, decode_responses=False)
    
    # Buscar forecasts
    print("\n1️⃣ Carregando cache...")
    forecast_key = "matopiba:forecasts:today_tomorrow"
    data_bytes = redis_client.get(forecast_key)
    
    if not data_bytes:
        print("❌ Cache não encontrado")
        return
    
    cache_data = pickle.loads(data_bytes)
    forecasts = cache_data.get('forecasts', {})
    validation = cache_data.get('validation', {})
    
    print(f"✅ Cache carregado: {len(forecasts)} cidades")
    
    # Metadata
    print("\n2️⃣ Validation Metrics:")
    print(f"   R²: {validation.get('r2', 'N/A')}")
    print(f"   RMSE: {validation.get('rmse', 'N/A')}")
    print(f"   Bias: {validation.get('bias', 'N/A')}")
    print(f"   MAE: {validation.get('mae', 'N/A')}")
    print(f"   Amostras: {validation.get('n_samples', 'N/A')}")
    print(f"   Status: {validation.get('status', 'N/A')}")
    
    # Analisar primeiras cidades
    print("\n3️⃣ Primeiras 10 cidades:")
    print("-"*70)
    print(f"{'Cidade':<25} {'Data':<12} {'ETo_EVA':>8} {'ETo_OM':>8} {'Diff':>8}")
    print("-"*70)
    
    count = 0
    for city_code, city_data in forecasts.items():
        if count >= 10:
            break
        
        city_name = city_data.get('city_name', 'N/A')
        forecast_dict = city_data.get('forecast', {})
        
        if forecast_dict:
            # Pegar primeiro dia
            first_date = list(forecast_dict.keys())[0]
            first_day = forecast_dict[first_date]
            
            eto_eva = first_day.get('ETo_EVAonline', 0)
            eto_om = first_day.get('ETo_OpenMeteo', 0)
            diff = eto_eva - eto_om
            
            print(f"{city_name:<25} {first_date:<12} {eto_eva:>8.2f} "
                  f"{eto_om:>8.2f} {diff:>8.2f}")
        
        count += 1
    
    # Estatísticas gerais
    print("\n4️⃣ Estatísticas gerais:")
    all_eto_eva = []
    all_eto_om = []
    
    for city_code, city_data in forecasts.items():
        forecast_dict = city_data.get('forecast', {})
        for date_str, day_data in forecast_dict.items():
            eto_eva = day_data.get('ETo_EVAonline', 0)
            eto_om = day_data.get('ETo_OpenMeteo', 0)
            all_eto_eva.append(eto_eva)
            all_eto_om.append(eto_om)
    
    print(f"   Total de valores: {len(all_eto_eva)}")
    print(f"\n   ETo_EVAonline:")
    print(f"      Mín: {min(all_eto_eva):.2f} mm/dia")
    print(f"      Máx: {max(all_eto_eva):.2f} mm/dia")
    print(f"      Média: {sum(all_eto_eva)/len(all_eto_eva):.2f} mm/dia")
    print(f"\n   ETo_OpenMeteo:")
    print(f"      Mín: {min(all_eto_om):.2f} mm/dia")
    print(f"      Máx: {max(all_eto_om):.2f} mm/dia")
    print(f"      Média: {sum(all_eto_om)/len(all_eto_om):.2f} mm/dia")
    
    # Identificar anomalias
    print("\n5️⃣ Anomalias (|diff| > 5 mm/dia):")
    anomalies = 0
    for city_code, city_data in forecasts.items():
        city_name = city_data.get('city_name', 'N/A')
        forecast_dict = city_data.get('forecast', {})
        
        for date_str, day_data in forecast_dict.items():
            eto_eva = day_data.get('ETo_EVAonline', 0)
            eto_om = day_data.get('ETo_OpenMeteo', 0)
            diff = abs(eto_eva - eto_om)
            
            if diff > 5:
                if anomalies < 10:  # Mostrar apenas 10
                    print(f"   {city_name}: {date_str} - "
                          f"EVA={eto_eva:.2f}, OM={eto_om:.2f}, "
                          f"diff={eto_eva-eto_om:+.2f}")
                anomalies += 1
    
    if len(all_eto_eva) > 0:
        anomaly_pct = anomalies/len(all_eto_eva)*100
        print(f"\n   Total anomalias: {anomalies}/{len(all_eto_eva)} "
              f"({anomaly_pct:.1f}%)")
    else:
        print("\n   Nenhum dado para análise")
    
    # Diagnóstico
    print("\n6️⃣ DIAGNÓSTICO:")
    avg_eva = sum(all_eto_eva)/len(all_eto_eva)
    avg_om = sum(all_eto_om)/len(all_eto_om)
    avg_diff = avg_eva - avg_om
    
    print(f"   Diferença média: {avg_diff:+.2f} mm/dia")
    
    if avg_diff > 10:
        print("   ⚠️  ETo_EVAonline MUITO MAIOR que Open-Meteo")
        print("   Possível causa:")
        print("      - Erro no cálculo ETo (unidades?)")
        print("      - Conversão de dados incorreta")
        print("      - Cn/Cd com valores errados")
    elif avg_diff < -10:
        print("   ⚠️  ETo_EVAonline MUITO MENOR que Open-Meteo")
        print("   Possível causa:")
        print("      - Divisão por fator errado")
        print("      - Unidades de tempo incorretas (hora vs dia)")
    else:
        print("   ⚠️  Valores próximos mas R² negativo")
        print("   Possível causa:")
        print("      - Ordem dos dados invertida na comparação")
        print("      - Cálculo de R² usando arrays errados")
        print("      - Variância zero em algum array")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
