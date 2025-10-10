"""
Debug detalhado dos componentes de ETo.

Compara cada componente do cálculo:
- Ra, Rn, G, VPD, u2, gamma, delta
- Identifica onde está o erro

Autor: EVAonline Team
Data: 2025-10-09
"""

import numpy as np
import pandas as pd
from loguru import logger

from backend.core.eto_calculation.eto_hourly import fetch_openmeteo_hourly

logger.add("./logs/debug_eto.log", rotation="10 MB", level="DEBUG")


def debug_eto_hour(row, lat, lon, elev):
    """Debug de um único cálculo horário."""
    from backend.core.eto_calculation.eto_hourly import (
        ALBEDO, CP, EPS, GSC, LAMBDA, SIGMA, extraterrestrial_radiation)
    
    dt = pd.to_datetime(row['time'])
    T = row['temp']
    u10 = row['ws']
    Rs_w = row['radiation']
    
    print(f"\n{'='*70}")
    print(f"🕐 HORA: {dt}")
    print(f"{'='*70}")
    
    # INPUT
    print(f"\n📥 INPUT:")
    print(f"  T = {T:.2f} °C")
    print(f"  u10 = {u10:.2f} m/s")
    print(f"  Rs = {Rs_w:.2f} W/m²")
    print(f"  RH = {row.get('rh', np.nan):.1f} %")
    if 'dew_point' in row:
        print(f"  Td = {row['dew_point']:.2f} °C")
    
    # AJUSTE VENTO
    if u10 > 0:
        u2 = u10 * (4.87 / np.log(67.8 * 10 - 5.42))
    else:
        u2 = 0.5
    print(f"\n🌬️  VENTO:")
    print(f"  u10 = {u10:.2f} m/s → u2 = {u2:.2f} m/s")
    
    # PRESSÃO
    if 'surface_pressure' in row and pd.notna(row['surface_pressure']):
        P = row['surface_pressure'] / 10.0
        print(f"\n🔽 PRESSÃO:")
        print(f"  P_API = {row['surface_pressure']:.1f} hPa → {P:.2f} kPa")
    else:
        P = 101.3 * ((293 - 0.0065 * elev) / 293) ** 5.26
        print(f"\n🔽 PRESSÃO (calculada):")
        print(f"  P = {P:.2f} kPa")
    
    # GAMMA
    gamma = (CP * P) / (EPS * LAMBDA)
    print(f"  γ = {gamma:.4f} kPa/°C")
    
    # VAPOR PRESSURE
    es = 0.6108 * np.exp((17.27 * T) / (T + 237.3))
    
    if 'dew_point' in row and pd.notna(row['dew_point']):
        Td = row['dew_point']
        ea = 0.6108 * np.exp((17.27 * Td) / (Td + 237.3))
        print(f"\n💧 VAPOR (de Td):")
        print(f"  es = {es:.4f} kPa")
        print(f"  ea = {ea:.4f} kPa (de Td={Td:.2f}°C)")
    elif 'rh' in row and pd.notna(row['rh']):
        RH = row['rh']
        ea = es * (RH / 100.0)
        print(f"\n💧 VAPOR (de RH):")
        print(f"  es = {es:.4f} kPa")
        print(f"  ea = {ea:.4f} kPa (de RH={RH:.1f}%)")
    else:
        ea = es * 0.7
        print(f"\n💧 VAPOR (fallback 70%):")
        print(f"  es = {es:.4f} kPa")
        print(f"  ea = {ea:.4f} kPa")
    
    vpd = es - ea
    print(f"  VPD = {vpd:.4f} kPa")
    
    if 'vapour_pressure_deficit' in row and pd.notna(row['vapour_pressure_deficit']):
        vpd_api = row['vapour_pressure_deficit']
        print(f"  VPD_API = {vpd_api:.4f} kPa (diff: {abs(vpd-vpd_api):.4f})")
    
    # DELTA
    delta = (4098 * es) / ((T + 237.3) ** 2)
    print(f"  Δ = {delta:.4f} kPa/°C")
    
    # RADIAÇÃO
    Rs = Rs_w * 0.0036  # W/m² → MJ/m²/h
    print(f"\n☀️  RADIAÇÃO:")
    print(f"  Rs = {Rs_w:.2f} W/m² → {Rs:.4f} MJ/m²/h")
    
    lat_rad = np.deg2rad(lat)
    Ra = extraterrestrial_radiation(dt, lat_rad, lon)
    print(f"  Ra (extraterrestre) = {Ra:.4f} MJ/m²/h")
    
    Rso = (0.75 + 2e-5 * elev) * Ra
    print(f"  Rso (céu claro) = {Rso:.4f} MJ/m²/h")
    
    if Rso > 0.001 and Rs > 0:
        ratio = Rs / Rso
        print(f"  Ratio Rs/Rso = {ratio:.4f}")
    else:
        ratio = 0.3
        print(f"  Ratio Rs/Rso = {ratio:.4f} (noite/fallback)")
    
    # RN
    Tk = T + 273.16
    Rnl = (SIGMA * (Tk ** 4) *
           (0.34 - 0.14 * np.sqrt(ea)) *
           (1.35 * ratio - 0.35))
    Rns = (1 - ALBEDO) * Rs
    Rn = Rns - Rnl
    
    print(f"\n🌡️  BALANÇO RADIATIVO:")
    print(f"  Rnl (onda longa) = {Rnl:.4f} MJ/m²/h")
    print(f"  Rns (onda curta) = {Rns:.4f} MJ/m²/h")
    print(f"  Rn (líquida) = {Rn:.4f} MJ/m²/h")
    
    # G
    if Rn > 0:
        G = 0.1 * Rn
        print(f"  G (dia, 0.1*Rn) = {G:.4f} MJ/m²/h")
    else:
        G = 0.5 * Rn
        print(f"  G (noite, 0.5*Rn) = {G:.4f} MJ/m²/h")
    
    # PM EQUATION
    print(f"\n🌾 PENMAN-MONTEITH (Cn=37, Cd=0.34):")
    num1 = 0.408 * delta * (Rn - G)
    num2 = gamma * (37 / (T + 273)) * u2 * vpd
    numerator = num1 + num2
    denominator = delta + gamma * (1 + 0.34 * u2)
    
    print(f"  Termo radiativo: 0.408×Δ×(Rn-G) = {num1:.4f}")
    print(f"  Termo aerodinâmico: γ×(37/(T+273))×u2×VPD = {num2:.4f}")
    print(f"  Numerador = {numerator:.4f}")
    print(f"  Denominador = {denominator:.4f}")
    
    if denominator > 0:
        ETo_hour = max(0, numerator / denominator)
        print(f"  ➡️  ETo_hora = {ETo_hour:.4f} mm/h")
    else:
        ETo_hour = 0
        print(f"  ⚠️  Denominador zero!")
    
    # COMPARAR COM OPEN-METEO
    if 'eto_openmeteo' in row and pd.notna(row['eto_openmeteo']):
        eto_om = row['eto_openmeteo']
        diff = ETo_hour - eto_om
        ratio_eto = ETo_hour / eto_om if eto_om > 0 else np.inf
        print(f"\n📊 COMPARAÇÃO:")
        print(f"  ETo_EVA = {ETo_hour:.4f} mm/h")
        print(f"  ETo_OM  = {eto_om:.4f} mm/h")
        print(f"  Diff    = {diff:+.4f} mm/h ({ratio_eto:.2f}x)")


