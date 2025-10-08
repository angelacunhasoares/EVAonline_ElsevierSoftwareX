# Testes de Integração - EVAonline Infrastructure

Este diretório contém testes de integração completa que validam a comunicação entre todos os componentes da infraestrutura do projeto EVAonline.

## 📋 Componentes Testados

### 1. **PostgreSQL + PostGIS**
- ✅ Conectividade com banco de dados
- ✅ Extensão PostGIS instalada e funcionando
- ✅ Operações CRUD básicas
- ✅ Verificação de schema e tabelas

### 2. **Redis Cache**
- ✅ Conectividade com Redis
- ✅ Operações SET/GET
- ✅ TTL (Time To Live) e expiração
- ✅ Cache de dados de elevação
- ✅ Métricas de cache hit/miss

### 3. **OpenMeteo API**
- ✅ Busca de elevação com validação
- ✅ Cache Redis integrado
- ✅ Performance: API vs Cache (99% improvement)
- ✅ Validação de coordenadas
- ✅ Tratamento de erros

### 4. **Dados Geoespaciais**
- ✅ GeoJSON do Brasil (27 UFs)
- ✅ GeoJSON do MATOPIBA
- ✅ CSV de 337 cidades MATOPIBA
- ✅ Validação de coordenadas

### 5. **Integração End-to-End**
- ✅ Workflow completo: Clique no mapa → Elevação → Cache
- ✅ Processamento em lote (múltiplas localizações)
- ✅ Performance benchmarking

## 🚀 Como Executar

### Pré-requisitos

1. **PostgreSQL** rodando (Docker ou instalação local):
   ```powershell
   # Via Docker Compose
   docker-compose up -d postgres
   
   # Ou via instalação local (Windows)
   # PostgreSQL deve estar rodando na porta 5432
   ```

2. **Redis** rodando (Docker ou instalação local):
   ```powershell
   # Via Docker Compose
   docker-compose up -d redis
   
   # Ou via instalação local (Windows)
   # Redis deve estar rodando na porta 6379
   ```

3. **Ambiente Python configurado**:
   ```powershell
   .\.venv\Scripts\activate
   ```

4. **Arquivo `.env` configurado** (copiar de `.env.example`)

### Executar Todos os Testes

```powershell
# Ativar ambiente virtual
.\.venv\Scripts\activate

# Executar testes de integração
pytest tests/integration/test_infrastructure_integration.py -v --tb=short

# Com relatório detalhado
pytest tests/integration/test_infrastructure_integration.py -v --tb=short -s
```

### Executar Testes Específicos

```powershell
# Apenas testes de conectividade
pytest tests/integration/test_infrastructure_integration.py::TestConnectivity -v

# Apenas testes de Redis
pytest tests/integration/test_infrastructure_integration.py::TestRedisCache -v

# Apenas testes de OpenMeteo
pytest tests/integration/test_infrastructure_integration.py::TestOpenMeteoIntegration -v

# Apenas testes geoespaciais
pytest tests/integration/test_infrastructure_integration.py::TestGeospatialData -v

# Apenas testes de integração completa
pytest tests/integration/test_infrastructure_integration.py::TestFullIntegration -v

# Apenas testes de performance
pytest tests/integration/test_infrastructure_integration.py::TestPerformance -v
```

### Executar com Docker Compose (Ambiente Completo)

```powershell
# Subir todos os serviços
docker-compose up -d

# Aguardar serviços ficarem prontos (30 segundos)
timeout /t 30

# Executar testes no container
docker-compose exec api pytest tests/integration/test_infrastructure_integration.py -v

# Ou executar localmente apontando para containers
pytest tests/integration/test_infrastructure_integration.py -v
```

## 📊 Exemplo de Saída

```
========================= test session starts =========================
tests/integration/test_infrastructure_integration.py::TestConnectivity::test_redis_ping PASSED [  5%]
tests/integration/test_infrastructure_integration.py::TestConnectivity::test_postgres_connection PASSED [ 10%]
tests/integration/test_infrastructure_integration.py::TestConnectivity::test_postgres_postgis_extension PASSED [ 15%]

tests/integration/test_infrastructure_integration.py::TestRedisCache::test_set_get_string PASSED [ 20%]
tests/integration/test_infrastructure_integration.py::TestRedisCache::test_cache_elevation_data PASSED [ 25%]

tests/integration/test_infrastructure_integration.py::TestOpenMeteoIntegration::test_get_elevation_with_cache PASSED [ 30%]
   🌐 API Call (MISS): 125.43ms - Elevation: 542.5m
   ⚡ Cache Hit (HIT): 1.23ms - Elevation: 542.5m
   ✅ Cache Performance: 99.0% mais rápido

tests/integration/test_infrastructure_integration.py::TestGeospatialData::test_load_brasil_geojson PASSED [ 40%]
   ✅ Brasil GeoJSON: 27 UFs carregadas

========================= 20 passed in 15.34s =========================

📊 RELATÓRIO DE INTEGRAÇÃO - EVAonline
======================================================================
🔴 REDIS:
   Versão: 7.2.4
   Uptime: 3600 segundos
   Conexões: 1
   Memória usada: 1.5M
   Keys: 5

🐘 POSTGRESQL:
   PostgreSQL 15.3 on x86_64-pc-linux-musl
   PostGIS: 3.4.0
   Tabelas: 12

🗺️  ARQUIVOS GEOESPACIAIS:
   ✅ brasil: BR_UF_2024.geojson (2456.3 KB)
   ✅ matopiba: Matopiba_Perimetro.geojson (89.7 KB)
   ✅ cities: CITIES_MATOPIBA_337.csv (15.2 KB)

✅ INTEGRAÇÃO COMPLETA: TODOS OS SISTEMAS OPERACIONAIS
======================================================================
```

