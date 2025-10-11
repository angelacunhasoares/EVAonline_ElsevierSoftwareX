"""Teste de conexão Redis para frontend"""
import sys
sys.path.insert(0, 'C:\\Users\\User\\OneDrive\\Documentos\\GitHub\\EVAonline_ElsevierSoftwareX')

from backend.core.map_results.matopiba_forecasts import fetch_forecast_data_from_redis, fetch_forecast_data

print("="*60)
print("🔍 TESTE 1: fetch_forecast_data_from_redis()")
print("="*60)

data = fetch_forecast_data_from_redis()

if data:
    print(f"✅ SUCCESS - Dados retornados!")
    print(f"   Cities: {len(data.get('forecasts', {}))}")
    metadata = data.get('metadata', {})
    print(f"   Updated: {metadata.get('updated_at', 'N/A')}")
    print(f"   N_cities: {metadata.get('n_cities', 0)}")
else:
    print("❌ FAILED - Retornou None")

print("\n" + "="*60)
print("🔍 TESTE 2: fetch_forecast_data(n_intervals=1)")
print("="*60)

forecast_data, status_bar = fetch_forecast_data(n_intervals=1)

if forecast_data and not forecast_data.get('_using_mock'):
    print(f"✅ SUCCESS - Dados REAIS carregados!")
    print(f"   Cities: {len(forecast_data.get('forecasts', {}))}")
elif forecast_data and forecast_data.get('_using_mock'):
    print(f"⚠️ WARNING - Usando MOCK data")
    print(f"   Cities: {len(forecast_data.get('forecasts', {}))}")
else:
    print("❌ FAILED - Nenhum dado retornado")

print("\nStatus Bar HTML:")
print(status_bar)
