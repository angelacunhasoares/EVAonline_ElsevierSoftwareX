# 📊 Estratégia de Monitoramento EVAonline

## 🎯 Visão Geral

O EVAonline implementa **dois níveis de observabilidade** para atender diferentes públicos:

### **Nível 1: Técnico (Desenvolvedores/DevOps)**
- **Público**: Desenvolvedores, DevOps, SRE
- **Objetivo**: Debug, troubleshooting, métricas técnicas detalhadas
- **Ferramentas**: Prometheus, Swagger, Logs estruturados

### **Nível 2: Negócio (Usuários/Gestores)**
- **Público**: Usuários finais, gestores, stakeholders
- **Objetivo**: Visibilidade de saúde da aplicação, métricas de negócio
- **Ferramentas**: Grafana com dashboards visuais amigáveis

---

## 🔧 **Nível 1: Monitoramento Técnico**

### **1.1. Prometheus (Métricas Brutas)**

**Acesso**: `http://localhost:9090`

**O que monitora**:
- Métricas de performance (latência, throughput)
- Métricas de infraestrutura (CPU, memória, disco)
- Métricas de aplicação (cache hit rate, erros)

**Métricas disponíveis**:
```promql
# Requests por segundo
rate(http_requests_total[5m])

# Latência P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Taxa de erro
rate(http_requests_total{status=~"5.."}[5m])

# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Active requests
api_active_requests
```

**Configuração**: `monitoring/prometheus.yml`
- Scrape interval: 15s
- Jobs configurados: api, celery, redis, postgres

### **1.2. Swagger/OpenAPI (Documentação da API)**

**Acesso**: `http://localhost:8000/api/v1/docs`

**Funcionalidades**:
- ✅ Documentação interativa de todos os endpoints
- ✅ Teste de endpoints direto no navegador
- ✅ Schemas de request/response
- ✅ Códigos de erro e exemplos

**Endpoints principais**:
```
GET  /api/v1/health          - Health check
GET  /api/v1/elevation       - Buscar elevação
POST /api/v1/eto/calculate   - Calcular ETo
GET  /metrics                - Métricas Prometheus
```

### **1.3. Logs Estruturados**

**Localização**: `logs/`
- `logs/api.log` - Logs da API FastAPI
- `logs/app.log` - Logs gerais da aplicação
- `logs/eto_calculator.log` - Logs específicos do cálculo de ETo

**Formato**:
```
2025-10-08 18:48:15 | INFO | backend.api.services.openmeteo:get_openmeteo_elevation:358 - Redis connection successful
```

**Níveis de log**:
- `DEBUG` - Informações detalhadas de debug
- `INFO` - Informações gerais de operação
- `WARNING` - Avisos de situações anormais
- `ERROR` - Erros que afetam funcionalidades
- `CRITICAL` - Erros críticos que param a aplicação

---

## 📈 **Nível 2: Dashboards Visuais (Grafana)**

### **2.1. Acesso ao Grafana**

**URL**: `http://localhost:3000`
**Credenciais padrão**:
- Usuário: `admin`
- Senha: `admin` (alterar no primeiro acesso)

### **2.2. Dashboard Principal: "EVAonline Application Metrics"**

**Arquivo**: `docker/monitoring/grafana/dashboards/evaonline-metrics.json`

**Painéis disponíveis**:

#### **1. API Requests per Second** 📊
- Visualização de requisições por segundo
- Breakdown por método (GET, POST) e endpoint
- Identificação de picos de tráfego

#### **2. Response Time** ⏱️
- Latência P50 (mediana)
- Latência P95 (95% das requisições)
- Identificação de degradação de performance

#### **3. Cache Performance** 💾
- Taxa de cache hit (%)
- Cache miss rate
- Economia de tempo por uso de cache

#### **4. Error Rate** ⚠️
- Taxa de erros 4xx (cliente)
- Taxa de erros 5xx (servidor)
- Alertas visuais quando exceder threshold

#### **5. System Resources** 🖥️
- CPU usage
- Memory usage
- Disk I/O

### **2.3. Configuração de Alertas**

**Arquivo**: `docker/monitoring/grafana/provisioning/alerting/`

**Alertas configurados**:

1. **High Error Rate** (>5% de erros 5xx)
   - Notifica via email/Slack
   - Threshold: 5% em 5 minutos

2. **High Latency** (P95 > 2s)
   - Indica degradação de performance
   - Threshold: 2 segundos P95

3. **Low Cache Hit Rate** (<70%)
   - Cache não está sendo efetivo
   - Threshold: 70% hit rate

4. **Service Down** (uptime < 99%)
   - Serviço indisponível
   - Verificação a cada 30s

---

## 🚀 **Como Subir o Stack de Monitoramento**

### **Opção 1: Desenvolvimento (Local + Docker para infraestrutura)**

```bash
# 1. Subir Redis e PostgreSQL (já rodando)
docker-compose up -d redis postgres

# 2. Subir Prometheus e Grafana
docker-compose up -d prometheus grafana

# 3. Iniciar API localmente
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 4. Acessar dashboards
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
# - API Docs: http://localhost:8000/api/v1/docs
```

### **Opção 2: Produção Completa (Tudo no Docker)**

