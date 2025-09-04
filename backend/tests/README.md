# Backend Tests

Este diretório contém os testes automatizados para os serviços backend do EVAonline.

## Estrutura dos Testes

```
backend/tests/
├── test_openmeteo.py          # Testes para OpenMeteo API
├── pytest.ini                 # Configuração do pytest
└── README.md                  # Este arquivo
```

## Instalação de Dependências de Teste

```bash
pip install pytest pytest-cov pytest-mock requests-mock
```

## Executando os Testes

### Todos os Testes
```bash
# Do diretório backend/
pytest

# Ou com mais detalhes
pytest -v
```

### Testes Específicos
```bash
# Apenas testes do OpenMeteo
pytest tests/test_openmeteo.py -v

# Apenas testes de inicialização
pytest tests/test_openmeteo.py::TestOpenMeteoForecastAPI::TestInitialization -v

# Apenas testes de cache
pytest tests/test_openmeteo.py::TestOpenMeteoForecastAPI::TestCaching -v
```

### Com Cobertura de Código
```bash
# Relatório de cobertura no terminal
pytest --cov=backend --cov-report=term-missing

# Relatório HTML de cobertura
pytest --cov=backend --cov-report=html
# Abre coverage_html/index.html no navegador
```

### Testes por Tipo
```bash
# Testes unitários
pytest -m unit

# Testes de integração
pytest -m integration

# Testes lentos
pytest -m slow
```

## Tipos de Teste Implementados

### 1. Testes de Inicialização
- ✅ Inicialização válida com parâmetros corretos
- ✅ Validação de latitude/longitude inválidas
- ✅ Validação de intervalo de datas (máx. 14 dias)

### 2. Testes de Construção de URL
- ✅ URL correta com todos os parâmetros
- ✅ Parâmetros horários obrigatórios incluídos
- ✅ Modelo correto (best_match)

### 3. Testes de Chamada da API
- ✅ Chamada bem-sucedida
- ✅ Tratamento de timeout
- ✅ Tratamento de erros HTTP
- ✅ Tratamento de resposta JSON inválida

### 4. Testes de Processamento de Dados
- ✅ Processamento bem-sucedido em DataFrame
- ✅ Tratamento de campos ausentes
- ✅ Conversão de unidades (vento m/s → km/h)
- ✅ Validação de dados

### 5. Testes de Cache
- ✅ Inicialização do Redis
- ✅ Falha na conexão do Redis
- ✅ Operações sem Redis disponível
- ✅ Cache hit/miss

### 6. Testes de Tratamento de Erros
- ✅ Recuperação de erros de rede
- ✅ Respostas vazias/inválidas
- ✅ Campos obrigatórios ausentes

### 7. Testes de Integração
- ✅ Workflow completo (API → DataFrame)
- ✅ Cache integrado com API
- ✅ Validações end-to-end

## Cobertura de Cenários

### Cenários de Sucesso
- ✅ Dados completos da API
- ✅ Cache funcionando
- ✅ Todos os campos presentes

### Cenários de Erro
- ✅ Rede indisponível
- ✅ API retorna erro HTTP
- ✅ JSON malformado
- ✅ Campos obrigatórios ausentes
- ✅ Redis indisponível

### Cenários de Validação
- ✅ Coordenadas geográficas inválidas
- ✅ Intervalo de datas muito longo
- ✅ Parâmetros fora dos ranges válidos

## Estrutura dos Testes

Os testes seguem o padrão AAA (Arrange, Act, Assert):

```python
def test_example(self):
    # Arrange: Preparar dados e mocks
    ...

    # Act: Executar a ação
    result = function_under_test()

    # Assert: Verificar resultado
    assert result == expected_value
```

## Mocks Utilizados

### API Responses
- Mock de respostas bem-sucedidas
- Mock de respostas com campos ausentes
- Mock de respostas vazias

### Redis Cache
- Mock de conexão bem-sucedida
- Mock de falha na conexão
- Mock de operações get/set

### HTTP Requests
- Mock de requests.get()
- Mock de timeouts
- Mock de HTTP errors

## Executando Testes em Desenvolvimento

### Durante Desenvolvimento
```bash
# Executar testes automaticamente ao salvar
pytest-watch

# Ou com pytest-xdist para paralelização
pytest -n auto
```

### CI/CD
```bash
# Para integração contínua
pytest --junitxml=reports/junit.xml --cov-report=xml
```

## Relatórios de Teste

### Cobertura de Código
- Relatório HTML: `htmlcov/index.html`
- Relatório XML: Para CI/CD

### Resultados dos Testes
- JUnit XML: Para integração com ferramentas CI/CD
- Resultados detalhados no terminal

## Boas Práticas Implementadas

1. **Isolamento**: Cada teste é independente
2. **Fixtures**: Reutilização de dados de teste
3. **Mocks**: Isolamento de dependências externas
4. **Parametrização**: Múltiplos cenários em um teste
5. **Nomenclatura**: Nomes descritivos e consistentes
6. **Documentação**: Docstrings em português
7. **Cobertura**: Testes abrangentes de cenários

## Próximos Passos

- [ ] Adicionar testes para outros módulos
- [ ] Implementar testes de performance
- [ ] Adicionar testes de carga
- [ ] Integrar com GitHub Actions
- [ ] Adicionar testes de mutação (mutmut)

---

**Nota**: Os testes foram criados seguindo as melhores práticas de testing em Python, com foco em cenários reais de uso do EVAonline.
