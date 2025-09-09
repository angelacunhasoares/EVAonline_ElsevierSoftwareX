# 🔧 Guia de Configuração - Extensão Redis for VS Code

## 📋 Pré-requisitos

1. **Extensão instalada:** `redis.redis-for-vscode`
2. **Redis rodando:** Container Docker do Redis deve estar ativo
3. **Configurações aplicadas:** Arquivo `.vscode/settings.json` atualizado

## 🚀 Como conectar ao Redis

### **Passo 1: Verificar se o Redis está rodando**
```bash
# Verificar status do container
docker-compose ps redis

# Ou testar conexão diretamente
docker exec evaonline-redis redis-cli -a evaonline ping
```

### **Passo 2: Abrir a extensão no VS Code**
1. Abra o **Command Palette** (`Ctrl+Shift+P`)
2. Digite: `Redis: Connect`
3. Selecione: **"EVAonline Redis (Docker)"**

### **Passo 3: Verificar conexão**
- A extensão deve mostrar uma conexão ativa
- Você deve ver databases e chaves disponíveis
- Status deve aparecer como "Connected"

## ⚙️ Configurações da Extensão

As seguintes configurações foram aplicadas automaticamente:

```json
{
    "redis-for-vscode.connections": [
        {
            "name": "EVAonline Redis (Docker)",
            "host": "localhost",
            "port": 6379,
            "password": "evaonline",
            "database": 0,
            "timeout": 5000,
            "showNamespace": true,
            "namespaceSeparator": ":",
            "autoConnect": false
        }
    ],
    "redis-for-vscode.scanLimit": 10000,
    "redis-for-vscode.showKeySize": true,
    "redis-for-vscode.showKeyType": true,
    "redis-for-vscode.confirmDelete": true,
    "redis-for-vscode.formatJson": true,
    "redis-for-vscode.connectionView": "tree"
}
```

## 🔍 Funcionalidades Disponíveis

### **Visualizar Dados**
- **Keys:** Explorar todas as chaves armazenadas
- **Types:** Ver tipos de dados (string, hash, list, set, zset)
- **Sizes:** Verificar tamanho dos valores
- **Namespaces:** Organizar chaves por prefixo

### **Operações Básicas**
- **GET/SET:** Operações com strings
- **HGET/HSET:** Operações com hashes
- **LPUSH/RPUSH:** Operações com listas
- **SADD/SREM:** Operações com sets
- **ZADD/ZREM:** Operações com sorted sets

### **Monitoramento**
- **Monitor:** Ver comandos em tempo real
- **Info:** Estatísticas do servidor Redis
- **Slowlog:** Comandos mais lentos

## 🐛 Solução de Problemas

### **Erro: "Connection refused"**
```bash
# Verificar se o container está rodando
docker-compose ps

# Reiniciar o Redis
docker-compose restart redis

# Verificar logs
docker-compose logs redis
```

### **Erro: "Authentication failed"**
- Verificar se a senha está correta: `evaonline`
- Testar conexão manual:
```bash
docker exec evaonline-redis redis-cli -a evaonline ping
```

### **Erro: "Connection timeout"**
- Aumentar o timeout nas configurações
- Verificar se a porta 6379 está livre
- Testar conectividade de rede

### **Extensão não carrega configurações**
1. Feche e reabra o VS Code
2. Recarregue a janela: `Ctrl+Shift+P` → "Developer: Reload Window"
3. Verifique se o arquivo `.vscode/settings.json` está correto

## 📊 Monitoramento em Tempo Real

### **Comandos Úteis**
```bash
# Ver todas as chaves
KEYS *

# Ver tipo de uma chave
TYPE minha_chave

# Ver informações do servidor
INFO

# Monitorar comandos
MONITOR
```

### **Namespaces Comuns no EVAonline**
- `cache:` - Dados de cache da aplicação
- `session:` - Sessões de usuário
- `celery:` - Tarefas do Celery
- `weather:` - Dados meteorológicos em cache

## 🔒 Segurança

- **Nunca commite** senhas em repositórios públicos
- **Use variáveis de ambiente** para senhas em produção
- **Configure firewalls** para restringir acesso ao Redis
- **Use TLS/SSL** em ambientes de produção

## 📚 Recursos Adicionais

- [Documentação Redis](https://redis.io/documentation)
- [Documentação da Extensão](https://marketplace.visualstudio.com/items?itemName=redis.redis-for-vscode)
- [Comandos Redis](https://redis.io/commands)

---

**Status:** ✅ Configurado e testado
**Última atualização:** 4 de setembro de 2025
