# Guia de Acesso ao Grafana - EVAonline

## Como acessar o Grafana

### 1. Iniciar os serviços de monitoramento

```bash
# Opção 1: Iniciar apenas Prometheus e Grafana
./start-monitoring.sh

# Opção 2: Iniciar todos os serviços
docker-compose up -d
```

### 2. Acessar o Grafana

- **URL:** http://localhost:3000
- **Usuário:** admin
- **Senha:** admin

### 3. Configuração inicial

1. No primeiro acesso, o Grafana irá solicitar alteração da senha
2. Você pode manter a senha "admin" ou definir uma nova

### 4. Visualizar métricas

#### Dashboard pré-configurado:
- O dashboard "EVAonline Application Metrics" já está configurado automaticamente
- Ele inclui painéis para:
  - Taxa de requisições por segundo
  - Tempo de resposta (percentis)
  - Conexões ativas
  - Uso de memória

#### Métricas disponíveis:
- `http_requests_total` - Total de requisições HTTP
- `http_request_duration_seconds` - Duração das requisições
- `evaonline_active_connections` - Conexões ativas
- `process_resident_memory_bytes` - Uso de memória

### 5. Adicionar novas métricas

Para adicionar novas métricas personalizadas:

1. Vá em **Configuration > Data Sources**
2. Selecione o datasource **Prometheus**
3. Clique em **Explore** para testar queries
4. Exemplos de queries:
   ```
   # Taxa de erro
   rate(http_requests_total{status=~"5.."}[5m])

   # Latência média
   rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

   # Uso de CPU
   rate(process_cpu_user_seconds_total[5m])
   ```

### 6. Criar novos dashboards

1. Vá em **Create > Dashboard**
2. Clique em **Add new panel**
3. Configure a query PromQL
4. Ajuste visualizações e alertas

### 7. Configuração do Prometheus

O Prometheus está configurado para coletar métricas de:
- API FastAPI (porta 8000)
- Aplicação Dash (porta 8000, mesmo container)

**URL do Prometheus:** http://localhost:9090

### 8. Troubleshooting

#### Problema: Grafana não consegue conectar ao Prometheus
- Verifique se o container do Prometheus está rodando: `docker-compose ps`
- Verifique os logs: `docker-compose logs prometheus`

#### Problema: Métricas não aparecem
- Verifique se a aplicação está rodando e expondo métricas em `/metrics`
- Teste o endpoint: `curl http://localhost:8000/metrics`

#### Problema: Dashboard vazio
- Vá em **Dashboards > Browse** e selecione "EVAonline Application Metrics"
- Ou importe o dashboard manualmente em **Create > Import**

### 9. Segurança

Para produção, considere:
- Alterar credenciais padrão
- Configurar HTTPS
- Restringir acesso por rede
- Configurar alertas

### 10. Documentação adicional

- [Documentação Grafana](https://grafana.com/docs/)
- [Documentação Prometheus](https://prometheus.io/docs/)
- [Guia PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/)
