# 🚀 Guia Rápido: Monitoramento EVAonline

## Para Usuários Comuns

### Acesso ao Dashboard

1. **Abra o navegador** e acesse: `http://localhost:3000`
2. **Sem login necessário!** O dashboard abrirá automaticamente em modo visualização
3. Você verá métricas amigáveis como:
   - ✅ Sistema online/offline
   - ⏱️ Tempo de resposta
   - 📊 Total de consultas
   - ⚡ Eficiência do cache

### O que cada métrica significa

| Métrica | O que mostra | Bom / Ruim |
|---------|--------------|------------|
| **Status do Sistema** | Se o sistema está funcionando | 🟢 Online = Bom / 🔴 Offline = Ruim |
| **Tempo de Resposta** | Quão rápido o sistema responde | < 1s = Bom / > 2s = Lento |
| **Consultas Hoje** | Quantas pessoas usaram hoje | Quanto mais, melhor! |
| **Cache Ativo (%)** | % de respostas instantâneas | > 80% = Excelente |
| **Taxa de Erro** | % de erros no sistema | < 1% = Normal / > 5% = Problema |
| **Uptime 24h** | Tempo que ficou no ar hoje | > 99% = Excelente |

### Navegando pelos Dashboards

**Dashboard Principal**: "EVAonline - Visão do Usuário"
- Métricas gerais de saúde
- Fácil de entender
- Atualiza a cada 30 segundos

**Dashboard Técnico**: "EVAonline Application Metrics" (opcional)
- Métricas mais detalhadas
- Para quem quer ver mais informações técnicas

---

## Para Desenvolvedores/DevOps

### Acesso Técnico

```bash
# 1. Subir stack completo
docker-compose up -d prometheus grafana

# 2. Acessar ferramentas
# Grafana (dashboards): http://localhost:3000
# Prometheus (métricas): http://localhost:9090
# API Docs (Swagger): http://localhost:8000/api/v1/docs
# Métricas API: http://localhost:8000/metrics
```

### Login Admin no Grafana

**URL**: http://localhost:3000/login
**Credenciais**:
- Usuário: `admin`
- Senha: `admin` (alterar no primeiro acesso!)

### Queries Prometheus Úteis

```promql
# Taxa de requisições
rate(http_requests_total[5m])

# Latência P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Erros por segundo
rate(http_requests_total{status=~"5.."}[5m])

# Requests ativos
api_active_requests
```

### Criando Alertas

1. Grafana → Alerting → Alert rules → New alert rule
2. Configurar condição (ex: error rate > 5%)
3. Definir canal de notificação (Slack, email, etc.)
4. Salvar e testar

### Exemplo de Alerta: High Error Rate

```yaml
alert: HighErrorRate
expr: (rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) > 0.05
for: 5m
labels:
  severity: critical
annotations:
  summary: "Taxa de erro muito alta!"
  description: "{{ $value }}% dos requests estão com erro 5xx"
```

---

## Troubleshooting

### ❌ Problema: "Grafana não abre"

**Solução**:
```bash
# Verificar se container está rodando
docker ps | grep grafana

# Se não estiver, iniciar
docker-compose up -d grafana

# Ver logs
docker logs evaonline-grafana
```

### ❌ Problema: "Métricas não aparecem"

**Solução**:
```bash
# 1. Verificar se API está expondo métricas
curl http://localhost:8000/metrics

# 2. Verificar se Prometheus está coletando
# Abra: http://localhost:9090/targets
# Deve mostrar "UP" para o job "api"

# 3. Fazer algumas requisições para gerar métricas
curl http://localhost:8000/api/v1/health
```

### ❌ Problema: "Dashboard está vazio"

**Possíveis causas**:
1. Prometheus não está conectado
   - Grafana → Configuration → Data Sources → Test
2. Tempo selecionado está errado
   - Mudar range para "Last 6 hours"
3. Ainda não há dados
   - Aguardar 1-2 minutos + fazer algumas requests

---

## Personalização

### Mudar Dashboard Padrão

Edite `docker-compose.yml`:
```yaml
grafana:
  environment:
    - GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/var/lib/grafana/dashboards/seu-dashboard.json
```

### Adicionar Novo Painel

1. Grafana → Dashboard → Add Panel
2. Escolher tipo (Graph, Stat, Gauge, etc.)
3. Adicionar query Prometheus
4. Configurar visualização
5. Salvar

### Exportar Dashboard

1. Dashboard → Settings (⚙️)
2. JSON Model → Copy to clipboard
3. Salvar em `docker/monitoring/grafana/dashboards/`

---

## Checklist de Verificação

- [ ] Prometheus rodando (`docker ps | grep prometheus`)
- [ ] Grafana rodando (`docker ps | grep grafana`)
- [ ] API rodando e expondo `/metrics`
- [ ] Grafana conectado ao Prometheus
- [ ] Dashboard "User" visível sem login
- [ ] Dashboard "Metrics" disponível para admins
- [ ] Métricas sendo coletadas (fazer requests de teste)
- [ ] Alertas configurados (opcional)

---

## Referências Rápidas

| Serviço | URL | Acesso |
|---------|-----|--------|
| **Dashboard Usuário** | http://localhost:3000 | Aberto (read-only) |
| **Grafana Admin** | http://localhost:3000/login | admin/admin |
| **Prometheus** | http://localhost:9090 | Aberto |
| **API Docs** | http://localhost:8000/api/v1/docs | Aberto |
| **Métricas API** | http://localhost:8000/metrics | Aberto |

---

**Dica**: Para acessar de outros dispositivos na rede, substitua `localhost` pelo IP do servidor!

Exemplo: `http://192.168.1.100:3000`
