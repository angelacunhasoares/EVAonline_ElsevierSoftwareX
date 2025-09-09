# Gerenciamento de Banco de Dados - EVAonline

Este documento explica como gerenciar o banco de dados PostgreSQL do projeto EVAonline usando Alembic para migrações automatizadas.

## 📁 Estrutura do Banco de Dados

```
backend/database/
├── connection.py          # Configuração da conexão SQLAlchemy
├── session_database.py    # Gerenciamento de sessões FastAPI
├── data_storage.py        # Funções de armazenamento de dados
├── __init__.py           # Inicialização do banco
├── models/               # Modelos SQLAlchemy
│   ├── __init__.py
│   └── climate_data.py   # Modelo EToResults
└── migrations/           # Migrações manuais (legado)
    └── create_tables.py
```

## 🔧 Configuração do Alembic

O projeto usa **Alembic** para gerenciamento automatizado de migrações de banco de dados.

### Arquivos de Configuração:
- `alembic.ini` - Configuração principal do Alembic
- `alembic/env.py` - Ambiente de execução das migrações
- `alembic/versions/` - Migrações versionadas

## 🚀 Como Usar

### 1. Verificar Status das Migrações
```bash
# Ver status atual
python manage_db.py status

# Ver histórico
python manage_db.py history
```

### 2. Criar Nova Migração
```bash
# Migração automática baseada nos modelos
python manage_db.py migrate "Adicionar campo novo"

# Ou diretamente com Alembic
alembic revision --autogenerate -m "Descrição da migração"
```

### 3. Aplicar Migrações
```bash
# Aplicar todas as migrações pendentes
python manage_db.py upgrade

# Aplicar até uma revisão específica
python manage_db.py upgrade 001

# Ou diretamente com Alembic
alembic upgrade head
```

### 4. Reverter Migrações
```bash
# Reverter uma migração
python manage_db.py downgrade

# Reverter para uma revisão específica
python manage_db.py downgrade 001

# Ou diretamente com Alembic
alembic downgrade -1
```

## 📊 Modelos Disponíveis

### EToResults
Armazena resultados de cálculos de evapotranspiração de referência.

**Campos:**
- `id`: Chave primária (Integer)
- `lat`: Latitude (Float)
- `lng`: Longitude (Float)
- `elevation`: Elevação (Float, opcional)
- `date`: Data do cálculo (DateTime)
- `t2m_max`: Temperatura máxima (°C, opcional)
- `t2m_min`: Temperatura mínima (°C, opcional)
- `rh2m`: Umidade relativa (%) (opcional)
- `ws2m`: Velocidade do vento (m/s, opcional)
- `radiation`: Radiação solar (MJ/m²/dia, opcional)
- `precipitation`: Precipitação (mm, opcional)
- `eto`: Evapotranspiração de referência (mm/dia)

## 🔄 Migração Inicial

A migração inicial (`001_create_initial_tables.py`) cria:
- Tabela `eto_results` com todos os campos necessários
- Índices para campos frequentemente consultados (`id`, `lat`, `lng`, `date`)

## 📝 Scripts de Gerenciamento

### manage_db.py
Script utilitário para facilitar o uso do Alembic:

```bash
# Criar migração
python manage_db.py migrate "Minha migração"

# Aplicar migrações
python manage_db.py upgrade

# Ver status
python manage_db.py status
```

### data_storage.py
Funções para armazenamento de dados:

```python
from database.data_storage import save_eto_data

# Salvar dados de ETo
save_eto_data(dados_eto)
```

## ⚠️ Notas Importantes

1. **Sempre faça backup** antes de aplicar migrações em produção
2. **Teste as migrações** em ambiente de desenvolvimento primeiro
3. **Mantenha o histórico** de migrações versionado no Git
4. **Use mensagens descritivas** nas migrações para facilitar o entendimento

## 🐛 Troubleshooting

### Erro de Conexão
- Verifique se o PostgreSQL está rodando
- Confirme as credenciais em `connection.py`
- Verifique se o banco `evaonline` existe

### Migração Não Aplicada
- Execute `alembic current` para ver o status
- Use `alembic upgrade head` para aplicar todas
- Verifique logs do PostgreSQL

### Modelo Não Sincronizado
- Execute `alembic revision --autogenerate` para detectar mudanças
- Reveja a migração gerada antes de aplicar

## 📚 Referências

- [Documentação Alembic](https://alembic.sqlalchemy.org/)
- [Documentação SQLAlchemy](https://sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
