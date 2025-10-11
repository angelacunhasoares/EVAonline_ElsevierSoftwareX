"""
Script de teste para executar a task MATOPIBA manualmente.
"""
import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.infrastructure.celery.tasks.matopiba_forecast_task import \
    update_matopiba_forecasts

if __name__ == "__main__":
    print("="*60)
    print("TESTE MANUAL: Task MATOPIBA")
    print("="*60)
    
    # Executar task
    result = update_matopiba_forecasts()
    
    print("\n" + "="*60)
    print("RESULTADO FINAL:")
    print("="*60)
    print(result)
    print("="*60)
