#!/bin/bash
# Script unificado para gerenciamento do projeto EVAonline
# Uso: ./manage.sh [comando] [opções]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para exibir ajuda
show_help() {
    echo "Script de gerenciamento do projeto EVAonline"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  monitoring    Iniciar serviços de monitoramento (Prometheus + Grafana)"
    echo "  test-redis    Testar conexão básica com Redis"
    echo "  vscode-redis  Teste completo Redis + instruções VS Code"
    echo "  test-all      Executar todos os testes de conectividade"
    echo "  start         Iniciar todos os serviços Docker"
    echo "  stop          Parar todos os serviços Docker"
    echo "  restart       Reiniciar todos os serviços Docker"
    echo "  logs          Mostrar logs dos serviços"
    echo "  status        Mostrar status dos serviços"
    echo "  help          Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 monitoring"
    echo "  $0 test-redis"
    echo "  $0 start"
}

# Função para iniciar monitoramento
start_monitoring() {
    echo -e "${BLUE}🚀 Iniciando serviços de monitoramento (Prometheus + Grafana)...${NC}"
    echo ""

    # Criar diretórios necessários se não existirem
    mkdir -p docker/monitoring/grafana/provisioning/datasources
    mkdir -p docker/monitoring/grafana/provisioning/dashboards
    mkdir -p docker/monitoring/grafana/dashboards

    # Iniciar apenas Prometheus e Grafana
    docker-compose up -d prometheus grafana

    echo -e "${GREEN}✅ Serviços iniciados!${NC}"
    echo ""
    echo -e "${YELLOW}🌐 Acesse o Grafana em: http://localhost:3000${NC}"
    echo "Credenciais:"
    echo "  Usuário: admin"
    echo "  Senha: admin"
    echo ""
    echo -e "${YELLOW}📊 Acesse o Prometheus em: http://localhost:9090${NC}"
}

# Função para testar Redis (básico)
test_redis() {
    echo -e "${BLUE}🔍 Testando conexão básica com Redis...${NC}"
    if docker exec evaonline-redis redis-cli -a evaonline ping 2>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✅ Redis funcionando (PONG)${NC}"
    else
        echo -e "${RED}❌ Redis não responde${NC}"
    fi
}

# Função para teste completo Redis + VS Code
vscode_redis() {
    echo -e "${BLUE}🔍 Teste de Conectividade Redis para VS Code${NC}"
    echo ""

    echo "1. Verificando se o Redis está rodando..."
    if docker-compose ps redis | grep -q "Up"; then
        echo -e "${GREEN}✅ Redis container está rodando${NC}"
    else
        echo -e "${RED}❌ Redis container NÃO está rodando${NC}"
        echo "Execute: docker-compose up -d redis"
        return 1
    fi

    echo ""
    echo "2. Testando conectividade na porta 6379..."
    if nc -z localhost 6379 2>/dev/null; then
        echo -e "${GREEN}✅ Porta 6379 está acessível${NC}"
    else
        echo -e "${RED}❌ Porta 6379 NÃO está acessível${NC}"
    fi

    echo ""
    echo "3. Testando autenticação Redis..."
    if docker exec evaonline-redis redis-cli -a evaonline ping 2>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✅ Autenticação Redis funcionando${NC}"
    else
        echo -e "${RED}❌ Falha na autenticação Redis${NC}"
    fi

    echo ""
    echo "4. Informações do servidor Redis:"
    docker exec evaonline-redis redis-cli -a evaonline info server 2>/dev/null | head -5

    echo ""
    echo -e "${YELLOW}📋 Próximos passos para VS Code:${NC}"
    echo "1. Abra a extensão Redis (ícone do Redis na barra lateral)"
    echo "2. Clique no botão + para adicionar conexão"
    echo "3. Configure:"
    echo "   - Name: EVAonline Redis (Docker)"
    echo "   - Host: localhost"
    echo "   - Port: 6379"
    echo "   - Password: evaonline"
    echo "   - Username: (deixe vazio)"
    echo "4. Clique em Test Connection"
    echo "5. Clique em Save"

    echo ""
    echo -e "${YELLOW}🔧 Se ainda não funcionar:${NC}"
    echo "- Verifique se a extensão está atualizada"
    echo "- Tente desabilitar e reabilitar a extensão"
    echo "- Recarregue a janela do VS Code"
}

