# 📁 Estrutura do Projeto EVAonline

Esta documentação descreve a estrutura de pastas do projeto após a reorganização de 2025-10-10.

## 🗂️ Estrutura Geral

```
EVAonline_ElsevierSoftwareX/
│
├── backend/                  # Código backend Python
│   ├── api/                 # API REST (FastAPI)
│   ├── core/                # Lógica de negócio
│   ├── database/            # Modelos e conexões de BD
│   ├── infrastructure/      # Celery, cache, etc.
│   └── tests/              # Testes específicos do backend
│
├── frontend/                # Interface Dash
│   ├── app.py              # Aplicação principal
│   ├── assets/             # CSS, JS, imagens
│   ├── components/         # Componentes reutilizáveis
│   ├── pages/              # Páginas da aplicação
│   └── tests/              # Testes de frontend
│
├── tests/                   # Testes organizados
│   ├── api/                # Testes de API
│   ├── integration/        # Testes de integração
│   ├── tasks/              # Testes de Celery tasks
│   ├── analysis/           # Scripts de análise
│   └── debug/              # Scripts de debug
│
├── scripts/                 # Scripts utilitários
│   ├── api/                # Scripts relacionados à API
│   ├── database/           # Scripts de gerenciamento de BD
│   ├── testing/            # Scripts auxiliares de teste
│   └── maintenance/        # Scripts de manutenção
│
├── docs/                    # Documentação completa
│   ├── guides/             # Guias de uso
│   ├── features/           # Documentação de funcionalidades
│   ├── maintenance/        # Documentação de manutenção
│   ├── architecture/       # Arquitetura do sistema
│   └── api/                # Documentação da API
│
├── data/                    # Dados da aplicação
│   ├── csv/                # Arquivos CSV
│   ├── geojson/            # Dados geoespaciais
│   └── shapefile/          # Shapefiles
│
├── config/                  # Configurações
│   ├── settings/           # Configurações da aplicação
│   └── translations/       # Arquivos de tradução
│
├── docker/                  # Dockerfiles e configurações
│   ├── backend/            # Dockerfile do backend
│   ├── nginx/              # Configuração Nginx
│   └── monitoring/         # Configuração de monitoramento
│
├── monitoring/              # Prometheus e Grafana
│   └── prometheus.yml      # Configuração Prometheus
│
├── logs/                    # Arquivos de log
├── temp/                    # Arquivos temporários
└── archive/                 # Arquivos antigos/deprecated

```

## 📋 Arquivos na Raiz

Apenas arquivos essenciais devem permanecer na raiz:

### Obrigatórios
- `README.md` - Documentação principal
- `requirements.txt` - Dependências Python
- `docker-compose.yml` - Configuração Docker
- `Dockerfile` - Imagem Docker principal
- `.env.example` - Template de variáveis de ambiente
- `.gitignore` - Arquivos ignorados pelo Git
- `alembic.ini` - Configuração Alembic (migrações)
- `entrypoint.sh` - Script de entrada Docker
- `LICENSE` - Licença do projeto

### Locais (não commitados)
- `.env` - Variáveis de ambiente locais
- `docker-compose.override.yml` - Overrides locais do Docker

## 🔧 Comandos Úteis

### Executar testes
```bash
# Todos os testes
pytest tests/

# Testes específicos
pytest tests/api/
pytest tests/integration/
pytest tests/tasks/
```

### Gerenciamento de pastas
```bash
# Limpar cache Python
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# Limpar logs antigos (>7 dias)
Get-ChildItem logs/*.log | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item
```

### Docker
```bash
# Iniciar aplicação
docker-compose up -d

# Rebuild sem cache
docker-compose build --no-cache

# Ver logs
docker-compose logs -f api
```

## 📚 Documentação Adicional

- [Guias de Uso](docs/guides/)
- [Funcionalidades](docs/features/)
- [Manutenção](docs/maintenance/)
- [Arquitetura](docs/architecture/)
- [API Documentation](docs/api/)

## 🧹 Manutenção

Para manter o projeto organizado:

1. **Novos testes**: Coloque em `tests/` na subpasta apropriada
2. **Novos scripts**: Coloque em `scripts/` na subpasta apropriada
3. **Nova documentação**: Coloque em `docs/` na subpasta apropriada
4. **Arquivos temporários**: Use `temp/` e limpe regularmente
5. **Arquivos antigos**: Mova para `archive/` antes de deletar

## 📝 Changelog da Reorganização

### 2025-10-10
- ✅ Criada estrutura organizada de pastas
- ✅ Movidos arquivos de teste para `tests/`
- ✅ Movidos scripts para `scripts/`
- ✅ Organizada documentação em `docs/`
- ✅ Limpeza de cache Python e arquivos temporários
- ✅ Criados READMEs em todas as subpastas
- ✅ Atualizado `.gitignore`

---

**Última atualização**: 2025-10-10
