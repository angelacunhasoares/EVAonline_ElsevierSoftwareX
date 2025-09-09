#!/usr/bin/env python3
"""
Script para obter dados horários brutos do Open-Meteo Forecast
"""
import requests
from datetime import datetime, timedelta

print('🌤️  Obtendo dados horários brutos do Open-Meteo Forecast')
print('='*60)

# Coordenadas de Jaú, SP
lat, long = -22.2964, -48.5578
print('📍 Localização: Jaú, SP')
print('📍 Coordenadas: lat={}, long={}'.format(lat, long))
print()

# Construir URL da API
today = datetime.now().date()
tomorrow = today + timedelta(days=1)
date_format = '%Y-%m-%d'
start_date = today.strftime(date_format)
end_date = tomorrow.strftime(date_format)

url = (
    'https://api.open-meteo.com/v1/forecast?'
    'latitude={}&longitude={}'.format(lat, long) +
    '&start_date={}'.format(start_date) +
    '&end_date={}'.format(end_date) +
    '&hourly=temperature_2m,relative_humidity_2m,' +
    'et0_fao_evapotranspiration,wind_speed_10m,' +
    'shortwave_radiation,precipitation,precipitation_probability' +
    '&timezone=America/Sao_Paulo' +
    '&format=json&models=best_match'
)

print('🔗 URL:', url)
print()

try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        print('✅ Resposta da API recebida!')

        if 'hourly' in data and 'time' in data['hourly']:
            hourly = data['hourly']
            times = hourly['time']

            # Extrair dados brutos (sem processamento estatístico)
            temperature_2m = hourly.get('temperature_2m', [])
            relative_humidity_2m = hourly.get('relative_humidity_2m', [])
            et0_fao_evapotranspiration = hourly.get('et0_fao_evapotranspiration', [])
            wind_speed_10m = hourly.get('wind_speed_10m', [])
            shortwave_radiation = hourly.get('shortwave_radiation', [])
            precipitation = hourly.get('precipitation', [])
            precipitation_probability = hourly.get('precipitation_probability', [])

            print('📊 Total de registros horários:', len(times))
            print('⏰ Período: {} até {}'.format(times[0], times[-1]))
            print()

            # Mostrar dados brutos hora por hora (primeiras 10 horas)
            print('📋 DADOS HORÁRIOS BRUTOS (primeiras 10 horas):')
            print('-' * 100)
            header = '{:<20} {:<8} {:<8} {:<8} {:<8} {:<8} {:<8} {:<12}'.format(
                'Horário', 'T2M', 'RH2M', 'ETO', 'WS10M', 'SW_RAD', 'PRECIP', 'PRECIP_PROB'
            )
            print(header)
            print('-' * 100)

            for i in range(min(10, len(times))):
                horario = times[i]
                t2m = temperature_2m[i] if i < len(temperature_2m) else 'N/A'
                rh2m = relative_humidity_2m[i] if i < len(relative_humidity_2m) else 'N/A'
                eto = et0_fao_evapotranspiration[i] if i < len(et0_fao_evapotranspiration) else 'N/A'
                ws10m = wind_speed_10m[i] if i < len(wind_speed_10m) else 'N/A'
                sw_rad = shortwave_radiation[i] if i < len(shortwave_radiation) else 'N/A'
                precip = precipitation[i] if i < len(precipitation) else 'N/A'
                precip_prob = precipitation_probability[i] if i < len(precipitation_probability) else 'N/A'

                row = '{:<20} {:<8} {:<8} {:<8} {:<8} {:<8} {:<8} {:<12}'.format(
                    horario, t2m, rh2m, eto, ws10m, sw_rad, precip, precip_prob
                )
                print(row)

            print()
            print('📋 LEGENDA:')
            print('• T2M: Temperatura 2m (°C)')
            print('• RH2M: Umidade Relativa 2m (%)')
            print('• ETO: Evapotranspiração (mm)')
            print('• WS10M: Velocidade do Vento 10m (km/h)')
            print('• SW_RAD: Radiação Solar (W/m²)')
            print('• PRECIP: Precipitação (mm)')
            print('• PRECIP_PROB: Probabilidade de Precipitação (%)')

        else:
            print('❌ Dados horários não encontrados na resposta')
            print('Chaves disponíveis:', list(data.keys()))
    else:
        print('❌ Erro HTTP:', response.status_code)
        print('Resposta:', response.text[:200] + '...')

except Exception as e:
    print('❌ Erro:', e)
    import traceback
    traceback.print_exc()

print()
print('='*60)
print('✅ Dados horários brutos obtidos com sucesso!')
