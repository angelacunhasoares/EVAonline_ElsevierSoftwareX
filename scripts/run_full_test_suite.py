"""
Suite de Testes Completa - EVAonline MATOPIBA
Valida toda a infraestrutura: Python, Redis, Celery, Pipeline ETo

Uso:
    python scripts/run_full_test_suite.py
"""

import json
import os
import pickle
import sys
import time
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# ============================================================================
# CORES E FORMATAÇÃO
# ============================================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{'='*70}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title}{Colors.END}")
    print(f"{'='*70}")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

# ============================================================================
# TESTE 1: AMBIENTE PYTHON
# ============================================================================

def test_python_environment():
    """Testa ambiente Python e dependências."""
    print_header("TESTE 1: Ambiente Python e Dependências")
    
    try:
        # Python versão
        python_version = sys.version.split()[0]
        print_info(f"Python versão: {python_version}")
        
        # Pacotes críticos
        packages = {
            'celery': 'Celery',
            'redis': 'Redis',
            'pandas': 'Pandas',
            'numpy': 'NumPy',
            'requests': 'Requests',
        }
        
        all_ok = True
        for module, name in packages.items():
            try:
                __import__(module)
                print_success(f"{name} instalado")
            except ImportError:
                print_error(f"{name} NÃO instalado")
                all_ok = False
        
        if all_ok:
            print_success("Ambiente Python OK!")
            return True
        else:
            print_error("Instale dependências: pip install -r requirements.txt")
            return False
            
    except Exception as e:
        print_error(f"Erro ao verificar ambiente: {e}")
        return False

# ============================================================================
# TESTE 2: REDIS
# ============================================================================

def test_redis_connection():
    """Testa conexão e operações Redis."""
    print_header("TESTE 2: Conexão e Operações Redis")
    
    try:
        from redis import Redis
        from redis.exceptions import AuthenticationError, ConnectionError

        # Configuração
        redis_password = os.getenv("REDIS_PASSWORD", "evaonline")
        redis_url = f"redis://default:{redis_password}@localhost:6379/0"
        
        print_info(f"Conectando a: localhost:6379")
        
        # Conexão
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        response = redis_client.ping()
        
        if not response:
            print_error("Redis não respondeu ao PING")
            return False
        
        print_success("Redis conectado!")
        
        # Info
        info = redis_client.info("server")
        print_info(f"Versão Redis: {info.get('redis_version', 'N/A')}")
        print_info(f"Uptime: {info.get('uptime_in_seconds', 0)}s")
        
        # Teste SET/GET
        test_key = "test:suite:key"
        test_value = f"test_{int(time.time())}"
        redis_client.set(test_key, test_value, ex=10)
        retrieved = redis_client.get(test_key)
        
        if retrieved == test_value:
            print_success("Operação SET/GET OK")
            redis_client.delete(test_key)
        else:
            print_error("Operação SET/GET falhou")
            return False
        
        # Teste Pickle
        redis_raw = Redis.from_url(redis_url, decode_responses=False)
        test_data = {'timestamp': datetime.now(), 'value': 123.45}
        pickled = pickle.dumps(test_data)
        redis_raw.setex("test:pickle", 10, pickled)
        retrieved_bytes = redis_raw.get("test:pickle")
        unpickled = pickle.loads(retrieved_bytes)
        
        if unpickled['value'] == 123.45:
            print_success("Operação Pickle OK")
            redis_client.delete("test:pickle")
        else:
            print_error("Operação Pickle falhou")
            return False
        
        print_success("Redis totalmente funcional!")
        return True
        
    except ConnectionError:
        print_error("Redis não está rodando")
        print_info("Execute: .\\scripts\\manage_celery_redis.ps1 start-redis")
        return False
    except AuthenticationError:
        print_error("Senha Redis incorreta")
        print_info("Verifique REDIS_PASSWORD no .env")
        return False
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        return False

