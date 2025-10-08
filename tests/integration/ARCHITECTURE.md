# 📊 Arquitetura e Ferramentas - EVAonline Project

## 🏗️ Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     EVAonline Application                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Frontend   │         │   Backend    │                 │
│  │   (Dash)     │◄───────►│   (FastAPI)  │                 │
│  │   :8050      │         │   :8000      │                 │
│  └──────────────┘         └──────────────┘                 │
│         │                         │                         │
│         │                         │                         │
│         ▼                         ▼                         │
│  ┌──────────────────────────────────────────────┐          │
│  │        Map Results & Data Processing         │          │
│  │   (backend/core/map_results/map_results.py)  │          │
│  └──────────────────────────────────────────────┘          │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │  Redis  │    │PostgreSQL│    │ OpenMeteo│
    │  Cache  │    │ +PostGIS │    │   API    │
    │  :6379  │    │  :5432   │    │ (HTTP)   │
    └─────────┘    └──────────┘    └──────────┘
          │               │               │
          └───────────────┴───────────────┘
                  Infrastructure
```

## 🛠️ Stack Tecnológico

### Frontend
- **Dash 2.10+**: Framework web para Python
- **Plotly 5.15+**: Visualizações interativas
- **Dash Leaflet 1.0+**: Mapas interativos (OpenStreetMap)
- **Dash Bootstrap Components**: UI responsiva

### Backend
- **FastAPI**: API REST moderna e assíncrona
- **SQLAlchemy 2.0+**: ORM para PostgreSQL
- **Celery**: Processamento assíncrono de tarefas
- **Redis**: Cache e message broker
- **Alembic**: Migrações de banco de dados

### Banco de Dados
- **PostgreSQL 15**: Banco de dados relacional
- **PostGIS 3.4**: Extensão geoespacial
- **psycopg2**: Driver Python para PostgreSQL

### Cache & Message Queue
- **Redis 7**: Cache in-memory e broker
- **redis-py**: Cliente Python para Redis

### APIs Externas
- **OpenMeteo API**: Dados meteorológicos
- **Elevation API**: Dados de altitude com cache de 24h

### Dados Geoespaciais
- **GeoPandas**: Manipulação de dados geoespaciais
- **Shapely**: Operações geométricas
- **PyProj**: Projeções cartográficas

### DevOps
- **Docker**: Containerização
- **Docker Compose**: Orquestração de containers
- **Nginx**: Reverse proxy (produção)
- **Prometheus**: Métricas
- **Grafana**: Dashboards de monitoramento

### Testing
- **pytest**: Framework de testes
- **pytest-cov**: Coverage de testes
- **unittest.mock**: Mocks para testes

## 📁 Estrutura do Projeto

```
EVAonline_ElsevierSoftwareX/
│
├── frontend/                    # Aplicação Dash
│   ├── app.py                  # Aplicação principal
│   ├── pages/                  # Páginas da aplicação
│   │   ├── home.py            # Página inicial (mapas)
│   │   ├── dash_eto.py        # Calculadora ETo
│   │   ├── about.py           # Sobre o projeto
│   │   └── documentation.py   # Documentação
│   ├── components/            # Componentes reutilizáveis
│   └── tests/                 # Testes do frontend
│
├── backend/                    # Backend FastAPI
│   ├── api/                   # API REST
│   │   ├── main.py           # Aplicação FastAPI
│   │   ├── routes/           # Endpoints da API
│   │   ├── services/         # Lógica de negócio
│   │   │   └── openmeteo.py  # Cliente OpenMeteo + Cache
│   │   └── middleware/       # Middlewares
│   │
│   ├── core/                  # Lógica principal
│   │   ├── map_results/      # Geração de mapas
│   │   │   └── map_results.py  # Mapas MATOPIBA e Mundo
│   │   ├── eto_calculation/  # Cálculos de evapotranspiração
│   │   └── data_processing/  # Processamento de dados
│   │
│   ├── database/             # Configuração do banco
│   │   ├── connection.py     # Conexão PostgreSQL
│   │   ├── models/           # Modelos SQLAlchemy
│   │   └── migrations/       # Migrações Alembic
│   │
│   ├── infrastructure/       # Infraestrutura
│   │   ├── cache/           # Gerenciador de cache
│   │   │   └── redis_manager.py
│   │   └── celery/          # Configuração Celery
│   │
│   └── tests/               # Testes do backend
│       └── conftest.py      # Fixtures compartilhadas
│
├── config/                   # Configurações
│   ├── settings/            # Settings da aplicação
│   │   └── app_settings.py  # Configurações principais
│   └── translations/        # i18n
│
├── data/                    # Dados geoespaciais
│   ├── geojson/            # Arquivos GeoJSON
│   │   ├── BR_UF_2024.geojson          # Brasil (27 UFs)
│   │   └── Matopiba_Perimetro.geojson  # MATOPIBA
│   ├── csv/                # Arquivos CSV
│   │   └── CITIES_MATOPIBA_337.csv     # 337 cidades
│   └── shapefile/          # Shapefiles (opcional)
│
├── tests/                   # Testes globais
│   ├── integration/         # 🆕 Testes de integração
│   │   ├── test_infrastructure_integration.py  # Testes completos
│   │   ├── README.md                          # Documentação
│   │   ├── QUICKSTART.md                      # Guia rápido
│   │   ├── pytest.ini                         # Config pytest
│   │   ├── run_integration_tests.py           # Runner Python
│   │   └── run_tests.ps1                      # Runner PowerShell
│   └── ...                  # Outros testes
│
├── docker/                  # Configurações Docker
├── monitoring/              # Prometheus/Grafana
├── logs/                    # Logs da aplicação
├── scripts/                 # Scripts utilitários
│
├── docker-compose.yml       # Orquestração Docker
├── Dockerfile              # Imagem Docker
├── requirements.txt        # Dependências Python
├── .env.example           # Variáveis de ambiente
└── README.md              # Documentação principal
```

## 🔧 Ferramentas Instaladas (Windows)

### Confirmadas pelo Usuário:
- ✅ **Docker Desktop**: Containerização
- ✅ **PostgreSQL**: Banco de dados
- ✅ **Redis**: Cache in-memory
- ✅ **pgAdmin**: GUI para PostgreSQL
- ✅ **VS Code**: IDE principal
- ✅ **Python 3.10+**: Linguagem principal
- ✅ **Git**: Controle de versão

### Extensões VS Code:
- Python
- Docker
- PostgreSQL (provavelmente)
- GitLens (recomendado)
- Pylance (análise de código)

## 🚀 Workflows de Desenvolvimento

### 1. Desenvolvimento Local (Sem Docker)
```powershell
# Ativar ambiente virtual
.\.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Iniciar Redis (Windows Service ou WSL)
redis-server

