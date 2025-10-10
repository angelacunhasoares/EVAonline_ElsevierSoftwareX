"""
Teste de validação com dados reais do Open-Meteo.

Este script:
1. Baixa dados horários reais do Open-Meteo para uma cidade
2. Calcula ETo usando nosso algoritmo (eto_hourly.py)
3. Compara com ETo do Open-Meteo
4. Mostra métricas de validação: R², RMSE, Bias

Autor: EVAonline Team
Data: 2025-10-09
"""

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import mean_squared_error, r2_score

from backend.core.eto_calculation.eto_hourly import (aggregate_hourly_to_daily,
                                                     calculate_eto_hourly,
                                                     fetch_openmeteo_hourly)

logger.add(
    "./logs/test_eto_validation.log",
    rotation="10 MB",
    level="INFO"
)


def validate_eto(
    city_name: str,
    lat: float,
    lon: float,
    elev: float,
    days: int = 7
):
    """
    Valida ETo calculado vs Open-Meteo para uma cidade.
    
    Args:
        city_name: Nome da cidade
        lat: Latitude
        lon: Longitude
        elev: Elevação (m)
        days: Número de dias para testar (default=7, mín=3, máx=16)
    """
    from datetime import datetime, timedelta
    
    logger.info("=" * 70)
    logger.info(f"VALIDAÇÃO ETo: {city_name}")
    logger.info(f"Coordenadas: ({lat:.4f}, {lon:.4f}), Elev: {elev:.1f}m")
    logger.info(f"Período: {days} dias")
    logger.info("=" * 70)
    
    # 1. Buscar dados reais do Open-Meteo
    logger.info(f"\n[1/4] Buscando {days} dias de dados horários do Open-Meteo...")
    
    # Calcular datas
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=days-1)).strftime('%Y-%m-%d')
    
    data = fetch_openmeteo_hourly(lat, lon, start_date, end_date)
    
    if not data or 'hourly' not in data:
        logger.error("❌ Falha ao buscar dados!")
        return
    
    hourly = data['hourly']
    logger.info(f"✅ Dados recebidos: {len(hourly.get('time', []))} horas")
    
    # 2. Preparar DataFrame
    logger.info("\n[2/4] Preparando dados horários...")
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
        'precipitation': hourly.get('precipitation', []),
        'precipitation_probability': hourly.get('precipitation_probability', []),
        'eto_openmeteo': hourly.get('et0_fao_evapotranspiration', [])
    })
    
    logger.info(f"✅ DataFrame criado: {len(df)} registros")
    logger.info(f"   Período: {df['time'].min()} até {df['time'].max()}")
    
    # 3. Calcular ETo com nosso algoritmo
    logger.info("\n[3/5] Calculando ETo horária com algoritmo EVAonline...")
    df_eto, warnings = calculate_eto_hourly(df, lat, lon, elev)
    
    if df_eto.empty:
        logger.error("❌ Cálculo de ETo falhou!")
        if warnings:
            logger.error(f"Avisos: {warnings}")
        return
    
    logger.info(f"✅ ETo horária calculada: {len(df_eto)} registros")
    if warnings:
        logger.warning(f"⚠️  {len(warnings)} avisos durante cálculo")
    
    # 4. Agregar para diário
    logger.info("\n[4/5] Agregando para valores diários...")
    df_daily, agg_warnings = aggregate_hourly_to_daily(df_eto)
    
    if df_daily.empty:
        logger.error("❌ Agregação falhou!")
        return
    
    logger.info(f"✅ Agregação inicial: {len(df_daily)} dias")
    
    # 5. Filtrar apenas dias com 24 horas completas
    logger.info("\n[5/5] Filtrando dias com dados completos (24h)...")
    
    # Contar horas por dia
    hours_per_day = df_eto.groupby(df_eto['time'].dt.date).size()
    complete_days = hours_per_day[hours_per_day == 24].index
    
    # Filtrar DataFrame diário
    df_daily_complete = df_daily[df_daily['date'].isin(complete_days)].copy()
    
    days_removed = len(df_daily) - len(df_daily_complete)
    if days_removed > 0:
        logger.warning(
            f"⚠️  Removidos {days_removed} dias com dados incompletos"
        )
        logger.info(
            f"   Dias completos: {len(df_daily_complete)} "
            f"(24 horas cada)"
        )
    else:
        logger.info(f"✅ Todos os {len(df_daily)} dias têm 24 horas completas")
    
    if df_daily_complete.empty:
        logger.error("❌ Nenhum dia com 24 horas completas!")
        return
    
    # Usar apenas dias completos para validação
    df_daily = df_daily_complete
    
    # 5. Validação
    logger.info("\n" + "=" * 70)
    logger.info("RESULTADOS DA VALIDAÇÃO")
    logger.info("=" * 70)
    
    # Mostrar dados dia a dia
    logger.info("\n📊 Dados diários:")
    for _, row in df_daily.iterrows():
        logger.info(
            f"  {row['date']}: "
            f"ETo_EVA={row['ETo_daily']:.2f} mm/dia, "
            f"ETo_OM={row.get('ETo_OpenMeteo', np.nan):.2f} mm/dia"
        )
    
    # Calcular métricas
    if 'ETo_OpenMeteo' in df_daily.columns:
        eva = df_daily['ETo_daily'].values
        om = df_daily['ETo_OpenMeteo'].values
        
        # Remover NaN
        mask = ~(np.isnan(eva) | np.isnan(om))
        eva_clean = eva[mask]
        om_clean = om[mask]
        
        if len(eva_clean) > 0:
            # Ordem correta: EVAonline (y_true), OpenMeteo (y_pred)
            r2 = r2_score(eva_clean, om_clean)
            rmse = np.sqrt(mean_squared_error(eva_clean, om_clean))
            bias = np.mean(eva_clean - om_clean)
            mae = np.mean(np.abs(eva_clean - om_clean))
            
            logger.info("\n📈 MÉTRICAS DE VALIDAÇÃO:")
            logger.info(f"  N (amostras):            {len(eva_clean)} dias")
            logger.info(f"  R² (coef. determinação): {r2:.4f}")
            logger.info(f"  RMSE (erro quadrático):  {rmse:.4f} mm/dia")
            logger.info(f"  Bias (viés sistemático): {bias:+.4f} mm/dia")
            logger.info(f"  MAE (erro absoluto):     {mae:.4f} mm/dia")
            
            # Avaliação de confiabilidade do R²
            logger.info("\n📊 CONFIABILIDADE ESTATÍSTICA:")
            n = len(eva_clean)
            if n < 5:
                conf = "❌ MUITO BAIXA - R² não confiável (precisa ≥7 dias)"
            elif n < 7:
                conf = "⚠️  BAIXA - R² indicativo, mas pouco confiável"
            elif n < 10:
                conf = "✅ RAZOÁVEL - R² tem significância estatística"
            elif n < 14:
                conf = "✅ BOA - R² confiável para validação"
            else:
                conf = "✅ EXCELENTE - R² estatisticamente robusto"
            logger.info(f"  {conf}")
            
            # Avaliação
            logger.info("\n🎯 AVALIAÇÃO:")
            if r2 > 0.75:
                logger.info("  ✅ R² > 0.75 - EXCELENTE correlação!")
            elif r2 > 0.60:
                logger.info("  ⚠️  R² entre 0.60-0.75 - BOM, mas pode melhorar")
            else:
                logger.info("  ❌ R² < 0.60 - RUIM, revisar algoritmo")
            
            if rmse < 1.5:
                logger.info("  ✅ RMSE < 1.5 mm/dia - EXCELENTE precisão!")
            elif rmse < 2.5:
                logger.info("  ⚠️  RMSE entre 1.5-2.5 mm/dia - BOM")
            else:
                logger.info("  ❌ RMSE > 2.5 mm/dia - RUIM, grandes erros")
            
            if abs(bias) < 0.5:
                logger.info("  ✅ |Bias| < 0.5 mm/dia - SEM viés sistemático!")
            elif abs(bias) < 1.0:
                logger.info(
                    f"  ⚠️  |Bias| entre 0.5-1.0 mm/dia - "
                    f"{'SUPERESTIMA' if bias > 0 else 'SUBESTIMA'} ligeiramente"
                )
            else:
                logger.info(
                    f"  ❌ |Bias| > 1.0 mm/dia - "
                    f"{'SUPERESTIMA' if bias > 0 else 'SUBESTIMA'} muito!"
                )
    else:
        logger.warning("⚠️  ETo_OpenMeteo não disponível para validação")
    
    logger.info("\n" + "=" * 70)