```bash
# Subir todos os serviços com profile production
docker-compose --profile production up -d

# Verificar saúde dos containers
docker ps

# Acessar logs
docker-compose logs -f api
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

---

## 📋 **Métricas de Negócio para Usuários**

### **Dashboard "User Metrics" (Recomendado criar)**

**Métricas amigáveis para usuários**:

1. **Disponibilidade do Sistema** 🟢
   - Uptime atual (%)
   - Tempo médio de resposta
   - Status: Operacional / Degradado / Indisponível

2. **Uso da Plataforma** 📈
   - Total de consultas hoje
   - Consultas por região (MATOPIBA vs Mundo)
   - Cidades mais consultadas

3. **Performance do Cache** ⚡
   - % de consultas instantâneas (cache)
   - Tempo economizado pelo cache
   - Economia em chamadas de API externa

4. **Dados Processados** 📊
   - Total de cálculos de ETo realizados
   - Fontes de dados utilizadas
   - Cobertura geográfica

### **Como criar dashboard customizado**:

1. Acessar Grafana: `http://localhost:3000`
2. Clicar em **"+"** → **"New Dashboard"**
3. Adicionar painel com query Prometheus:
   ```promql
   # Exemplo: Total de requests hoje
   increase(http_requests_total[24h])
   ```
4. Configurar visualização (gauge, graph, stat)
5. Salvar dashboard

---

## 🔐 **Controle de Acesso**

### **Níveis de Acesso Sugeridos**:

| Ferramenta | Público | Autenticação |
|------------|---------|--------------|
| **Grafana (Visualização)** | Todos os usuários | Login público (read-only) |
| **Grafana (Admin)** | DevOps/Admins | Login com senha forte |
| **Prometheus** | DevOps/Desenvolvedores | Rede interna ou VPN |
| **Swagger Docs** | Desenvolvedores | Autenticação básica |
| **Logs** | DevOps/SRE | Acesso SSH ao servidor |

### **Configurar acesso público ao Grafana**:

**Editar**: `docker-compose.yml` (serviço grafana)
```yaml
grafana:
  environment:
    # Permitir visualização anônima (somente leitura)
    - GF_AUTH_ANONYMOUS_ENABLED=true
    - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
    
    # Desabilitar signup
    - GF_USERS_ALLOW_SIGN_UP=false
```

---

## 📦 **Exportação de Métricas**

### **Prometheus Exporter Endpoints**:

```
GET /metrics                    - Métricas da API (FastAPI)
GET http://redis:6379/metrics   - Redis metrics (via exporter)
GET http://postgres:5432/metrics - PostgreSQL metrics (via exporter)
```

### **Métricas customizadas disponíveis**:

```python
# backend/api/middleware/prometheus_metrics.py

# Contadores
API_REQUESTS = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
CACHE_HITS = Counter('cache_hits_total', 'Total cache hits')
CACHE_MISSES = Counter('cache_misses_total', 'Total cache misses')

# Histogramas
API_REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')

# Gauges
API_ACTIVE_REQUESTS = Gauge('api_active_requests', 'Active API requests')
```

---

## 🎨 **Personalização de Dashboards**

### **Exemplo: Dashboard de Negócio Simplificado**

```json
{
  "title": "EVAonline - Visão Geral para Usuários",
  "panels": [
    {
      "title": "Sistema Operacional?",
      "type": "stat",
      "targets": [{
        "expr": "up{job='api'} == 1"
      }],
      "fieldConfig": {
        "mappings": [
          {"value": 1, "text": "✅ Online", "color": "green"},
          {"value": 0, "text": "❌ Offline", "color": "red"}
        ]
      }
    },
    {
      "title": "Consultas nas Últimas 24h",
      "type": "stat",
      "targets": [{
        "expr": "increase(http_requests_total[24h])"
      }]
    },
    {
      "title": "Cache Economizando Tempo",
      "type": "gauge",
      "targets": [{
        "expr": "(cache_hits_total / (cache_hits_total + cache_misses_total)) * 100"
      }]
    }
  ]
}
```

---

## 🔍 **Troubleshooting**

### **Prometheus não está coletando métricas**:
```bash
# Verificar se API está expondo /metrics
curl http://localhost:8000/metrics

# Verificar configuração do Prometheus
docker exec -it evaonline-prometheus cat /etc/prometheus/prometheus.yml

# Ver logs do Prometheus
docker logs evaonline-prometheus
```

### **Grafana não está mostrando dados**:
1. Verificar se datasource Prometheus está configurado
2. Acessar: Grafana → Configuration → Data Sources
3. Testar conexão com Prometheus
4. Verificar queries nos painéis

### **Métricas não aparecem**:
- Aguardar 15s (scrape interval do Prometheus)
- Fazer algumas requests na API para gerar métricas
- Verificar se endpoints estão instrumentados

---

## 📚 **Recursos Adicionais**

- [Prometheus Query Language (PromQL)](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [FastAPI Prometheus Instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)

---

## ✅ **Checklist de Implementação**

- [x] Prometheus configurado e coletando métricas
- [x] API expondo endpoint `/metrics`
- [x] Grafana com datasource Prometheus
- [ ] Dashboard técnico para DevOps
- [ ] Dashboard simplificado para usuários
- [ ] Alertas configurados
- [ ] Acesso público (read-only) ao Grafana
- [ ] Documentação de uso para equipe
- [ ] Backup automático de dashboards

---

**Autor**: EVAonline Team  
**Última atualização**: Outubro 2025  
**Versão**: 1.0
