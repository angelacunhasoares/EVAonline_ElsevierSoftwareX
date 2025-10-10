"""
Teste de conexão e operações básicas Redis.

Este script verifica:
1. Conexão com servidor Redis
2. Operações SET/GET/DELETE
3. Operações com TTL
4. Operações com tipos complexos (JSON, pickle)
"""

import json
import os
import pickle
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar backend ao path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from redis import Redis
from redis.exceptions import AuthenticationError, ConnectionError


def test_redis_connection():
    """Testa conexão básica com Redis."""
    print("\n" + "="*60)
    print("🔍 TESTE 1: Conexão Redis")
    print("="*60)
    
    # Obter configuração
    redis_password = os.getenv("REDIS_PASSWORD", "evaonline")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    redis_url = f"redis://default:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
    
    print(f"\n📍 Configuração:")
    print(f"   Host: {redis_host}")
    print(f"   Port: {redis_port}")
    print(f"   DB: {redis_db}")
    print(f"   Password: {'*' * len(redis_password)}")
    
    try:
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        response = redis_client.ping()
        
        if response:
            print(f"\n✅ Redis conectado com sucesso!")
            
            # Info do servidor
            info = redis_client.info("server")
            print(f"\n📊 Informações do Servidor:")
            print(f"   Versão Redis: {info.get('redis_version', 'N/A')}")
            print(f"   Modo: {info.get('redis_mode', 'N/A')}")
            print(f"   Uptime: {info.get('uptime_in_seconds', 0)} segundos")
            
            return redis_client
        else:
            print(f"\n❌ Erro: Redis não respondeu ao PING")
            return None
            
    except AuthenticationError:
        print(f"\n❌ Erro de autenticação: verifique REDIS_PASSWORD")
        return None
    except ConnectionError as e:
        print(f"\n❌ Erro de conexão: {e}")
        print(f"\n💡 Dicas:")
        print(f"   1. Verificar se Redis está rodando: docker ps | Select-String redis")
        print(f"   2. Iniciar Redis: docker start evaonline-redis")
        print(f"   3. Criar Redis: docker run -d --name evaonline-redis -p 6379:6379 redis:7-alpine")
        return None
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return None


def test_basic_operations(redis_client):
    """Testa operações básicas SET/GET/DELETE."""
    if not redis_client:
        return False
        
    print("\n" + "="*60)
    print("🔍 TESTE 2: Operações Básicas (SET/GET/DELETE)")
    print("="*60)
    
    try:
        # SET
        test_key = "test:basic:key"
        test_value = "test_value_123"
        redis_client.set(test_key, test_value, ex=60)
        print(f"\n✅ SET: {test_key} = {test_value} (TTL 60s)")
        
        # GET
        retrieved = redis_client.get(test_key)
        if retrieved == test_value:
            print(f"✅ GET: {test_key} = {retrieved}")
        else:
            print(f"❌ GET falhou: esperado {test_value}, obtido {retrieved}")
            return False
        
        # TTL
        ttl = redis_client.ttl(test_key)
        print(f"✅ TTL: {test_key} expira em {ttl}s")
        
        # DELETE
        redis_client.delete(test_key)
        deleted = redis_client.get(test_key)
        if deleted is None:
            print(f"✅ DELETE: {test_key} removido com sucesso")
        else:
            print(f"❌ DELETE falhou: chave ainda existe")
            return False
        
        print(f"\n✅ Todos os testes básicos passaram!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro em operações básicas: {e}")
        return False


def test_json_operations(redis_client):
    """Testa operações com JSON."""
    if not redis_client:
        return False
        
    print("\n" + "="*60)
    print("🔍 TESTE 3: Operações com JSON")
    print("="*60)
    
    try:
        # Dados JSON complexos
        test_key = "test:json:data"
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "forecasts": [
                {"city": "Brasília", "eto": 5.2, "temp": 28.5},
                {"city": "Palmas", "eto": 6.1, "temp": 32.0},
            ],
            "metadata": {
                "version": "1.0",
                "source": "test",
                "count": 2
            }
        }
        
        # SET JSON
        json_str = json.dumps(test_data, ensure_ascii=False)
        redis_client.set(test_key, json_str, ex=120)
        print(f"\n✅ SET JSON: {len(json_str)} bytes")
        
        # GET JSON
        retrieved_str = redis_client.get(test_key)
        retrieved_data = json.loads(retrieved_str)
        
        if retrieved_data == test_data:
            print(f"✅ GET JSON: dados recuperados corretamente")
            print(f"   Cidades: {len(retrieved_data['forecasts'])}")
            print(f"   Timestamp: {retrieved_data['timestamp']}")
        else:
            print(f"❌ GET JSON falhou: dados corrompidos")
            return False
        
        # Cleanup
        redis_client.delete(test_key)
        print(f"✅ Cleanup: chave removida")
        
        print(f"\n✅ Todos os testes JSON passaram!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro em operações JSON: {e}")
        return False


