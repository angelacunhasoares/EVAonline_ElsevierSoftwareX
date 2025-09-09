#!/usr/bin/env python3
"""
Script de Integração: Captura dados do Open-Meteo e salva no PostgreSQL

Este script demonstra como capturar dados meteorológicos do Open-Meteo
e salvá-los no banco de dados PostgreSQL com cache Redis.
"""

import pickle
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "backend"))

try:
    from backend.api.services.openmeteo import OpenMeteoForecastAPI
    from backend.database.data_storage import save_eto_data
    print("✅ Módulos importados com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)


def main():
    """Função principal para capturar e salvar dados."""
    print("🌤️  CAPTURA DE DADOS: OPEN-METEO → POSTGRESQL + REDIS")
    print("=" * 60)

    # Coordenadas de exemplo (Jaú, SP)
    lat, long = -22.2964, -48.5578
    print(f"📍 Localização: Jaú, SP (lat={lat}, long={long})")

    try:
        # 1. Inicializar API do Open-Meteo
        print("\n🔗 Conectando ao Open-Meteo...")
        api = OpenMeteoForecastAPI(lat=lat, long=long, days_ahead=1)
        print("✅ API Open-Meteo conectada!")

        # 2. Obter dados meteorológicos usando requisição direta
        print("\n📊 Obtendo dados meteorológicos...")
        url = api.build_url()
        print(f"🔗 URL: {url}")

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
        print("✅ Dados meteorológicos obtidos!")

        # 3. Processar dados para formato do banco
        print("\n🔄 Processando dados para o banco...")
        processed_data = []

        if weather_data and 'hourly' in weather_data:
            hourly = weather_data['hourly']
            times = hourly.get('time', [])
            temperatures = hourly.get('temperature_2m', [])
            humidities = hourly.get('relative_humidity_2m', [])
            etos = hourly.get('et0_fao_evapotranspiration', [])
            wind_speeds = hourly.get('wind_speed_10m', [])
            radiations = hourly.get('shortwave_radiation', [])
            precipitations = hourly.get('precipitation', [])

            # Processar dados hora por hora
            for i, time_str in enumerate(times):
                try:
                    # Converter string para datetime
                    date_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))

                    # Preparar dados para o banco
                    record = {
                        "lat": lat,
                        "lng": long,
                        "elev": 0.0,  # Elevation (pode ser obtida da API)
                        "date": date_obj,
                        "T2M_MAX": temperatures[i] if i < len(temperatures) else None,
                        "T2M_MIN": temperatures[i] if i < len(temperatures) else None,
                        "RH2M": humidities[i] if i < len(humidities) else None,
                        "WS2M": wind_speeds[i] if i < len(wind_speeds) else None,
                        "ALLSKY_SFC_SW_DWN": radiations[i] if i < len(radiations) else None,
                        "PRECTOTCORR": precipitations[i] if i < len(precipitations) else None,
                        "ETo": etos[i] if i < len(etos) else None
                    }

                    processed_data.append(record)

                except Exception as e:
                    print(f"⚠️  Erro ao processar registro {i}: {e}")
                    continue

            print(f"✅ {len(processed_data)} registros processados!")

            # 4. Salvar no banco de dados
            print("\n💾 Salvando dados no PostgreSQL...")
            if processed_data:
                # save_eto_data espera uma lista de registros diretamente
                save_eto_data(processed_data)
                print("✅ Dados salvos com sucesso no PostgreSQL!")

                # 5. Verificar cache Redis
                print("\n🔍 Verificando cache Redis...")
                if api.redis_client:
                    today_str = datetime.now().strftime("%Y%m%d")
                    cache_key = f"forecast:{today_str}:{lat}:{long}:{api.timezone}"
                    # Tentar salvar no cache também
                    try:
                        import pickle
                        api.redis_client.setex(cache_key, 3600, pickle.dumps(weather_data))
                        print("✅ Dados também armazenados no cache Redis!")
                    except Exception as e:
                        print(f"⚠️  Erro ao salvar no cache: {e}")
                else:
                    print("⚠️  Cliente Redis não disponível")

            else:
                print("❌ Nenhum dado para salvar!")

        else:
            print("❌ Dados meteorológicos não encontrados na resposta")
            if weather_data:
                print("Chaves disponíveis:", list(weather_data.keys()))

    except Exception as e:
        print(f"❌ Erro durante a execução: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("🎉 PROCESSO CONCLUÍDO!")


if __name__ == "__main__":
    main()
