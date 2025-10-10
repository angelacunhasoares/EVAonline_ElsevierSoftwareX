"""
Teste do OpenMeteo Client com dados HORÁRIOS.

Este script testa:
1. Download de dados horários (24 registros/dia)
2. Agregação diária (min/max/mean/sum)
3. Conversão de W/m² → MJ/m²/dia
4. Soma de ETo horária → ETo diária
"""

import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from api.services.openmeteo_matopiba_client import OpenMeteoMatopibaClient


def test_hourly_data():
    """Testa download e agregação de dados horários."""
    
    print("="*70)
    print("TESTE: OpenMeteo Client com dados HORÁRIOS")
    print("="*70)
    
    # Inicializar cliente
    print("\n1. Inicializando cliente...")
    client = OpenMeteoMatopibaClient(forecast_days=3)
    print(f"   ✅ Cliente inicializado para {len(client.cities_df)} cidades")
    
    # Selecionar cidade de teste (Aguiarnópolis, TO - dos seus dados)
    # Latitude: -6.5472, Longitude: -47.4705
    print("\n2. Selecionando cidade de teste...")
    test_city = client.cities_df[client.cities_df['CODE_CITY'] == 1700301].iloc[0]
    print(f"   📍 Cidade: {test_city['CITY']} ({test_city['UF']})")
    print(f"   📌 Código: {test_city['CODE_CITY']}")
    print(f"   🌍 Coordenadas: ({test_city['LATITUDE']:.4f}, {test_city['LONGITUDE']:.4f})")
    
    # Buscar dados
    print("\n3. Buscando dados horários do Open-Meteo...")
    city_code = str(test_city['CODE_CITY'])
    forecast_data, warnings = client.get_forecast_single_city(city_code)
    
    if forecast_data:
        print("   ✅ Dados recebidos com sucesso!")
        
        # Mostrar estrutura
        city_info = forecast_data['city_info']
        forecast = forecast_data['forecast']
        
        print(f"\n4. Dados da cidade:")
        print(f"   • Nome: {city_info['name']}")
        print(f"   • UF: {city_info['uf']}")
        print(f"   • Elevação: {city_info['elevation']:.2f} m")
        
        print(f"\n5. Dados de previsão (agregados diariamente):")
        print(f"   Total de dias: {len(forecast)}")
        
        for date_str, values in sorted(forecast.items()):
            print(f"\n   📅 {date_str}")
            print(f"      T2M: {values['T2M_MIN']:.1f}°C (min) | "
                  f"{values['T2M_MAX']:.1f}°C (max) | "
                  f"{values['T2M']:.1f}°C (mean)")
            print(f"      RH2M: {values['RH2M']:.1f}%")
            print(f"      WS2M: {values['WS2M']:.1f} m/s")
            print(f"      Radiação: {values['ALLSKY_SFC_SW_DWN']:.2f} MJ/m²/dia")
            print(f"      Precipitação: {values['PRECTOTCORR']:.1f} mm")
            print(f"      ⭐ ETo Open-Meteo (soma diária): {values['ETo_OpenMeteo']:.2f} mm/dia")
    else:
        print("   ❌ Falha ao buscar dados!")
    
    if warnings:
        print(f"\n⚠️  Avisos ({len(warnings)}):")
        for w in warnings:
            print(f"   - {w}")
    
    print("\n" + "="*70)
    print("TESTE CONCLUÍDO!")
    print("="*70)
    
    # Comparar com seus dados manuais
    print("\n📊 COMPARAÇÃO COM SEUS DADOS MANUAIS:")
    print("   Você testou no site Open-Meteo:")
    print("   📍 Lat: -6.5, Lon: -47.5 (próximo de Aguiarnópolis)")
    print("   📅 2025-10-09: ETo horária somada = ~5.26 mm/dia")
    print(f"\n   Nossa API retornou para 2025-10-09:")
    if forecast_data and '2025-10-09' in forecast_data['forecast']:
        eto_api = forecast_data['forecast']['2025-10-09']['ETo_OpenMeteo']
        print(f"   ETo: {eto_api:.2f} mm/dia")
        print(f"\n   💡 Valores devem estar próximos (~5-6 mm/dia)!")
    
    return forecast_data, warnings


if __name__ == "__main__":
    test_hourly_data()
