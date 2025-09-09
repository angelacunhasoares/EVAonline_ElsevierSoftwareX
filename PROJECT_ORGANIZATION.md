# 📁 Organização do Projeto EVAonline

## 📂 Estrutura de Pastas

### 🔧 `scripts/`
Scripts utilitários e ferramentas de gerenciamento:
- `manage.bat` / `manage.sh` - Scripts de gerenciamento
- `manage_db.py` - Ferramentas de banco de dados
- `get_hourly_data.py` - Script para obter dados horários do Open-Meteo
- `requirementx.txt` - Backup de requirements

### 🧪 `tests/`
Todos os arquivos de teste do projeto:
- `test_db.py` - Testes de banco de dados
- `test_openmeteo.py` - Testes da API Open-Meteo
- `test_psycopg2.py` - Testes de conexão PostgreSQL

### 🗄️ `database/`
Arquivos relacionados ao banco de dados:

#### `database/init/`
- `init_alembic.py` - Inicialização do Alembic
- `init-db/` - Scripts de inicialização do banco

#### `database/migrations/`
- `migration.sql` - Scripts de migração SQL
- `fix_postgres_encoding.sql` - Correções de encoding PostgreSQL

### 📊 `data/`
Arquivos de dados e resultados:
- `hourly_weather_data.json` - Dados meteorológicos horários
- Outros arquivos de dados gerados

## 🎯 Benefícios da Organização

### ✅ **Manutenibilidade**
- Arquivos relacionados agrupados logicamente
- Fácil localização de scripts e testes
- Separação clara entre código, dados e configurações

### ✅ **Colaboração**
- Estrutura padronizada e intuitiva
- Menos conflitos em repositórios compartilhados
- Documentação clara da organização

### ✅ **Desenvolvimento**
- Scripts de teste isolados
- Ferramentas de gerenciamento centralizadas
- Dados organizados por tipo

## 🚀 Como Usar

### Executar Testes
```bash
python -m pytest tests/
# ou
python tests/test_openmeteo.py
```

### Usar Scripts
```bash
python scripts/manage_db.py
python scripts/get_hourly_data.py
```

### Trabalhar com Banco de Dados
```bash
# Scripts de migração
ls database/migrations/

# Scripts de inicialização
ls database/init/
```

## 📋 Convenções

- **Scripts**: Arquivos `.py`, `.bat`, `.sh` em `scripts/`
- **Testes**: Arquivos `test_*.py` em `tests/`
- **Migrações**: Arquivos SQL em `database/migrations/`
- **Dados**: Arquivos `.json`, `.csv` em `data/`

Esta organização mantém o projeto limpo, organizado e fácil de navegar! 🎉
