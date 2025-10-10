"""
Debug detalhado de dia com alta ETo (problema de superestimação).

Foca no dia 18/10/2025 onde:
- ETo_EVA = 10.04 mm/dia (nosso cálculo)
- ETo_OM = 7.30 mm/dia (Open-Meteo)
- Erro = +37.5% (MUITO ALTO!)

Objetivo: Identificar qual componente está causando superestimação.
"""

import numpy as np
import pandas as pd
from loguru import logger

from backend.core.eto_calculation.eto_hourly import (ALBEDO, CP, EPS, LAMBDA,
                                                     SIGMA,
                                                     calculate_eto_hourly,
                                                     fetch_openmeteo_hourly)

logger.add("./logs/debug_high_eto.log", rotation="10 MB", level="DEBUG")


def analyze_day(date_str: str, lat: float, lon: float, elev: float):
    """
    Analisa componentes de ETo para um dia específico.
    
    Args:
        date_str: Data no formato 'YYYY-MM-DD'
        lat, lon, elev: Coordenadas da cidade
    """
    logger.info("=" * 80)
    logger.info(f"🔍 ANÁLISE DETALHADA: {date_str}")
    logger.info("=" * 80)
    
    # Buscar dados (dia anterior até dia seguinte para contexto)
    from datetime import datetime, timedelta
    target_date = datetime.strptime(date_str, '%Y-%m-%d')
    start_date = (target_date - timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    logger.info(f"\n📥 Buscando dados: {start_date} a {end_date}")
    data = fetch_openmeteo_hourly(lat, lon, start_date, end_date)
    
    if not data or 'hourly' not in data:
        logger.error("❌ Falha ao buscar dados!")
        return
    
    # Preparar DataFrame
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
    
    # Filtrar apenas o dia alvo
    df_day = df[df['time'].dt.date == target_date.date()].copy()
    
    if df_day.empty:
        logger.error(f"❌ Sem dados para {date_str}")
        return
    
    logger.info(f"✅ {len(df_day)} horas de dados para {date_str}")
    
    # Calcular ETo
    logger.info("\n🧮 Calculando ETo com nosso algoritmo...")
    df_eto, warnings = calculate_eto_hourly(df_day, lat, lon, elev)
    
    if df_eto.empty:
        logger.error("❌ Cálculo falhou!")
        return
    
    # Análise horária
    logger.info("\n" + "=" * 80)
    logger.info("📊 ANÁLISE HORÁRIA")
    logger.info("=" * 80)
    
    eto_eva_hourly = df_eto['ETo_hour'].values
    eto_om_hourly = df_eto['eto_openmeteo'].values
    
    # Estatísticas diárias
    eto_eva_daily = np.sum(eto_eva_hourly)
    eto_om_daily = np.sum(eto_om_hourly)
    diff = eto_eva_daily - eto_om_daily
    pct = (diff / eto_om_daily) * 100
    
    logger.info(f"\n🎯 TOTAIS DIÁRIOS:")
    logger.info(f"   ETo_EVA: {eto_eva_daily:.2f} mm/dia")
    logger.info(f"   ETo_OM:  {eto_om_daily:.2f} mm/dia")
    logger.info(f"   Diferença: {diff:+.2f} mm/dia ({pct:+.1f}%)")
    
    # Identificar horas problemáticas
    logger.info(f"\n⚠️  HORAS COM MAIOR DISCREPÂNCIA:")
    hourly_diff = eto_eva_hourly - eto_om_hourly
    worst_hours = np.argsort(np.abs(hourly_diff))[-5:][::-1]
    
    for idx in worst_hours:
        hour = df_eto.iloc[idx]
        h_diff = hourly_diff[idx]
        h_pct = (h_diff / eto_om_hourly[idx] * 100) if eto_om_hourly[idx] > 0 else 0
        
        logger.info(
            f"\n   {hour['time'].strftime('%H:%M')}: "
            f"EVA={eto_eva_hourly[idx]:.3f}, OM={eto_om_hourly[idx]:.3f} "
            f"({h_diff:+.3f} mm, {h_pct:+.1f}%)"
        )
        logger.info(f"      T={hour['temp']:.1f}°C, u2={hour['ws']:.1f}m/s, "
                   f"Rs={hour['radiation']:.0f}W/m²")
        logger.info(f"      Rn={hour.get('Rn', np.nan):.3f}MJ/m²/h, "
                   f"G={hour.get('G', np.nan):.3f}MJ/m²/h")
        logger.info(f"      VPD_calc={hour.get('vpd_calc', np.nan):.2f}kPa, "
                   f"VPD_API={hour.get('vapour_pressure_deficit', np.nan):.2f}kPa")
    
    # Análise de componentes
    logger.info(f"\n" + "=" * 80)
    logger.info("🔬 ANÁLISE DE COMPONENTES (médias do dia)")
    logger.info("=" * 80)
    
    # Condições meteorológicas
    logger.info(f"\n☀️  METEOROLOGIA:")
    logger.info(f"   Temp: {df_day['temp'].mean():.1f}°C "
               f"(min {df_day['temp'].min():.1f}, max {df_day['temp'].max():.1f})")
    logger.info(f"   RH: {df_day['rh'].mean():.0f}% "
               f"(min {df_day['rh'].min():.0f}, max {df_day['rh'].max():.0f})")
    logger.info(f"   Vento: {df_day['ws'].mean():.1f}m/s "
               f"(min {df_day['ws'].min():.1f}, max {df_day['ws'].max():.1f})")
    logger.info(f"   Radiação: {df_day['radiation'].mean():.0f}W/m² "
               f"(max {df_day['radiation'].max():.0f})")
    logger.info(f"   Nuvens: {df_day['cloud_cover'].mean():.0f}%")
    
    # Componentes calculados (apenas horas diurnas com Rs > 0)
    df_day_only = df_eto[df_eto['radiation'] > 10].copy()
    
    if not df_day_only.empty:
        logger.info(f"\n🌞 COMPONENTES DIURNOS (Rs > 10 W/m²):")
        logger.info(f"   Rn médio: {df_day_only['Rn'].mean():.3f} MJ/m²/h")
        logger.info(f"   G médio: {df_day_only['G'].mean():.3f} MJ/m²/h")
        logger.info(f"   (Rn-G) médio: {(df_day_only['Rn'] - df_day_only['G']).mean():.3f} MJ/m²/h")
        logger.info(f"   Ratio G/Rn: {(df_day_only['G']/df_day_only['Rn']).mean():.1%}")
        logger.info(f"   VPD_calc médio: {df_day_only['vpd_calc'].mean():.2f} kPa")
        logger.info(f"   VPD_API médio: {df_day_only['vapour_pressure_deficit'].mean():.2f} kPa")
        
        # Comparação VPD
        vpd_diff = df_day_only['vpd_calc'].mean() - df_day_only['vapour_pressure_deficit'].mean()
        logger.info(f"   Diferença VPD: {vpd_diff:+.2f} kPa")
    
    # Diagnóstico
    logger.info(f"\n" + "=" * 80)
    logger.info("💡 DIAGNÓSTICO")
    logger.info("=" * 80)
    
    # Verificar possíveis problemas
    issues = []
    
    # 1. G muito baixo?
    if not df_day_only.empty:
        g_ratio = (df_day_only['G']/df_day_only['Rn']).mean()
        if g_ratio < 0.08:
            issues.append(
                f"⚠️  G/Rn = {g_ratio:.1%} (muito baixo! FAO-56 sugere ~10% diurno)"
            )
    
    # 2. VPD superestimado?
    if not df_day_only.empty:
        vpd_ratio = df_day_only['vpd_calc'].mean() / df_day_only['vapour_pressure_deficit'].mean()
        if vpd_ratio > 1.15:
            issues.append(
                f"⚠️  VPD calculado {(vpd_ratio-1)*100:.0f}% maior que API "
                f"(superestima demanda evaporativa)"
            )
    
    # 3. Condições extremas?
    if df_day['temp'].max() > 35:
        issues.append(f"⚠️  Temperatura extrema: {df_day['temp'].max():.1f}°C")
    if df_day['rh'].min() < 30:
        issues.append(f"⚠️  Umidade muito baixa: {df_day['rh'].min():.0f}%")
    if df_day['ws'].max() > 8:
        issues.append(f"⚠️  Vento forte: {df_day['ws'].max():.1f}m/s")
    
    if issues:
        logger.warning("\n🔴 POSSÍVEIS PROBLEMAS IDENTIFICADOS:")
        for issue in issues:
            logger.warning(f"   {issue}")
    else:
        logger.info("\n✅ Nenhum problema óbvio identificado nos componentes")
    
    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    logger.info("🌾 DEBUG: Dias com Alta ETo (superestimação)\n")
    
    # Aguiarnópolis, TO
    city_lat = -6.5472
    city_lon = -47.4705
    city_elev = 173.19
    
    # Analisar os 3 piores dias
    problem_days = [
        ('2025-10-17', 'Dia 17: ETo_EVA=9.26 vs ETo_OM=7.01 (+32%)'),
        ('2025-10-18', 'Dia 18: ETo_EVA=10.04 vs ETo_OM=7.30 (+38%)'),
        ('2025-10-19', 'Dia 19: ETo_EVA=9.86 vs ETo_OM=6.71 (+47%)')
    ]
    
    for date_str, description in problem_days:
        logger.info(f"\n{'='*80}")
        logger.info(f"📅 {description}")
        logger.info(f"{'='*80}")
        analyze_day(date_str, city_lat, city_lon, city_elev)
        logger.info("\n\n")
    
    logger.info("✅ Análise concluída! Verifique logs/debug_high_eto.log")