# Função para testar todos os serviços
test_all() {
    echo -e "${BLUE}🧪 Executando testes completos de conectividade...${NC}"
    echo ""

    # Testar Redis
    echo -e "${YELLOW}=== Testando Redis ===${NC}"
    test_redis
    echo ""

    # Testar PostgreSQL
    echo -e "${YELLOW}=== Testando PostgreSQL ===${NC}"
    if nc -z localhost 5432 2>/dev/null; then
        echo -e "${GREEN}✅ Porta 5432 (PostgreSQL) está acessível${NC}"
    else
        echo -e "${RED}❌ Porta 5432 (PostgreSQL) não está acessível${NC}"
    fi
    echo ""

    # Testar API
    echo -e "${YELLOW}=== Testando API FastAPI ===${NC}"
    if nc -z localhost 8000 2>/dev/null; then
        echo -e "${GREEN}✅ Porta 8000 (API) está acessível${NC}"
        # Testar endpoint de saúde
        if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Endpoint /api/v1/health respondendo${NC}"
        else
            echo -e "${RED}❌ Endpoint /api/v1/health não responde${NC}"
        fi
    else
        echo -e "${RED}❌ Porta 8000 (API) não está acessível${NC}"
    fi
    echo ""

    # Testar outros serviços
    echo -e "${YELLOW}=== Testando outros serviços ===${NC}"
    services=("nginx:80" "grafana:3000" "prometheus:9090" "pgadmin:5050" "flower:5555")
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        if nc -z localhost $port 2>/dev/null; then
            echo -e "${GREEN}✅ $name (porta $port) está acessível${NC}"
        else
            echo -e "${RED}❌ $name (porta $port) não está acessível${NC}"
        fi
    done
}

# Função para iniciar todos os serviços
start_all() {
    echo -e "${BLUE}🚀 Iniciando todos os serviços Docker...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ Todos os serviços iniciados!${NC}"
}

# Função para parar todos os serviços
stop_all() {
    echo -e "${BLUE}🛑 Parando todos os serviços Docker...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Todos os serviços parados!${NC}"
}

# Função para reiniciar todos os serviços
restart_all() {
    echo -e "${BLUE}🔄 Reiniciando todos os serviços Docker...${NC}"
    docker-compose restart
    echo -e "${GREEN}✅ Todos os serviços reiniciados!${NC}"
}

# Função para mostrar logs
show_logs() {
    echo -e "${BLUE}📋 Mostrando logs dos serviços...${NC}"
    docker-compose logs -f
}

# Função para mostrar status
show_status() {
    echo -e "${BLUE}📊 Status dos serviços Docker:${NC}"
    docker-compose ps
}