# Iniciar PostgreSQL (Windows Service)
# (já deve estar rodando)

# Executar aplicação
python frontend/app.py
```

### 2. Desenvolvimento com Docker
```powershell
# Subir todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

### 3. Testes de Integração (🆕)
```powershell
# Quick test (30s)
.\tests\integration\run_tests.ps1 -Quick

# Full test (2-3 min)
.\tests\integration\run_tests.ps1 -Full

# Com serviços Docker
.\tests\integration\run_tests.ps1 -StartServices
```

## 📊 Fluxo de Dados

### Workflow: Clique no Mapa → Elevação

```
1. Usuário clica no mapa (frontend/pages/home.py)
   ↓
2. Coordenadas (lat, long) capturadas
   ↓
3. Callback Dash chama get_elevation() (frontend/app.py)
   ↓
4. get_elevation() chama get_openmeteo_elevation() (backend/api/services/openmeteo.py)
   ↓
5. Verificar cache Redis (chave: "elevation:{lat}:{long}")
   │
   ├─→ Cache HIT (99% dos casos)
   │   └─→ Retornar elevação em ~1-5ms
   │
   └─→ Cache MISS (primeira vez)
       └─→ Chamar API OpenMeteo (~100-200ms)
           └─→ Salvar no Redis (TTL: 24h)
           └─→ Retornar elevação
   ↓
6. Exibir no popup do mapa
```

### Workflow: Carregar Mapa MATOPIBA

```
1. Usuário acessa tab "MATOPIBA, Brasil"
   ↓
2. render_tab_content() callback (frontend/app.py)
   ↓
3. Chama create_matopiba_real_map() (backend/core/map_results/map_results.py)
   ↓
4. Carrega dados geoespaciais (com @lru_cache):
   - data/geojson/BR_UF_2024.geojson (27 UFs)
   - data/geojson/Matopiba_Perimetro.geojson (contorno)
   - data/csv/CITIES_MATOPIBA_337.csv (337 cidades)
   ↓
5. Gera layout Dash com dash_leaflet
   ↓
6. Renderiza mapa no browser
```

## 🔐 Segurança e Boas Práticas

### Variáveis de Ambiente (.env)
```bash
# Nunca commitar .env no Git!
# Usar .env.example como template

POSTGRES_PASSWORD=senha_forte_aqui
REDIS_PASSWORD=senha_forte_aqui
SECRET_KEY=chave_secreta_unica
```

### Cache Strategy
- **Elevação**: 24h TTL (dados não mudam)
- **Dados meteorológicos**: 1h TTL (atualização frequente)
- **Cálculos ETo**: Session-based (usuário específico)

### Performance
- **@lru_cache**: Arquivos geoespaciais em memória
- **Redis**: Cache distribuído para APIs
- **Connection pooling**: PostgreSQL (pool_size=5)
- **Lazy loading**: Dados carregados sob demanda

## 📈 Métricas e Monitoramento

### Prometheus Metrics (backend/api/main.py)
- `cache_hits`: Contagem de cache hits
- `cache_misses`: Contagem de cache misses
- `popular_data_accesses`: Dados mais acessados
- `api_request_duration`: Latência de APIs

### Logs (loguru)
```python
logger.info("Operação bem-sucedida")
logger.warning("Aviso de cache miss")
logger.error("Erro ao conectar ao Redis")
```

## 🎯 Próximos Passos

1. ✅ **Testes de Integração** (COMPLETO!)
   - Redis + PostgreSQL + OpenMeteo
   - Performance benchmarking
   - Validação de dados geoespaciais

2. 🔄 **CI/CD** (Próximo)
   - GitHub Actions
   - Testes automáticos em PRs
   - Deploy automático

3. 📊 **Monitoramento** (Futuro)
   - Grafana dashboards
   - Alertas de performance
   - Logs centralizados

4. 🚀 **Produção** (Futuro)
   - Nginx reverse proxy
   - SSL/HTTPS
   - Load balancing

## 📚 Referências Técnicas

- **Dash**: https://dash.plotly.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Redis**: https://redis.io/docs/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **PostGIS**: https://postgis.net/documentation/
- **OpenMeteo**: https://open-meteo.com/en/docs
- **Docker**: https://docs.docker.com/
- **pytest**: https://docs.pytest.org/

---

**Última atualização**: 2025-10-08  
**Versão**: 1.0.0  
**Mantido por**: Ângela Cunha Soares
