# 🗄️ Database Directory

Diretório para scripts e configurações relacionadas ao banco de dados PostgreSQL.

## 📁 Estrutura

```
database/
├── init/                      # Scripts de inicialização
│   └── init_alembic.py       # Inicializa Alembic programaticamente
├── scripts/                   # Scripts administrativos SQL
│   └── fix_postgres_encoding.sql  # Recriar banco com UTF-8
└── init_alembic.py           # Script de inicialização (raiz)
```

## 🔧 Scripts Disponíveis

### `scripts/fix_postgres_encoding.sql`
Script administrativo para recriar o banco `evaonline` com encoding UTF-8 correto.

**Quando usar:**
- Banco criado com encoding errado
- Problemas de caracteres especiais (ã, ç, é, etc.)
- Recriação completa do banco

**Como executar:**
```bash
# Via psql
psql -U postgres -f database/scripts/fix_postgres_encoding.sql

# Via Docker
docker exec -i evaonline-postgres psql -U postgres < database/scripts/fix_postgres_encoding.sql
```

## 📦 Migrações

**⚠️ IMPORTANTE:** Não crie arquivos `.sql` neste diretório para migrações!

**Use Alembic para todas as migrações de schema:**

```bash
# Criar nova migração
alembic revision -m "Add new table"

# Aplicar migrações
alembic upgrade head

# Reverter última migração
alembic downgrade -1

# Ver histórico
alembic history
```

As migrações ficam em: `alembic/versions/`

## 🔗 Relacionado

- [Alembic Migrations](../alembic/) - Migrações versionadas
- [Backend Database](../backend/database/) - Modelos e conexão
- [Docker Compose](../docker-compose.yml) - Configuração do PostgreSQL