if __name__ == "__main__":
    logger.info("🌾 TESTE: Validação ETo com dados reais Open-Meteo\n")
    
    # Testar com cidade do MATOPIBA
    # Aguiarnópolis, TO (primeira cidade do CSV alfabeticamente)
    
    logger.info("=" * 70)
    logger.info("📊 ANÁLISE: Quantidade de dias vs Confiabilidade do R²")
    logger.info("=" * 70)
    logger.info("• 3 dias  (mínimo):     R² não confiável, serve apenas para debug")
    logger.info("• 7 dias  (recomendado): R² começa a ter significância")
    logger.info("• 10 dias (bom):        R² confiável para validação")
    logger.info("• 14+ dias (ideal):     R² estatisticamente robusto")
    logger.info("=" * 70 + "\n")
    
    # Teste com 14 dias (apenas dias completos com 24h)
    logger.info("🎯 Executando validação com 14 dias (dados completos)")
    logger.info("   Filtrando apenas dias com 24 horas para análise precisa\n")
    
    validate_eto(
        city_name="Aguiarnópolis (TO)",
        lat=-6.5472,
        lon=-47.4705,
        elev=173.19,
        days=14  # 14 dias para R² estatisticamente robusto
    )
    
    logger.info("\n✅ Teste concluído!")
    logger.info(
        "\n� RESULTADOS: Com 14 dias completos, R² tem alta confiança estatística"
    )
    logger.info(
        "   Dias incompletos (parciais) foram automaticamente removidos"
    )
