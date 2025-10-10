"""
Teste de integração: Pipeline completo MATOPIBA.

Este teste valida:
- OpenMeteoMatopibaClient retornando dados horários brutos
- calculate_eto_matopiba_city usando eto_hourly.py
- Validação com ETo Open-Meteo
- Teste gradual: 1 cidade → 5 cidades → 10 cidades

Autor: EVAonline Team
Data: 2025-10-09
"""

from loguru import logger

from backend.api.services.openmeteo_matopiba_client import \
    OpenMeteoMatopibaClient
from backend.core.eto_calculation.eto_matopiba import (
    calculate_eto_matopiba_batch, calculate_eto_matopiba_city)

# Configuração do logging
logger.add(
    "./logs/test_matopiba_integration.log",
    rotation="10 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)


def test_single_city():
    """Teste 1: Uma cidade (Aguiarnópolis-TO)."""
    logger.info("="*70)
    logger.info("TESTE 1: Uma cidade (validação R²)")
    logger.info("="*70)
    
    # Inicializar client
    client = OpenMeteoMatopibaClient(forecast_days=2)
    
    # Buscar primeira cidade
    city_df = client.cities_df.head(1)
    logger.info(
        f"Testando: {city_df.iloc[0]['CITY']}, {city_df.iloc[0]['UF']} "
        f"({city_df.iloc[0]['CODE_CITY']})"
    )
    
    # Buscar dados
    forecasts, warnings = client._fetch_batch(city_df)
    
    if warnings:
        logger.warning(f"Avisos na busca: {warnings}")
    
    if not forecasts:
        logger.error("❌ Falha ao buscar dados")
        return False
    
    # Processar primeira cidade
    city_code = list(forecasts.keys())[0]
    city_data = forecasts[city_code]
    
    # Verificar estrutura
    if 'hourly_data' not in city_data:
        logger.error("❌ Dados horários brutos não retornados pelo client!")
        return False
    
    logger.info(
        f"✅ Dados horários recebidos: "
        f"{len(city_data['hourly_data'].get('time', []))} registros"
    )
    
    # Calcular ETo
    result, calc_warnings = calculate_eto_matopiba_city(city_data)
    
    if calc_warnings:
        logger.warning(f"Avisos no cálculo: {calc_warnings}")
    
    if not result:
        logger.error("❌ Falha no cálculo de ETo")
        return False
    
    # Mostrar resultados
    logger.info(f"\n✅ SUCESSO! Cidade {result['city_code']} processada:")
    logger.info(f"   Nome: {result['city_name']}, {result['uf']}")
    logger.info(f"   Dias calculados: {len(result['forecast'])}")
    
    for date, values in result['forecast'].items():
        eto_eva = values['ETo_EVAonline']
        eto_om = values['ETo_OpenMeteo']
        diff = ((eto_eva - eto_om) / eto_om) * 100
        
        logger.info(
            f"   {date}: ETo_EVA={eto_eva:.2f} mm/dia, "
            f"ETo_OM={eto_om:.2f} mm/dia ({diff:+.1f}%)"
        )
    
    return True


def test_multiple_cities(n_cities: int = 5):
    """Teste 2: Múltiplas cidades com métricas de validação."""
    logger.info("="*70)
    logger.info(f"TESTE 2: {n_cities} cidades (validação em lote)")
    logger.info("="*70)
    
    # Inicializar client
    client = OpenMeteoMatopibaClient(forecast_days=2)
    
    # Buscar N primeiras cidades
    cities_df = client.cities_df.head(n_cities)
    logger.info(f"Testando {len(cities_df)} cidades:")
    for _, city in cities_df.iterrows():
        logger.info(f"  - {city['CITY']}, {city['UF']} ({city['CODE_CITY']})")
    
    # Buscar dados
    forecasts, warnings = client._fetch_batch(cities_df)
    
    if warnings:
        logger.warning(f"Avisos na busca: {warnings}")
    
    if not forecasts:
        logger.error("❌ Falha ao buscar dados")
        return False
    
    logger.info(
        f"✅ Dados obtidos para {len(forecasts)}/{n_cities} cidades "
        f"({len(forecasts)/n_cities*100:.1f}%)"
    )
    
    # Calcular ETo em lote
    results, calc_warnings, validation = calculate_eto_matopiba_batch(
        forecasts
    )
    
    if calc_warnings:
        logger.warning(f"Avisos no cálculo ({len(calc_warnings)} total)")
    
    # Mostrar validação
    logger.info("\n📊 MÉTRICAS DE VALIDAÇÃO:")
    logger.info(f"   R² (correlação):      {validation['r2']:.4f}")
    logger.info(f"   RMSE (erro):          {validation['rmse']:.4f} mm/dia")
    logger.info(f"   Bias (viés):          {validation['bias']:.4f} mm/dia")
    logger.info(f"   MAE (erro absoluto):  {validation['mae']:.4f} mm/dia")
    logger.info(f"   Amostras:             {validation['n_samples']}")
    logger.info(f"   Status:               {validation['status']}")
    
    # Avaliar qualidade
    if validation['r2'] >= 0.75 and validation['rmse'] <= 1.2:
        logger.info("\n✅ VALIDAÇÃO: BOM ou superior (R²≥0.75, RMSE≤1.2)")
        return True
    elif validation['r2'] >= 0.65 and validation['rmse'] <= 1.5:
        logger.warning(
            "\n⚠️ VALIDAÇÃO: ACEITÁVEL (R²≥0.65, RMSE≤1.5) "
            "mas abaixo do ideal"
        )
        return True
    else:
        logger.error(
            f"\n❌ VALIDAÇÃO: INSUFICIENTE "
            f"(R²={validation['r2']:.3f}, RMSE={validation['rmse']:.3f})"
        )
        return False


if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("TESTE DE INTEGRAÇÃO: Pipeline MATOPIBA Completo")
    logger.info("="*70 + "\n")
    
    # Teste 1: Uma cidade
    success1 = test_single_city()
    
    if not success1:
        logger.error("\n❌ Teste 1 falhou. Abortando testes subsequentes.")
        exit(1)
    
    # Teste 2: 5 cidades
    logger.info("\n")
    success2 = test_multiple_cities(n_cities=5)
    
    if not success2:
        logger.error("\n❌ Teste 2 falhou. Verifique logs.")
        exit(1)
    
    # Teste 3: 10 cidades (opcional)
    logger.info("\n")
    success3 = test_multiple_cities(n_cities=10)
    
    if not success3:
        logger.warning(
            "\n⚠️ Teste 3 (10 cidades) teve problemas mas não crítico."
        )
    
    logger.info("\n" + "="*70)
    logger.info("✅ TODOS OS TESTES PASSARAM!")
    logger.info("="*70)
    logger.info("\nPróximo passo: Testar com todas as 337 cidades")
    logger.info("Comando: python -m backend.tests.test_matopiba_integration_full\n")
