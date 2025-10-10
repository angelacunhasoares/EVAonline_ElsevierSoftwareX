"""
Script rápido para verificar métricas no cache Redis.
"""
import json

import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Ler metadata (JSON, não pickle)
metadata_str = r.get('matopiba:metadata')
if metadata_str:
    metadata = json.loads(metadata_str)
else:
    print("❌ Cache vazio! Execute o forecast task primeiro.")
    exit(1)

validation = metadata.get('validation', {})

print("\n" + "="*60)
print("📊 MÉTRICAS DE VALIDAÇÃO NO CACHE REDIS")
print("="*60)

print(f"\nR²:     {validation.get('r2', 'N/A')}")
print(f"RMSE:   {validation.get('rmse', 'N/A')} mm/dia")
print(f"Bias:   {validation.get('bias', 'N/A')} mm/dia")
print(f"MAE:    {validation.get('mae', 'N/A')} mm/dia")
print(f"Status: {validation.get('status', 'N/A')}")
print(f"N:      {validation.get('n_samples', 'N/A')} amostras")

print("\n⚠️ IMPORTANTE: Estes valores são do ÚLTIMO cálculo.")
print("   Para ver valores ATUALIZADOS, execute:")
print("   1. python scripts\\trigger_matopiba_forecast.py")
print("   2. Aguarde ~60s (cálculo de 337 cidades)")
print("   3. Re-execute este script")
print("="*60)