## 🐛 Troubleshooting

### Redis não conecta

**Problema**: `redis.ConnectionError: Error connecting to Redis`

**Soluções**:
1. Verificar se Redis está rodando:
   ```powershell
   # Docker
   docker ps | findstr redis
   
   # Windows Service
   sc query Redis
   ```

2. Verificar senha no `.env`:
   ```bash
   REDIS_PASSWORD=evaonline
   ```

3. Testar conexão manual:
   ```powershell
   redis-cli -h localhost -p 6379 -a evaonline ping
   ```

### PostgreSQL não conecta

**Problema**: `sqlalchemy.exc.OperationalError: could not connect`

**Soluções**:
1. Verificar se PostgreSQL está rodando:
   ```powershell
   # Docker
   docker ps | findstr postgres
   
   # Windows Service
   sc query postgresql-x64-15
   ```

2. Verificar configurações no `.env`:
   ```bash
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=evaonline
   ```

3. Testar conexão via psql:
   ```powershell
   psql -h localhost -U postgres -d evaonline
   ```

### Arquivos geoespaciais não encontrados

**Problema**: `AssertionError: Arquivo não encontrado`

**Solução**: Verificar estrutura de diretórios:
```
EVAonline_ElsevierSoftwareX/
├── data/
│   ├── geojson/
│   │   ├── BR_UF_2024.geojson
│   │   └── Matopiba_Perimetro.geojson
│   └── csv/
│       └── CITIES_MATOPIBA_337.csv
└── tests/
    └── integration/
        └── test_infrastructure_integration.py
```

### API OpenMeteo timeout

**Problema**: `requests.exceptions.Timeout`

**Soluções**:
1. Verificar conexão com internet
2. Aumentar timeout no código (padrão: 10s)
3. Verificar se API está disponível: https://open-meteo.com/

## 📈 Métricas de Performance

Os testes medem automaticamente:

- **Cache Hit Latency**: ~1-5ms (Redis)
- **Cache Miss Latency**: ~100-200ms (API externa)
- **Performance Improvement**: ~99% (Cache vs API)
- **Redis Throughput**: ~10,000 ops/sec (local)
- **PostgreSQL Connection**: ~10-50ms (primeira conexão)

## 🔧 Configuração de Ambientes

### Ambiente Local (Desenvolvimento)

```bash
# .env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Ambiente Docker (Produção)

```bash
# .env
POSTGRES_HOST=postgres  # Nome do container
POSTGRES_PORT=5432
REDIS_HOST=redis  # Nome do container
REDIS_PORT=6379
```

### Ambiente CI/CD (GitHub Actions)

```yaml
# .github/workflows/tests.yml
services:
  postgres:
    image: postgis/postgis:15-3.4-alpine
  redis:
    image: redis:7-alpine
```

## 📝 Notas Importantes

1. **Cache Warming**: Primeira execução é mais lenta (cache miss)
2. **Cleanup Automático**: Testes limpam dados criados automaticamente
3. **Fixtures Reutilizáveis**: `session` scope para conexões (performance)
4. **Múltiplos Ambientes**: Testes tentam conectar em Docker → Local → CI/CD
5. **Skip Automático**: Se serviço não disponível, teste é pulado (não falha)

## 🎯 Próximos Passos

- [ ] Adicionar testes de Celery workers
- [ ] Adicionar testes de WebSocket (API)
- [ ] Adicionar testes de FastAPI endpoints
- [ ] Adicionar testes de frontend Dash
- [ ] Integração com GitHub Actions CI/CD
- [ ] Testes de carga (stress testing)
- [ ] Monitoramento com Prometheus/Grafana

## 📚 Referências

- [PostgreSQL + PostGIS](https://postgis.net/)
- [Redis Documentation](https://redis.io/docs/)
- [OpenMeteo API](https://open-meteo.com/en/docs)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Compose](https://docs.docker.com/compose/)