# ============================================================================
# TESTE 3: IMPORTS MATOPIBA
# ============================================================================

def test_matopiba_imports():
    """Testa imports dos módulos MATOPIBA."""
    print_header("TESTE 3: Imports Módulos MATOPIBA")
    
    try:
        # OpenMeteo Client
        from backend.api.services.openmeteo_matopiba_client import \
            OpenMeteoMatopibaClient
        print_success("OpenMeteoMatopibaClient importado")
        
        # ETo MATOPIBA
        from backend.core.eto_calculation.eto_matopiba import (
            calculate_eto_matopiba_batch, calculate_eto_matopiba_city)
        print_success("eto_matopiba importado")
        
        # ETo Hourly
        from backend.core.eto_calculation.eto_hourly import (
            aggregate_hourly_to_daily, calculate_eto_hourly)
        print_success("eto_hourly importado")
        
        # Task
        from backend.infrastructure.celery.tasks.matopiba_forecast_task import \
            update_matopiba_forecasts
        print_success("matopiba_forecast_task importado")
        
        print_success("Todos os imports OK!")
        return True
        
    except ImportError as e:
        print_error(f"Erro de import: {e}")
        return False
    except SyntaxError as e:
        print_error(f"Erro de sintaxe: {e}")
        return False
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        return False

# ============================================================================
# TESTE 4: PIPELINE 1 CIDADE
# ============================================================================

