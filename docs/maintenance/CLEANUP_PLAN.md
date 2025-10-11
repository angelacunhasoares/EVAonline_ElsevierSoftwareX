# 🧹 Plano de Limpeza do Projeto EVAonline

## 📋 Ações Necessárias

### 1. ❌ REMOVER Pastas Vazias
```bash
# Raiz
rmdir init-db

# Database
rmdir database/init/init-db

# Pasta que deveria ser arquivo
rmdir pg_hba_extra.conf
```

### 2. 📝 ATUALIZAR .gitignore

Adicionar:
```gitignore
# ===========================================
# Temporary Results and Outputs
# ===========================================
temp/*.csv
temp/*.conf
temp/*.tmp
temp/*.output

# ===========================================
# Old Test Files (deprecated)
# ===========================================
tests/test_*.py
tests/insert_data.py
tests/*.ps1
!tests/conftest.py
!tests/README.md

# Manter apenas:
# - tests/integration/ (novos testes organizados)
# - tests/conftest.py (fixtures globais)
```

### 3. 🗂️ ORGANIZAR Testes Antigos

**Opção A - Mover para pasta de arquivo:**
```
tests/
├── integration/          # ✅ Testes novos (MANTER)
├── conftest.py          # ✅ Fixtures (MANTER)
├── README.md            # ✅ Documentação (MANTER)
└── deprecated/          # 📦 Testes antigos (ARQUIVAR)
    ├── test_db.py
    ├── test_openmeteo.py
    ├── test_postgres_connection.py
    └── ...
```

**Opção B - Deletar completamente:**
```bash
# Se não são mais necessários
rm tests/test_*.py
rm tests/insert_data.py
rm tests/*.ps1
```

### 4. 📁 Estrutura Recomendada

```
EVAonline/
├── .env.example              # ✅ Versionado
├── .gitignore               # ✅ Atualizado
├── docker-compose.yml       # ✅ Configuração base
├── docker-compose.override.example.yml  # ✅ Exemplo local
├── Dockerfile               # ✅ Build principal
├── requirements.txt         # ✅ Dependências
├── README.md                # ✅ Documentação
│
├── alembic/                 # ✅ Migrações DB
├── backend/                 # ✅ Código backend
├── frontend/                # ✅ Código frontend
├── config/                  # ✅ Configurações
├── data/                    # ✅ Dados estáticos
├── docs/                    # ✅ Documentação
├── scripts/                 # ✅ Scripts auxiliares
├── utils/                   # ✅ Utilitários
│
├── database/                # ✅ DB específico
│   ├── init/               # Scripts de inicialização
│   ├── migrations/         # Migrações SQL
│   └── models/             # Modelos de dados
│
├── docker/                  # ✅ Dockerfiles específicos
│   ├── backend/
│   ├── nginx/
│   └── monitoring/
│
├── tests/                   # ✅ LIMPAR
│   ├── integration/        # ✅ Novos testes (MANTER)
│   ├── unit/              # 🆕 Criar para testes unitários
│   ├── conftest.py        # ✅ Fixtures (MANTER)
│   └── README.md          # ✅ Docs (MANTER)
│
├── logs/                    # ❌ NÃO VERSIONAR (gitignore)
├── temp/                    # ❌ NÃO VERSIONAR (gitignore)
└── .venv/                   # ❌ NÃO VERSIONAR (já no gitignore)
```

### 5. 🔧 Arquivos de Configuração

**MANTER Versionados:**
- `.env.example` ✅
- `docker-compose.yml` ✅
- `docker-compose.override.example.yml` ✅
- `alembic.ini` ✅
- `requirements.txt` ✅

**NÃO Versionar:**
- `.env` ❌ (gitignore)
- `docker-compose.override.yml` ❌ (gitignore)
- `logs/*.log` ❌ (gitignore)
- `temp/*` ❌ (gitignore)

### 6. 📦 Database Folder

**Propósito Atual:**
```
database/
├── init/
│   ├── init_alembic.py       # Script de inicialização Alembic
│   └── init-db/             # ❌ VAZIA - DELETAR
├── migrations/
│   ├── fix_postgres_encoding.sql
│   └── migration.sql
└── init_alembic.py          # ❌ DUPLICADO? Verificar
```

**Questionamentos:**
1. `init_alembic.py` está duplicado (raiz de database/ e em init/)
2. `init-db/` vazia serve para Docker entrypoint? → Verificar docker-compose.yml
3. Migrações SQL devem ir para `alembic/versions/` ou ficar em `database/migrations/`?

### 7. 🐳 Docker Init-DB

**No docker-compose.yml:**
```yaml
volumes:
  - ./init-db:/docker-entrypoint-initdb.d
```

**Propósito:** PostgreSQL executa automaticamente scripts SQL/sh em `/docker-entrypoint-initdb.d` na primeira inicialização.

**Opções:**
- A) Usar `/init-db/` (raiz) com scripts SQL de inicialização
- B) Remover e usar Alembic para migrações
- C) Usar `/database/init/scripts/` ao invés de raiz

## ✅ Decisões Necessárias

1. **Testes antigos**: Deletar ou arquivar?
2. **init-db folder**: Manter na raiz ou mover para database/?
3. **Migrações**: Unificar em Alembic ou manter SQLs separados?
4. **Logs**: Commit atual ou limpar histórico?
5. **Temp files**: Limpar agora?

## 🚀 Comandos de Limpeza (Após decisões)

```bash
# 1. Remover pastas vazias
Remove-Item -Recurse init-db
Remove-Item -Recurse database/init/init-db
Remove-Item -Recurse pg_hba_extra.conf

# 2. Limpar logs (não versionar)
git rm --cached logs/*.log
Remove-Item logs/*.log

# 3. Limpar temp (não versionar)
git rm --cached temp/*.csv temp/*.conf
Remove-Item temp/*.csv, temp/*.conf

# 4. Organizar testes antigos
New-Item -ItemType Directory tests/deprecated
Move-Item tests/test_*.py tests/deprecated/
Move-Item tests/insert_data.py tests/deprecated/
Move-Item tests/*.ps1 tests/deprecated/

# 5. Atualizar .gitignore
# (editar manualmente conforme sugestões acima)

# 6. Commit das mudanças
git add .gitignore
git commit -m "chore: Clean project structure and update gitignore"
```