# Verificar se foi passado um comando
if [ $# -eq 0 ]; then
    echo -e "${RED}Erro: Nenhum comando especificado${NC}"
    echo ""
    show_help
    exit 1
fi

# Processar o comando
case "$1" in
    "monitoring")
        start_monitoring
        ;;
    "test-redis")
        test_redis
        ;;
    "vscode-redis")
        vscode_redis
        ;;
    "test-all")
        test_all
        ;;
    "start")
        start_all
        ;;
    "stop")
        stop_all
        ;;
    "restart")
        restart_all
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}Erro: Comando '$1' não reconhecido${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

# Função para iniciar monitoramento
start_monitoring() {
    echo -e "${BLUE}🚀 Iniciando serviços de monitoramento (Prometheus + Grafana)...${NC}"
    echo ""

    # Criar diretórios necessários se não existirem
    mkdir -p docker/monitoring/grafana/provisioning/datasources
    mkdir -p docker/monitoring/grafana/provisioning/dashboards
    mkdir -p docker/monitoring/grafana/dashboards

    # Iniciar apenas Prometheus e Grafana
    docker-compose up -d prometheus grafana

    echo -e "${GREEN}✅ Serviços iniciados!${NC}"
    echo ""
    echo -e "${YELLOW}🌐 Acesse o Grafana em: http://localhost:3000${NC}"
    echo "Credenciais:"
    echo "  Usuário: admin"
    echo "  Senha: admin"
    echo ""
    echo -e "${YELLOW}📊 Acesse o Prometheus em: http://localhost:9090${NC}"
}

# Função para testar Redis
test_redis() {
    echo -e "${BLUE}🔍 Testando conexão com Redis...${NC}"
    echo ""

    # Teste básico
    echo "1. Teste de conectividade (porta 6379):"
    if nc -z localhost 6379 2>/dev/null; then
        echo -e "${GREEN}✅ Porta 6379 está aberta${NC}"
    else
        echo -e "${RED}❌ Porta 6379 não está acessível${NC}"
    fi

    echo ""
    echo "2. Teste de autenticação Redis:"
    if docker exec evaonline-redis redis-cli -a evaonline ping 2>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✅ Autenticação Redis funcionando${NC}"
    else
        echo -e "${RED}❌ Falha na autenticação Redis${NC}"
    fi

    echo ""
    echo "3. Informações do servidor Redis:"
    docker exec evaonline-redis redis-cli -a evaonline info server 2>/dev/null | head -5

    echo ""
    echo "4. Chaves armazenadas:"
    docker exec evaonline-redis redis-cli -a evaonline dbsize 2>/dev/null

    echo ""
    echo -e "${YELLOW}📋 Instruções para VS Code:${NC}"
    echo "- Abra Command Palette (Ctrl+Shift+P)"
    echo "- Digite: 'Redis: Connect'"
    echo "- Selecione: 'EVAonline Redis (Docker)'"
    echo "- A conexão deve funcionar automaticamente"
}

# Função para testar todos os serviços
test_all() {
    echo -e "${BLUE}🧪 Executando testes completos de conectividade...${NC}"
    echo ""

    # Testar Redis
    echo -e "${YELLOW}=== Testando Redis ===${NC}"
    test_redis
    echo ""

    # Testar PostgreSQL
    echo -e "${YELLOW}=== Testando PostgreSQL ===${NC}"
    if nc -z localhost 5432 2>/dev/null; then
        echo -e "${GREEN}✅ Porta 5432 (PostgreSQL) está aberta${NC}"
    else
        echo -e "${RED}❌ Porta 5432 (PostgreSQL) não está acessível${NC}"
    fi
    echo ""

    # Testar API
    echo -e "${YELLOW}=== Testando API FastAPI ===${NC}"
    if nc -z localhost 8000 2>/dev/null; then
        echo -e "${GREEN}✅ Porta 8000 (API) está aberta${NC}"
        # Testar endpoint de saúde
        if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Endpoint /api/v1/health respondendo${NC}"
        else
            echo -e "${RED}❌ Endpoint /api/v1/health não responde${NC}"
        fi
    else
        echo -e "${RED}❌ Porta 8000 (API) não está acessível${NC}"
    fi
    echo ""

    # Testar outros serviços
    echo -e "${YELLOW}=== Testando outros serviços ===${NC}"
    services=("nginx:80" "grafana:3000" "prometheus:9090" "pgadmin:5050" "flower:5555")
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        if nc -z localhost $port 2>/dev/null; then
            echo -e "${GREEN}✅ $name (porta $port) está acessível${NC}"
        else
            echo -e "${RED}❌ $name (porta $port) não está acessível${NC}"
        fi
    done
}

# Função para iniciar todos os serviços
start_all() {
    echo -e "${BLUE}🚀 Iniciando todos os serviços Docker...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ Todos os serviços iniciados!${NC}"
}

# Função para parar todos os serviços
stop_all() {
    echo -e "${BLUE}🛑 Parando todos os serviços Docker...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Todos os serviços parados!${NC}"
}

# Função para reiniciar todos os serviços
restart_all() {
    echo -e "${BLUE}🔄 Reiniciando todos os serviços Docker...${NC}"
    docker-compose restart
    echo -e "${GREEN}✅ Todos os serviços reiniciados!${NC}"
}

# Função para mostrar logs
show_logs() {
    echo -e "${BLUE}📋 Mostrando logs dos serviços...${NC}"
    docker-compose logs -f
}

# Função para mostrar status
show_status() {
    echo -e "${BLUE}📊 Status dos serviços Docker:${NC}"
    docker-compose ps
}

# Verificar se foi passado um comando
if [ $# -eq 0 ]; then
    echo -e "${RED}Erro: Nenhum comando especificado${NC}"
    echo ""
    show_help
    exit 1
fi

# Processar o comando
case "$1" in
    "monitoring")
        start_monitoring
        ;;
    "test-redis")
        test_redis
        ;;
    "test-all")
        test_all
        ;;
    "start")
        start_all
        ;;
    "stop")
        stop_all
        ;;
    "restart")
        restart_all
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}Erro: Comando '$1' não reconhecido${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
