# 🚀 Quick Start - Testes de Integração EVAonline

Este guia rápido mostra como executar os testes de integração em 5 minutos.

## ⚡ Opção 1: Teste Rápido (Apenas Conectividade)

```powershell
# 1. Ativar ambiente virtual
.\.venv\Scripts\activate

# 2. Subir Redis e PostgreSQL (Docker)
docker-compose up -d redis postgres

# 3. Aguardar 10 segundos
timeout /t 10

# 4. Executar testes rápidos
python tests/integration/run_integration_tests.py --quick
```

**Tempo**: ~30 segundos  
**Testa**: Redis PING, PostgreSQL connection, PostGIS extension

---

## 🎯 Opção 2: Testes Completos (Recomendado)

```powershell
# 1. Ativar ambiente virtual
.\.venv\Scripts\activate

# 2. Subir toda a infraestrutura
docker-compose up -d

# 3. Aguardar 30 segundos (serviços ficarem prontos)
timeout /t 30

# 4. Executar todos os testes
pytest tests/integration/test_infrastructure_integration.py -v
```

**Tempo**: ~2-3 minutos  
**Testa**: Redis, PostgreSQL, OpenMeteo API, Geospatial data, Performance

---

## 🐳 Opção 3: Usando Apenas Docker

```powershell
# 1. Subir stack completa
docker-compose up -d

# 2. Executar testes dentro do container
docker-compose exec api pytest tests/integration/test_infrastructure_integration.py -v
```

---

## ✅ Resultado Esperado

```
========================= test session starts =========================
collected 20 items

test_infrastructure_integration.py::TestConnectivity::test_redis_ping PASSED
test_infrastructure_integration.py::TestConnectivity::test_postgres_connection PASSED
test_infrastructure_integration.py::TestRedisCache::test_set_get_string PASSED
test_infrastructure_integration.py::TestOpenMeteoIntegration::test_get_elevation_with_cache PASSED
...

========================= 20 passed in 15.34s =========================

✅ TODOS OS TESTES PASSARAM!
```

---

## ❌ Problemas Comuns

### Redis não conecta
```powershell
# Verificar se está rodando
docker ps | findstr redis

# Reiniciar
docker-compose restart redis
```

### PostgreSQL não conecta
```powershell
# Verificar se está rodando
docker ps | findstr postgres

# Ver logs
docker-compose logs postgres
```

### Sem Docker?
Use instalações locais:
- PostgreSQL: https://www.postgresql.org/download/windows/
- Redis: https://redis.io/docs/getting-started/installation/install-redis-on-windows/

---

## 📊 Comandos Úteis

```powershell
# Apenas testes de Redis
pytest tests/integration/test_infrastructure_integration.py::TestRedisCache -v

# Apenas testes de PostgreSQL
pytest tests/integration/test_infrastructure_integration.py::TestConnectivity -v

# Apenas testes de Performance
pytest tests/integration/test_infrastructure_integration.py::TestPerformance -v

# Com output detalhado
pytest tests/integration/test_infrastructure_integration.py -v -s

# Gerar relatório final
pytest tests/integration/test_infrastructure_integration.py -v -k "generate_integration_report"
```

---

## 🎓 Próximos Passos

Após os testes passarem:

1. ✅ **Infraestrutura validada** - Todos os serviços funcionando
2. ✅ **Cache otimizado** - Redis acelerando 99% das requisições
3. ✅ **Dados geoespaciais carregados** - 27 UFs + 337 cidades MATOPIBA
4. ✅ **APIs integradas** - OpenMeteo funcionando com cache

**Agora você pode**:
- Testar a aplicação Dash: `python frontend/app.py`
- Testar a API FastAPI: `uvicorn backend.api.main:app --reload`
- Fazer commit das mudanças: `git add . && git commit -m "feat: Add integration tests"`

---

## 📚 Documentação Completa

Ver: `tests/integration/README.md`
