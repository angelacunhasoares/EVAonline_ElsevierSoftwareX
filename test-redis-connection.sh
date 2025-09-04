#!/bin/bash
# Script para testar conexão Redis

echo "🔍 Testando conexão com Redis..."
echo ""

# Teste básico
echo "1. Teste de conectividade (porta 6379):"
if nc -z localhost 6379 2>/dev/null; then
    echo "✅ Porta 6379 está aberta"
else
    echo "❌ Porta 6379 não está acessível"
fi

echo ""
echo "2. Teste de autenticação Redis:"
if docker exec evaonline-redis redis-cli -a evaonline ping 2>/dev/null | grep -q "PONG"; then
    echo "✅ Autenticação Redis funcionando"
else
    echo "❌ Falha na autenticação Redis"
fi

echo ""
echo "3. Informações do servidor Redis:"
docker exec evaonline-redis redis-cli -a evaonline info server 2>/dev/null | head -5

echo ""
echo "4. Chaves armazenadas:"
docker exec evaonline-redis redis-cli -a evaonline dbsize 2>/dev/null

echo ""
echo "📋 Instruções para VS Code:"
echo "- Abra Command Palette (Ctrl+Shift+P)"
echo "- Digite: 'Redis: Connect'"
echo "- Selecione: 'EVAonline Redis (Docker)'"
echo "- A conexão deve funcionar automaticamente"