if __name__ == "__main__":
    logger.info("🔍 DEBUG: Componentes de ETo horária\n")
    
    # Buscar dados
    lat, lon, elev = -6.5472, -47.4705, 173.19
    data = fetch_openmeteo_hourly(lat, lon)
    
    if not data or 'hourly' not in data:
        print("❌ Erro ao buscar dados!")
        sys.exit(1)
    
    hourly = data['hourly']
    df = pd.DataFrame({
        'time': pd.to_datetime(hourly['time']),
        'temp': hourly.get('temperature_2m', []),
        'dew_point': hourly.get('dew_point_2m', []),
        'rh': hourly.get('relative_humidity_2m', []),
        'ws': hourly.get('wind_speed_10m', []),
        'radiation': hourly.get('shortwave_radiation', []),
        'surface_pressure': hourly.get('surface_pressure', []),
        'cloud_cover': hourly.get('cloud_cover', []),
        'vapour_pressure_deficit': hourly.get('vapour_pressure_deficit', []),
        'eto_openmeteo': hourly.get('et0_fao_evapotranspiration', [])
    })
    
    print(f"📅 Dados: {len(df)} horas de {df['time'].min()} até {df['time'].max()}")
    
    # Debug horas específicas
    # Hora com radiação (meio-dia)
    midday_idx = df[df['time'].dt.hour == 12].index[0]
    print(f"\n🌞 ANALISANDO HORA COM SOL (meio-dia):")
    debug_eto_hour(df.iloc[midday_idx], lat, lon, elev)
    
    # Hora noturna
    night_idx = df[df['time'].dt.hour == 0].index[0]
    print(f"\n🌙 ANALISANDO HORA NOTURNA:")
    debug_eto_hour(df.iloc[night_idx], lat, lon, elev)
    
    # Manhã
    morning_idx = df[df['time'].dt.hour == 9].index[0]
    print(f"\n🌅 ANALISANDO MANHÃ:")
    debug_eto_hour(df.iloc[morning_idx], lat, lon, elev)
    
    print(f"\n{'='*70}")
    print("✅ Debug concluído!")
