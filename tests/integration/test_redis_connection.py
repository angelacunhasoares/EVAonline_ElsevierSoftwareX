"""
Teste de conexão Redis com diferentes formatos de URL.
"""
import redis

print("\n" + "="*60)
print("TESTE DE CONEXÃO REDIS")
print("="*60 + "\n")

# Teste 1: URL com senha no formato :password@
print("Teste 1: redis://:evaonline@localhost:6379/0")
try:
    client1 = redis.from_url("redis://:evaonline@localhost:6379/0")
    client1.ping()
    print("✅ SUCESSO!\n")
except Exception as e:
    print(f"❌ ERRO: {e}\n")

# Teste 2: Conexão direta com password parameter
print("Teste 2: Redis(host='localhost', port=6379, db=0, password='evaonline')")
try:
    client2 = redis.Redis(host='localhost', port=6379, db=0, password='evaonline')
    client2.ping()
    print("✅ SUCESSO!\n")
except Exception as e:
    print(f"❌ ERRO: {e}\n")

# Teste 3: URL com usuário default:password@
print("Teste 3: redis://default:evaonline@localhost:6379/0")
try:
    client3 = redis.from_url("redis://default:evaonline@localhost:6379/0")
    client3.ping()
    print("✅ SUCESSO!\n")
except Exception as e:
    print(f"❌ ERRO: {e}\n")

# Teste 4: URL sem senha (deve falhar)
print("Teste 4: redis://localhost:6379/0")
try:
    client4 = redis.from_url("redis://localhost:6379/0")
    client4.ping()
    print("✅ SUCESSO!\n")
except Exception as e:
    print(f"❌ ERRO: {e}\n")

print("="*60)
