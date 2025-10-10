"""
Trigger manual do cálculo MATOPIBA para testar correção do R².

Executa calculate_eto_matopiba_batch() diretamente (sem Celery)
para ver métricas atualizadas imediatamente.
"""

import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.api.services.openmeteo_matopiba_client import \
    OpenMeteoMatopibaClient
from backend.core.eto_calculation.eto_matopiba import \
    calculate_eto_matopiba_batch


def main():
    print("="*70)
    print("🚀 TRIGGER MANUAL: Cálculo ETo MATOPIBA")
    print("="*70)
    print("\n⚠️  Este script chama a função DIRETAMENTE (sem Celery)")
    print("    Tempo estimado: ~60-90 segundos para 337 cidades\n")
    
    # Confirmar
    resposta = input("Continuar? (s/N): ").strip().lower()
    if resposta != 's':
        print("❌ Cancelado pelo usuário")
        return
    
    print("\n1️⃣ Buscando dados Open-Meteo...")
    client = OpenMeteoMatopibaClient()
    
    try:
        # Buscar dados (hoje + amanhã)
        forecasts, warnings_api = client.get_forecasts_all_cities()
        
        if not forecasts:
            print("❌ Erro ao buscar dados da API")
            return
        
        print(f"✅ Dados recebidos: {len(forecasts)} cidades")
        
        if warnings_api:
            print(f"⚠️  {len(warnings_api)} avisos da API")
        
        # Calcular ETo
        print("\n2️⃣ Calculando ETo para todas as cidades...")
        print("   (aguarde ~60s...)")
        
        # calculate_eto_matopiba_batch espera cities_data (dict com city_code: city_data)
        results, warnings, validation_metrics = calculate_eto_matopiba_batch(
            cities_data=forecasts
        )
        
        print(f"\n✅ Cálculo concluído: {len(results)} cidades")
        
        # Exibir métricas
        print("\n" + "="*70)
        print("📊 MÉTRICAS DE VALIDAÇÃO (APÓS CORREÇÃO R²)")
        print("="*70)
        
        r2 = validation_metrics.get('r2', 0)
        rmse = validation_metrics.get('rmse', 0)
        bias = validation_metrics.get('bias', 0)
        mae = validation_metrics.get('mae', 0)
        n_samples = validation_metrics.get('n_samples', 0)
        status = validation_metrics.get('status', 'N/A')
        
        print(f"\n  R² (correlação):      {r2:.4f}")
        print(f"  RMSE (erro):          {rmse:.3f} mm/dia")
        print(f"  Bias (viés):          {bias:.3f} mm/dia")
        print(f"  MAE (erro absoluto):  {mae:.3f} mm/dia")
        print(f"  Amostras:             {n_samples}")
        print(f"  Status:               {status}")
        
        # Análise
        print("\n" + "="*70)
        print("🔍 ANÁLISE")
        print("="*70)
        
        if r2 < 0:
            print("\n❌ R² AINDA NEGATIVO!")
            print("   Possíveis causas:")
            print("   - Ordem em outro local não corrigida")
            print("   - Dados corrompidos no cache")
            print("   - Bug em aggregate_hourly_to_daily")
        elif r2 < 0.65:
            print(f"\n⚠️  R² = {r2:.3f} - INSUFICIENTE")
            print("   Esperado: 0.65-0.85 para correlação boa")
            print("   Problema pode estar no cálculo, não só validação")
        elif r2 < 0.75:
            print(f"\n✅ R² = {r2:.3f} - BOM!")
            print("   Correção funcionou! R² agora é positivo e aceitável.")
        else:
            print(f"\n🎉 R² = {r2:.3f} - EXCELENTE!")
            print("   Correção funcionou perfeitamente!")
        
        # Verificar 87% discrepância
        if abs(bias) > 3.0:
            print(f"\n⚠️  Bias = {bias:.2f} mm/dia - MUITO ALTO!")
            print("   ETo_EVAonline ainda muito diferente de ETo_OpenMeteo")
            print("   Próximo passo: investigar unidades/agregação")
        elif abs(bias) > 1.0:
            print(f"\n⚠️  Bias = {bias:.2f} mm/dia - MODERADO")
            print("   Diferença aceitável para modelos diferentes")
        else:
            print(f"\n✅ Bias = {bias:.2f} mm/dia - EXCELENTE!")
        
        # Avisos
        if warnings:
            print(f"\n⚠️  {len(warnings)} avisos durante cálculo")
            print("   Primeiros 5:")
            for w in warnings[:5]:
                print(f"   - {w}")
        
        print("\n" + "="*70)
        print("✅ TRIGGER CONCLUÍDO")
        print("="*70)
        print("\nPróximos passos:")
        print("  1. Se R² positivo → correção funcionou! ✅")
        print("  2. Se Bias alto → investigar unidades/agregação")
        print("  3. Executar vetorização para melhorar performance")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
