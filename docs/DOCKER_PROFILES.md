# Docker Compose Profiles - EVA Online

## 🚀 Como Usar

### Desenvolvimento (com ferramentas extras)
```bash
docker-compose --profile development up
```
**Serviços incluídos:** postgres, redis, api, cadvisor, celery-worker, flower, prometheus, grafana, portainer, celery-beat, pgadmin

### Produção (apenas serviços essenciais)
```bash
docker-compose --profile production up
```
**Serviços incluídos:** postgres, redis, api, cadvisor, celery-worker, flower, prometheus, grafana, celery-beat, nginx

### Todos os serviços
```bash
docker-compose --profile development --profile production up
```

## 📋 Perfis Disponíveis

### `development`
- ✅ API com hot-reload
- ✅ PgAdmin (administração PostgreSQL)
- ✅ Portainer (gerenciamento de containers)
- ✅ Todos os serviços de produção

### `production`
- ✅ API otimizada
- ✅ Nginx (proxy reverso)
- ✅ Serviços essenciais apenas

## 🔧 Comandos Úteis

```bash
# Ver logs de um serviço específico
docker-compose logs api

# Parar todos os serviços
docker-compose down

# Limpar volumes
docker-compose down -v

# Ver status dos serviços
docker-compose ps

# Ver serviços disponíveis em um profile
docker-compose --profile development config --services
```