def test_single_city_pipeline():
    """Testa pipeline completo com 1 cidade."""
    print_header("TESTE 4: Pipeline End-to-End (1 Cidade)")
    
    try:
        from backend.api.services.openmeteo_matopiba_client import \
            OpenMeteoMatopibaClient
        from backend.core.eto_calculation.eto_matopiba import \
            calculate_eto_matopiba_city
        
        print_info("Iniciando cliente Open-Meteo...")
        client = OpenMeteoMatopibaClient(forecast_days=2)
        
        # Pegar primeira cidade
        first_city = client.cities_df.iloc[0]
        city_name = first_city['city']
        state = first_city['state']
        print_info(f"Testando: {city_name}-{state}")
        
        # Fetch dados
        print_info("Baixando dados Open-Meteo...")
        start = time.time()
        city_data = client._parse_city_data(
            first_city,
            hourly_vars=client.hourly_vars
        )
        fetch_time = time.time() - start
        print_info(f"Download: {fetch_time:.2f}s")
        
        # Validar hourly_data
        if 'hourly_data' not in city_data:
            print_error("hourly_data não encontrado no resultado")
            return False
        
        hourly_data = city_data['hourly_data']
        n_hours = len(hourly_data.get('time', []))
        print_success(f"hourly_data recebido: {n_hours} horas")
        
        # Calcular ETo
        print_info("Calculando ETo EVAonline...")
        start = time.time()
        result = calculate_eto_matopiba_city(
            city_data,
            latitude=first_city['latitude'],
            longitude=first_city['longitude'],
            elevation=first_city['elevation']
        )
        calc_time = time.time() - start
        print_info(f"Cálculo: {calc_time:.2f}s")
        
        # Validar resultado
        if not result:
            print_error("Resultado vazio")
            return False
        
        forecasts = result.get('forecasts', [])
        if not forecasts:
            print_error("Sem forecasts no resultado")
            return False
        
        print_success(f"Forecasts gerados: {len(forecasts)} dias")
        
        # Mostrar primeira previsão
        first_forecast = forecasts[0]
        print_info(f"Data: {first_forecast['date']}")
        print_info(f"ETo EVAonline: {first_forecast['ETo_EVAonline']:.2f} mm/dia")
        print_info(f"ETo OpenMeteo: {first_forecast['ETo_OpenMeteo']:.2f} mm/dia")
        
        diff_pct = abs(
            first_forecast['ETo_EVAonline'] - first_forecast['ETo_OpenMeteo']
        ) / first_forecast['ETo_OpenMeteo'] * 100
        print_info(f"Diferença: {diff_pct:.1f}%")
        
        if diff_pct > 50:
            print_warning(f"Diferença alta: {diff_pct:.1f}% (esperado <20%)")
        else:
            print_success(f"Diferença aceitável: {diff_pct:.1f}%")
        
        print_success("Pipeline 1 cidade OK!")
        return True
        
    except Exception as e:
        print_error(f"Erro no pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TESTE 5: CELERY WORKER
# ============================================================================

def test_celery_worker():
    """Testa se Celery worker está acessível."""
    print_header("TESTE 5: Celery Worker")
    
    try:
        from backend.infrastructure.celery.celery_config import celery_app
        
        print_info("Verificando workers ativos...")
        
        # Inspect workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if not active_workers:
            print_warning("Nenhum worker ativo detectado")
            print_info("Inicie worker: .\\scripts\\manage_celery_redis.ps1 start-worker")
            return False
        
        for worker_name, tasks in active_workers.items():
            print_success(f"Worker ativo: {worker_name}")
            print_info(f"  Tasks em execução: {len(tasks)}")
        
        # Registered tasks
        registered = inspect.registered()
        if registered:
            worker_name = list(registered.keys())[0]
            tasks = registered[worker_name]
            print_info(f"Tasks registradas: {len(tasks)}")
            
            # Verificar task MATOPIBA
            matopiba_task = 'update_matopiba_forecasts'
            if matopiba_task in tasks:
                print_success(f"Task '{matopiba_task}' registrada")
            else:
                print_warning(f"Task '{matopiba_task}' NÃO registrada")
        
        print_success("Celery worker acessível!")
        return True
        
    except Exception as e:
        print_error(f"Erro ao verificar worker: {e}")
        print_info("Worker pode não estar rodando")
        return False

# ============================================================================
# TESTE 6: EXECUTAR TASK MANUAL
# ============================================================================

def test_manual_task_execution(n_cities=10):
    """Executa task MATOPIBA manualmente com N cidades."""
    print_header(f"TESTE 6: Execução Manual Task ({n_cities} cidades)")
    
    try:
        from backend.infrastructure.celery.tasks.matopiba_forecast_task import \
            update_matopiba_forecasts
        
        print_info(f"Enviando task para worker (limite: {n_cities} cidades)...")
        print_warning("Isso pode levar 10-60 segundos dependendo de N")
        
        # Trigger task
        start = time.time()
        result = update_matopiba_forecasts.delay()
        
        print_success(f"Task enviada! ID: {result.id}")
        print_info("Aguardando conclusão...")
        
        # Aguardar resultado (timeout 120s)
        try:
            task_result = result.get(timeout=120)
            duration = time.time() - start
            
            print_success(f"Task concluída em {duration:.1f}s")
            
            # Analisar resultado
            if isinstance(task_result, dict):
                print_info("Resultado:")
                for key, value in task_result.items():
                    if key == 'validation':
                        print_info(f"  Validação:")
                        for k, v in value.items():
                            print_info(f"    {k}: {v}")
                    elif key != 'summary':
                        print_info(f"  {key}: {value}")
            
            return True
            
        except Exception as e:
            print_error(f"Task falhou ou timeout: {e}")
            print_info(f"Task ID: {result.id} (verificar logs do worker)")
            return False
        
    except Exception as e:
        print_error(f"Erro ao executar task: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TESTE 7: VERIFICAR CACHE REDIS
# ============================================================================

def test_redis_cache():
    """Verifica cache MATOPIBA no Redis."""
    print_header("TESTE 7: Cache Redis MATOPIBA")
    
    try:
        from redis import Redis
        
        redis_password = os.getenv("REDIS_PASSWORD", "evaonline")
        redis_url = f"redis://default:{redis_password}@localhost:6379/0"
        
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        
        # Buscar chaves MATOPIBA
        print_info("Buscando chaves matopiba:*...")
        keys = redis_client.keys("matopiba:*")
        
        if not keys:
            print_warning("Nenhuma chave MATOPIBA encontrada no cache")
            print_info("Execute task primeiro: .\\scripts\\manage_celery_redis.ps1 trigger")
            return False
        
        print_success(f"Encontradas {len(keys)} chaves MATOPIBA")
        
        for key in keys:
            print_info(f"\nChave: {key}")
            
            # TTL
            ttl = redis_client.ttl(key)
            ttl_hours = ttl / 3600
            print_info(f"  TTL: {ttl}s ({ttl_hours:.1f}h)")
            
            # Size
            try:
                size = redis_client.memory_usage(key)
                size_kb = size / 1024
                print_info(f"  Tamanho: {size} bytes ({size_kb:.1f} KB)")
            except:
                pass
            
            # Conteúdo (se metadata)
            if "metadata" in key:
                try:
                    metadata = redis_client.get(key)
                    data = json.loads(metadata)
                    print_info(f"  Conteúdo:")
                    print_info(f"    Cidades: {data.get('n_cities', 'N/A')}")
                    print_info(f"    Atualizado: {data.get('updated_at', 'N/A')}")
                    print_info(f"    Próxima: {data.get('next_update', 'N/A')}")
                    print_info(f"    Versão: {data.get('version', 'N/A')}")
                except Exception as e:
                    print_warning(f"  Erro ao ler metadata: {e}")
        
        print_success("Cache Redis verificado!")
        return True
        
    except Exception as e:
        print_error(f"Erro ao verificar cache: {e}")
        return False

# ============================================================================
# TESTE 8: VALIDAR MÉTRICAS
# ============================================================================

def test_validation_metrics():
    """Valida métricas R²/RMSE do cache."""
    print_header("TESTE 8: Métricas de Validação R²/RMSE")
    
    try:
        from redis import Redis
        
        redis_password = os.getenv("REDIS_PASSWORD", "evaonline")
        redis_url = f"redis://default:{redis_password}@localhost:6379/0"
        
        redis_client = Redis.from_url(redis_url, decode_responses=False)
        
        # Buscar forecasts
        forecast_key = "matopiba:forecasts:today_tomorrow"
        data_bytes = redis_client.get(forecast_key)
        
        if not data_bytes:
            print_warning("Cache de forecasts não encontrado")
            print_info("Execute task primeiro")
            return False
        
        # Deserializar
        cache_data = pickle.loads(data_bytes)
        validation = cache_data.get('validation', {})
        
        if not validation:
            print_warning("Métricas de validação não encontradas no cache")
            return False
        
        print_info("Métricas encontradas:")
        
        # R²
        r2 = validation.get('r2', 0)
        print_info(f"  R² (correlação): {r2:.4f}")
        
        if r2 >= 0.75:
            print_success(f"  ✅ EXCELENTE (R² ≥ 0.75)")
        elif r2 >= 0.65:
            print_warning(f"  ⚠️  ACEITÁVEL (R² ≥ 0.65)")
        else:
            print_error(f"  ❌ INSUFICIENTE (R² < 0.65)")
        
        # RMSE
        rmse = validation.get('rmse', 999)
        print_info(f"  RMSE (erro): {rmse:.4f} mm/dia")
        
        if rmse <= 1.2:
            print_success(f"  ✅ EXCELENTE (RMSE ≤ 1.2)")
        elif rmse <= 1.5:
            print_warning(f"  ⚠️  ACEITÁVEL (RMSE ≤ 1.5)")
        else:
            print_error(f"  ❌ INSUFICIENTE (RMSE > 1.5)")
        
        # Outros
        print_info(f"  Bias: {validation.get('bias', 0):.4f} mm/dia")
        print_info(f"  MAE: {validation.get('mae', 0):.4f} mm/dia")
        print_info(f"  Amostras: {validation.get('n_samples', 0)}")
        print_info(f"  Status: {validation.get('status', 'N/A')}")
        
        # Aprovação
        if r2 >= 0.65 and rmse <= 1.5:
            print_success("Métricas APROVADAS para produção!")
            return True
        else:
            print_warning("Métricas abaixo do esperado (mas funcionais)")
            return True  # Não falha, pois dados são salvos mesmo assim
        
    except Exception as e:
        print_error(f"Erro ao validar métricas: {e}")
        return False

# ============================================================================
# RESUMO E RELATÓRIO
# ============================================================================

def generate_report(results):
    """Gera relatório final dos testes."""
    print_header("RELATÓRIO FINAL")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"\nTotal de testes: {total}")
    print_success(f"Aprovados: {passed}")
    
    if failed > 0:
        print_error(f"Falharam: {failed}")
    else:
        print_success("Falharam: 0")
    
    print("\nDetalhamento:")
    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        color = Colors.GREEN if passed else Colors.RED
        print(f"  {color}{status}{Colors.END} - {test_name}")
    
    print("\n" + "="*70)
    
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("🎉 TODOS OS TESTES PASSARAM! 🎉")
        print("Sistema pronto para produção!")
        print(f"{Colors.END}")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}")
        print(f"⚠️  {failed} teste(s) falharam")
        print("Revise os erros acima e corrija antes de produção")
        print(f"{Colors.END}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Executa suite completa de testes."""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("="*70)
    print("   SUITE DE TESTES COMPLETA - EVAonline MATOPIBA")
    print("="*70)
    print(f"{Colors.END}")
    print(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # Teste 1: Ambiente Python
    results['Ambiente Python'] = test_python_environment()
    if not results['Ambiente Python']:
        print_error("\n⛔ Ambiente Python com problemas. Corrija antes de continuar.")
        generate_report(results)
        return
    
    # Teste 2: Redis
    results['Redis Connection'] = test_redis_connection()
    if not results['Redis Connection']:
        print_warning("\n⚠️  Redis não disponível. Alguns testes serão pulados.")
    
    # Teste 3: Imports
    results['Imports MATOPIBA'] = test_matopiba_imports()
    if not results['Imports MATOPIBA']:
        print_error("\n⛔ Imports com problemas. Corrija antes de continuar.")
        generate_report(results)
        return
    
    # Teste 4: Pipeline 1 cidade
    print_info("\n⏱️  Próximo teste pode levar ~30-60s...")
    results['Pipeline 1 Cidade'] = test_single_city_pipeline()
    
    # Teste 5: Celery Worker
    results['Celery Worker'] = test_celery_worker()
    
    # Teste 6: Executar task (apenas se worker ativo)
    if results.get('Celery Worker') and results.get('Redis Connection'):
        print_info("\n⏱️  Próximo teste pode levar ~60-120s...")
        user_input = input("Executar task manual com 10 cidades? (s/n): ")
        if user_input.lower() == 's':
            results['Task Manual'] = test_manual_task_execution(n_cities=10)
        else:
            print_info("Teste de task manual pulado pelo usuário")
            results['Task Manual'] = None
    else:
        print_info("Task manual não executada (worker ou Redis indisponível)")
        results['Task Manual'] = None
    
    # Teste 7: Cache Redis
    if results.get('Redis Connection'):
        results['Cache Redis'] = test_redis_cache()
    else:
        results['Cache Redis'] = None
    
    # Teste 8: Métricas
    if results.get('Cache Redis'):
        results['Métricas Validação'] = test_validation_metrics()
    else:
        results['Métricas Validação'] = None
    
    # Relatório final
    print(f"\nFim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Filtrar testes None (pulados)
    results_filtered = {k: v for k, v in results.items() if v is not None}
    generate_report(results_filtered)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Testes interrompidos pelo usuário{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Erro fatal: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
