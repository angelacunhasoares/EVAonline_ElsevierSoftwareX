# 🧪 Guia de Testes - EVAonline

Este documento explica como usar as extensões de teste instaladas no VS Code para facilitar o desenvolvimento e execução dos testes.

## 📦 Extensões Instaladas

### 1. **Python Test Explorer** (`littlefoxteam.vscode-python-test-adapter`)
Interface visual para explorar e executar testes pytest no painel lateral do VS Code.

### 2. **Pytest IntelliSense** (`cameron.vscode-pytest`)
Autocompletar inteligente para fixtures e funções do pytest.

## 🚀 Como Usar

### **Test Explorer (Painel Lateral)**

1. Abra o **Test Explorer** no painel lateral (ícone de proveta)
2. Você verá todos os testes organizados por arquivo
3. Clique nos botões para:
   - ▶️ Executar todos os testes
   - ▶️ Executar teste específico
   - 🔄 Recarregar testes
   - 📊 Ver cobertura

### **IntelliSense para Pytest**

- **Autocompletar fixtures**: Digite o nome de uma fixture e pressione Ctrl+Espaço
- **Navegação**: Clique com Ctrl em uma fixture para ir à sua definição
- **Sugestões**: O IntelliSense sugere fixtures disponíveis automaticamente

### **Atalhos Úteis**

- `Ctrl+Shift+P` → "Python: Run All Tests"
- `Ctrl+Shift+P` → "Python: Run Test File"
- `Ctrl+Shift+P` → "Python: Debug Test"

### **Debug de Testes**

1. Clique com o botão direito em um teste
2. Selecione "Debug Test"
3. Use breakpoints normais do Python

## 📋 Configurações Aplicadas

### **settings.json**
- Testes pytest habilitados
- Diretório de trabalho: `backend/`
- Ambiente virtual configurado
- Decorações visuais nos testes
- Linting e formatação automáticos

### **pytest.ini**
- Cobertura de código habilitada
- Relatórios HTML de cobertura
- Marcadores personalizados (unit, integration, api, slow)
- Warnings desabilitados

### **launch.json**
- Configurações de debug para testes
- Execução com coverage
- Teste de arquivo específico

### **tasks.json**
- Tarefas para executar testes via Command Palette
- Testes com coverage
- Testes por categoria (API, unitários)

## 🎯 Funcionalidades Avançadas

### **Marcadores de Teste**
```python
@pytest.mark.unit
def test_example():
    pass

@pytest.mark.integration
def test_database():
    pass

@pytest.mark.api
def test_openmeteo_api():
    pass

@pytest.mark.slow
def test_performance():
    pass
```

### **Execução por Marcador**
```bash
# Apenas testes unitários
pytest -m unit

# Apenas testes de API
pytest -m api

# Testes lentos
pytest -m slow
```

### **Cobertura de Código**
- Relatório HTML: `backend/htmlcov/index.html`
- Relatório no terminal com `--cov-report=term-missing`
- Cobertura mínima exigida: 80%

## 🔧 Troubleshooting

### **Testes não aparecem no Test Explorer**
1. Verifique se o Python Interpreter está correto
2. Recarregue a janela do VS Code (Ctrl+Shift+P → "Developer: Reload Window")
3. Execute `pytest --collect-only` no terminal para verificar

### **IntelliSense não funciona**
1. Certifique-se de que o arquivo está dentro do diretório `backend/`
2. Verifique se o `PYTHONPATH` está configurado corretamente
3. Recarregue o IntelliSense (Ctrl+Shift+P → "Python: Reload IntelliSense")

### **Problemas de Import**
- Certifique-se de que o ambiente virtual está ativado
- Verifique se todas as dependências estão instaladas
- Execute `pip install -r requirements.txt`

## 📊 Relatórios

### **Cobertura de Código**
```bash
# Gerar relatório HTML
pytest --cov=backend --cov-report=html

# Abrir relatório
start backend/htmlcov/index.html
```

### **Relatório Detalhado**
```bash
# Com informações detalhadas
pytest -v --tb=long --cov=backend --cov-report=term-missing
```

## 🎉 Dicas

- Use `pytest-watch` para execução automática durante desenvolvimento
- Configure git hooks para executar testes antes de commits
- Use `pytest-xdist` para execução paralela em múltiplos núcleos
- Configure CI/CD para executar testes automaticamente

---

**Precisa de ajuda?** Consulte a documentação das extensões ou abra uma issue no repositório.
