# 🔧 Configuração Manual da Extensão Redis

## Método 1: Configuração via Interface (Recomendado)

1. **Abra a extensão Redis** no VS Code (ícone do Redis na barra lateral)
2. **Clique no botão "+"** para adicionar uma nova conexão
3. **Preencha os campos:**

### Campos obrigatórios:
- **Name:** `EVAonline Redis (Docker)`
- **Host:** `localhost`
- **Port:** `6379`
- **Password:** `evaonline`

### Campos opcionais:
- **Database:** `0`
- **Timeout:** `5000`
- **Username:** (deixe vazio)

4. **Clique em "Test Connection"** para verificar
5. **Clique em "Save"** para salvar

## Método 2: Verificação da Configuração

Se a configuração automática não funcionar:

1. Abra **Command Palette** (`Ctrl+Shift+P`)
2. Digite: `Preferences: Open Settings (JSON)`
3. Verifique se existe esta seção:

```json
"redis-for-vscode.connections": [
    {
        "name": "EVAonline Redis (Docker)",
        "host": "localhost",
        "port": 6379,
        "password": "evaonline",
        "database": 0,
        "timeout": 10000,
        "username": "",
        "autoConnect": false
    }
]
```

## Método 3: Reset da Extensão

Se ainda não funcionar:

1. Feche o VS Code
2. Abra o VS Code
3. Vá em **Extensions** (Ctrl+Shift+X)
4. Encontre **Redis for VS Code**
5. Clique no **engrenagem** > **Disable**
6. Clique no **engrenagem** > **Enable**

## 🔍 Verificação de Conectividade

Execute este comando no terminal para confirmar que o Redis está acessível:

```bash
# Teste básico
Test-NetConnection -ComputerName localhost -Port 6379

# Teste com autenticação
docker exec evaonline-redis redis-cli -a evaonline ping
```

**Resultado esperado:** `PONG`

## 🐛 Possíveis Problemas

### Problema: "Authentication failed"
**Solução:** Verifique se a senha está exatamente como `evaonline`

### Problema: "Connection refused"
**Solução:** Certifique-se de que o Redis está rodando:
```bash
docker-compose ps redis
```

### Problema: "Connection timeout"
**Solução:** Aumente o timeout nas configurações para 10000ms

### Problema: Extensão não carrega configurações
**Solução:** Recarregue a janela do VS Code (`Ctrl+Shift+P` > "Developer: Reload Window")

## 📋 Configurações Finais

Após configurar corretamente, você deve ver:
- ✅ Conexão estabelecida
- ✅ Lista de databases
- ✅ Interface para executar comandos
- ✅ Visualização de chaves e valores

## 💡 Dica

Se a extensão pedir **username**, deixe o campo vazio. O Redis neste projeto usa apenas autenticação por senha.