def test_pickle_operations(redis_client):
    """Testa operações com pickle (como MATOPIBA usa)."""
    if not redis_client:
        return False
        
    print("\n" + "="*60)
    print("🔍 TESTE 4: Operações com Pickle")
    print("="*60)
    
    try:
        # Dados complexos Python
        test_key = "test:pickle:data"
        test_data = {
            "forecasts": {
                "today": [5.2, 6.1, 4.8],
                "tomorrow": [5.5, 6.3, 5.0]
            },
            "validation": {
                "r2": 0.83,
                "rmse": 0.59,
                "bias": 0.44
            },
            "timestamp": datetime.now()
        }
        
        # SET Pickle (sem decode_responses)
        redis_raw = redis_client.client()  # Cliente sem decode
        pickled = pickle.dumps(test_data)
        redis_raw.setex(test_key, 120, pickled)
        print(f"\n✅ SET Pickle: {len(pickled)} bytes")
        
        # GET Pickle
        retrieved_bytes = redis_raw.get(test_key)
        retrieved_data = pickle.loads(retrieved_bytes)
        
        if retrieved_data["validation"]["r2"] == 0.83:
            print(f"✅ GET Pickle: dados recuperados corretamente")
            print(f"   R² = {retrieved_data['validation']['r2']}")
            print(f"   RMSE = {retrieved_data['validation']['rmse']}")
            print(f"   Timestamp: {retrieved_data['timestamp']}")
        else:
            print(f"❌ GET Pickle falhou: dados corrompidos")
            return False
        
        # Cleanup
        redis_client.delete(test_key)
        print(f"✅ Cleanup: chave removida")
        
        print(f"\n✅ Todos os testes Pickle passaram!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro em operações Pickle: {e}")
        return False


def test_matopiba_keys(redis_client):
    """Testa chaves específicas do MATOPIBA."""
    if not redis_client:
        return False
        
    print("\n" + "="*60)
    print("🔍 TESTE 5: Chaves MATOPIBA")
    print("="*60)
    
    try:
        # Buscar chaves MATOPIBA existentes
        matopiba_keys = redis_client.keys("matopiba:*")
        
        if matopiba_keys:
            print(f"\n📦 Encontradas {len(matopiba_keys)} chaves MATOPIBA:")
            for key in matopiba_keys:
                ttl = redis_client.ttl(key)
                size = redis_client.memory_usage(key)
                print(f"   • {key}")
                print(f"     TTL: {ttl}s ({ttl/3600:.1f}h)")
                print(f"     Size: {size} bytes")
                
                # Se for metadata, mostrar conteúdo
                if "metadata" in key:
                    try:
                        metadata = redis_client.get(key)
                        data = json.loads(metadata)
                        print(f"     Conteúdo:")
                        print(f"       - Cidades: {data.get('n_cities', 'N/A')}")
                        print(f"       - Última atualização: {data.get('timestamp', 'N/A')}")
                        print(f"       - Versão: {data.get('version', 'N/A')}")
                    except:
                        print(f"     Conteúdo: (não JSON)")
        else:
            print(f"\n⚠️  Nenhuma chave MATOPIBA encontrada")
            print(f"   Isso é normal se a task ainda não foi executada")
        
        print(f"\n✅ Teste chaves MATOPIBA concluído!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar chaves MATOPIBA: {e}")
        return False


def test_database_stats(redis_client):
    """Mostra estatísticas do banco de dados."""
    if not redis_client:
        return False
        
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS DO BANCO DE DADOS")
    print("="*60)
    
    try:
        # Info geral
        info = redis_client.info("stats")
        memory = redis_client.info("memory")
        
        print(f"\n💾 Memória:")
        print(f"   Usada: {memory.get('used_memory_human', 'N/A')}")
        print(f"   Pico: {memory.get('used_memory_peak_human', 'N/A')}")
        
        print(f"\n📈 Estatísticas:")
        print(f"   Total de chaves: {redis_client.dbsize()}")
        print(f"   Conexões recebidas: {info.get('total_connections_received', 'N/A')}")
        print(f"   Comandos processados: {info.get('total_commands_processed', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao obter estatísticas: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("🧪 TESTE DE INTEGRAÇÃO REDIS - EVAonline MATOPIBA")
    print("="*60)
    print(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Teste 1: Conexão
    redis_client = test_redis_connection()
    if not redis_client:
        print("\n❌ Falha na conexão. Abortando testes.")
        sys.exit(1)
    
    # Teste 2: Operações básicas
    success = test_basic_operations(redis_client)
    if not success:
        print("\n⚠️  Falha em operações básicas")
    
    # Teste 3: JSON
    success = test_json_operations(redis_client)
    if not success:
        print("\n⚠️  Falha em operações JSON")
    
    # Teste 4: Pickle
    success = test_pickle_operations(redis_client)
    if not success:
        print("\n⚠️  Falha em operações Pickle")
    
    # Teste 5: Chaves MATOPIBA
    test_matopiba_keys(redis_client)
    
    # Estatísticas finais
    test_database_stats(redis_client)
    
    print("\n" + "="*60)
    print("✅ TODOS OS TESTES CONCLUÍDOS!")
    print("="*60)
    print(f"Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    redis_client.close()


if __name__ == "__main__":
    main()
