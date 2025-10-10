"""
Teste COMPLETO do pipeline MATOPIBA com dados HORÁRIOS.

Testa:
1. Download de dados horários
2. Agregação diária
3. Pré-processamento EVAonline
4. Cálculo ETo EVAonline
5. Validação contra ETo Open-Meteo
"""

import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from api.services.openmeteo_matopiba_client import OpenMeteoMatopibaClient
from core.eto_calculation.eto_matopiba import calculate_eto_matopiba_city


def test_full_pipeline():
    """Testa pipeline completo: dados horários → ETo EVAonline."""
    
    print("="*70)
    print("TESTE: Pipeline Completo MATOPIBA (Dados Horários → ETo)")
    print("="*70)
    
    # 1. Inicializar cliente
    print("\n📡 1. Buscando dados horários do Open-Meteo...")
    client = OpenMeteoMatopibaClient(forecast_days=2)
    
    # Aguiarnópolis, TO - cidade dos seus testes
    city_code = '1700301'
    forecast_data, warnings = client.get_forecast_single_city(city_code)
    
    if not forecast_data:
        print("   ❌ Falha ao buscar dados!")
        return
    
    city_info = forecast_data['city_info']
    print(f"   ✅ Dados recebidos: {city_info['name']} ({city_info['uf']})")
    print(f"   📍 Coordenadas: ({city_info['latitude']:.4f}, {city_info['longitude']:.4f})")
    print(f"   📅 Dias de previsão: {len(forecast_data['forecast'])}")
    
    # Mostrar dados Open-Meteo agregados
    print("\n📊 2. Dados Open-Meteo (agregados diariamente):")
    for date_str, values in sorted(forecast_data['forecast'].items()):
        print(f"\n   📅 {date_str}")
        print(f"      • Temp: {values['T2M_MIN']:.1f}°C - {values['T2M_MAX']:.1f}°C (média: {values['T2M']:.1f}°C)")
        print(f"      • Umidade: {values['RH2M']:.1f}%")
        print(f"      • Vento: {values['WS2M']:.1f} m/s")
        print(f"      • Radiação: {values['ALLSKY_SFC_SW_DWN']:.2f} MJ/m²/dia")
        print(f"      • Precipitação: {values['PRECTOTCORR']:.1f} mm")
        print(f"      • 🔵 ETo Open-Meteo: {values['ETo_OpenMeteo']:.2f} mm/dia")
    
    # 3. Calcular ETo EVAonline
    print("\n⚙️  3. Calculando ETo EVAonline (Penman-Monteith)...")
    result, eto_warnings = calculate_eto_matopiba_city(forecast_data)
    
    if not result:
        print("   ❌ Falha no cálculo ETo!")
        if eto_warnings:
            for w in eto_warnings:
                print(f"   ⚠️  {w}")
        return
    
    print("   ✅ ETo EVAonline calculada!")
    
    # 4. Comparar resultados
    print("\n📈 4. COMPARAÇÃO: ETo EVAonline vs ETo Open-Meteo:")
    print("   " + "-"*66)
    print("   Data       │ ETo EVAonline │ ETo OpenMeteo │ Diferença │ Dif%")
    print("   " + "-"*66)
    
    for date_str in sorted(result['forecast'].keys()):
        values = result['forecast'][date_str]
        eto_eva = values['ETo_EVAonline']
        eto_om = values['ETo_OpenMeteo']
        diff = eto_eva - eto_om
        diff_pct = (diff / eto_om) * 100
        
        print(f"   {date_str} │  {eto_eva:6.2f} mm/dia │  {eto_om:6.2f} mm/dia │ {diff:+5.2f} mm │ {diff_pct:+5.1f}%")
    
    print("   " + "-"*66)
    
    # 5. Calcular métricas de validação
    eto_eva_list = [v['ETo_EVAonline'] for v in result['forecast'].values()]
    eto_om_list = [v['ETo_OpenMeteo'] for v in result['forecast'].values()]
    
    import numpy as np
    from sklearn.metrics import mean_squared_error, r2_score
    
    r2 = r2_score(eto_om_list, eto_eva_list)
    rmse = np.sqrt(mean_squared_error(eto_om_list, eto_eva_list))
    bias = np.mean(np.array(eto_eva_list) - np.array(eto_om_list))
    
    print("\n📊 5. MÉTRICAS DE VALIDAÇÃO:")
    print(f"   • R² (coeficiente de determinação): {r2:.3f}")
    print(f"   • RMSE (erro quadrático médio): {rmse:.3f} mm/dia")
    print(f"   • Bias (viés sistemático): {bias:+.3f} mm/dia")
    
    # Classificação
    if r2 >= 0.90 and rmse <= 0.5:
        status = "EXCELENTE ⭐⭐⭐"
    elif r2 >= 0.85 and rmse <= 0.8:
        status = "MUITO BOM ⭐⭐"
    elif r2 >= 0.75 and rmse <= 1.2:
        status = "BOM ⭐"
    elif r2 >= 0.65 and rmse <= 1.5:
        status = "ACEITÁVEL ✓"
    else:
        status = "INSUFICIENTE ✗"
    
    print(f"\n   📌 Status de Validação: {status}")
    print("   (Baseado em Allen et al. 1998, FAO-56)")
    
    # Avisos
    all_warnings = warnings + eto_warnings
    if all_warnings:
        print(f"\n⚠️  Avisos ({len(all_warnings)}):")
        for w in set(all_warnings):  # Remove duplicatas
            print(f"   • {w}")
    
    print("\n" + "="*70)
    print("✅ TESTE COMPLETO CONCLUÍDO!")
    print("="*70)
    
    print("\n💡 CONCLUSÃO:")
    print("   Com dados HORÁRIOS agregados diariamente, esperamos que:")
    print("   • R² > 0.75 (boa correlação)")
    print("   • RMSE < 1.5 mm/dia (erro aceitável)")
    print("   • Bias próximo de 0 (sem viés sistemático)")
    print("\n   Se os resultados ainda forem ruins, o problema está em:")
    print("   • Conversão de unidades (radiação W/m² → MJ/m²/dia)")
    print("   • Parâmetros do cálculo Penman-Monteith")
    print("   • Pré-processamento dos dados")


if __name__ == "__main__":
    test_full_pipeline()
