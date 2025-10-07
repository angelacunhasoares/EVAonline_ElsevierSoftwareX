# 🎨 EVAonline CSS Design System

## 📋 Índice
- [Introdução](#introdução)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Variáveis CSS](#variáveis-css)
- [Utility Classes](#utility-classes)
- [Componentes](#componentes)
- [Boas Práticas](#boas-práticas)
- [Guia de Uso](#guia-de-uso)

---

## 🎯 Introdução

Este documento descreve o **Design System** do EVAonline, baseado nas cores institucionais da ESALQ/USP. Todo o CSS foi organizado em um arquivo externo (`styles.css`) seguindo as melhores práticas de separação de responsabilidades.

### ✅ Benefícios
- **Manutenibilidade**: Estilos centralizados
- **Performance**: CSS cacheado pelo navegador
- **Consistência**: Uso de variáveis CSS
- **Reusabilidade**: Utility classes padronizadas
- **Produção**: Versão minificada disponível

---

## 📁 Estrutura de Arquivos

```
frontend/
└── assets/
    └── styles/
        ├── styles.css       # ⭐ Versão para desenvolvimento (comentada)
        └── styles.min.css   # 🚀 Versão para produção (minificada)
```

### Como usar em desenvolvimento:
```python
# app.py já carrega automaticamente styles.css
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
```

### Como usar em produção:
Altere o link no `app.py` para:
```python
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    '/assets/styles/styles.min.css'
                ])
```

---

## 🎨 Variáveis CSS

Todas as cores, tamanhos e espaçamentos são definidos como variáveis CSS no `:root`:

### 🟢 Cores ESALQ
```css
--esalq-green-dark: #2d5016;   /* Verde ESALQ principal */
--esalq-green-light: #4a7c2c;  /* Verde ESALQ claro (hover) */
--esalq-green-bg: #f0f4ed;     /* Fundo verde suave */
```

### 🎨 Cores do Sistema
```css
--color-danger: #dc3545;       /* Vermelho (erros) */
--color-info: #0d6efd;         /* Azul (informação) */
--color-warning: #ffc107;      /* Amarelo (avisos) */
--color-muted: #6c757d;        /* Cinza (texto secundário) */
--color-border: #dee2e6;       /* Cinza claro (bordas) */
```

### 📏 Tipografia
```css
--font-size-xs: 11px;          /* Extra pequeno */
--font-size-sm: 12px;          /* Pequeno */
--font-size-base: 13px;        /* Base */
--font-size-md: 14px;          /* Médio */
--font-size-lg: 16px;          /* Grande */
```

### 📐 Espaçamento
```css
--spacing-xs: 0.25rem;         /* 4px */
--spacing-sm: 0.5rem;          /* 8px */
--spacing-md: 1rem;            /* 16px */
--spacing-lg: 1.5rem;          /* 24px */
```

### 🌊 Sombras
```css
--shadow-sm: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
--shadow-md: 0 2px 4px rgba(0, 0, 0, 0.1);
--shadow-hover: 0 2px 4px rgba(0, 0, 0, 0.2);
```

### ⏱️ Transições
```css
--transition-fast: all 0.2s ease;
--transition-normal: all 0.3s ease;
```

---

## 🛠️ Utility Classes

### Tipografia

| Classe | Tamanho | Uso |
|--------|---------|-----|
| `.text-xs` | 11px | Labels muito pequenos |
| `.text-sm` | 12px | Labels e legendas |
| `.text-md` | 14px | Texto padrão |
| `.text-lg` | 16px | Títulos |

**Exemplo:**
```python
html.Span("Texto pequeno", className="text-sm")
html.H5("Título", className="text-lg")
```

### Cores ESALQ

| Classe | Cor | Uso |
|--------|-----|-----|
| `.text-esalq` | Verde escuro | Texto principal ESALQ |
| `.text-esalq-light` | Verde claro | Hover, destaques |
| `.bg-esalq-light` | Fundo verde | Backgrounds suaves |

**Exemplo:**
```python
html.H5("Título ESALQ", className="text-esalq")
html.Div(className="bg-esalq-light p-3")
```

### Cores do Sistema

| Classe | Cor | Uso |
|--------|-----|-----|
| `.text-danger-custom` | Vermelho | Erros |
| `.text-info-custom` | Azul | Informações |
| `.text-warning-custom` | Amarelo | Avisos |

### Ícones

| Classe | Tamanho | Uso |
|--------|---------|-----|
| `.icon-xs` | 12px | Ícones inline |
| `.icon-sm` | 14px | Ícones em botões |
| `.icon-md` | 16px | Ícones em títulos |

**Exemplo:**
```python
html.I(className="fas fa-star icon-sm text-warning-custom")
```

### Utilitários

| Classe | Efeito | Uso |
|--------|--------|-----|
| `.smooth-transition` | Transição suave 0.3s | Animações |
| `.card-shadow-sm` | Sombra sutil | Cards |
| `.section-title` | Título de seção ESALQ | H5 padronizado |

---

## 🧩 Componentes

### Navbar
- **Classe**: `.nav-link-custom`
- **Cor**: Branco sobre verde ESALQ
- **Hover**: Fundo verde claro transparente

**Exemplo:**
```python
dbc.NavLink("Link", className="nav-link-custom")
```

### Footer
- **Classe**: `.partner-logo` (para logos)
- **Classe**: `.partner-logo-img` (para tags <img>)
- **Classe**: `.email-link` (para links de email)
- **Classe**: `.section-title` (para títulos)

**Exemplo:**
```python
html.H5("Parceiros", className="section-title")
html.Img(src="logo.png", className="partner-logo-img")
html.A("email@example.com", className="email-link")
```

### Accordion
- **Expandido**: Fundo verde ESALQ claro
- **Focus**: Borda verde
- **Fonte**: 14px

**Uso automático** com `dbc.Accordion`

### Botões de Ação Rápida
- **Classe**: `.quick-action-btn`
- **Tamanho fixo**: 36x31px
- **Hover**: Elevação com sombra

**Exemplo:**
```python
dbc.Button(
    html.I(className="fas fa-location-arrow"),
    className="quick-action-btn",
    color="primary"
)
```

### Favoritos
- **Classe**: `.favorite-card-btn`
- **Fonte**: 11px
- **Scrollbar**: `.favorites-scroll`

**Exemplo:**
```python
html.Div(id="favorites-list", className="favorites-scroll")
```

---

## ✅ Boas Práticas

### ❌ **NÃO FAZER** (Inline CSS):
```python
# Ruim - style inline
html.Div("Texto", style={"fontSize": "12px", "color": "#2d5016"})
```

### ✅ **FAZER** (Classes CSS):
```python
# Bom - classes CSS
html.Div("Texto", className="text-sm text-esalq")
```

### ❌ **NÃO FAZER** (Hardcoded colors):
```python
# Ruim - cor hardcoded
style={"color": "#2d5016"}
```

### ✅ **FAZER** (Variáveis CSS via classes):
```python
# Bom - classe com variável CSS
className="text-esalq"
```

### ❌ **NÃO FAZER** (Styles redundantes):
```python
# Ruim - style já definido no CSS
className="nav-link-custom"
style={"color": "white"}  # Redundante!
```

### ✅ **FAZER** (Apenas classe):
```python
# Bom - CSS cuida de tudo
className="nav-link-custom"
```

---

## 📖 Guia de Uso

### Cenário 1: Adicionar novo título de seção

```python
# ❌ Antes (inline)
html.H5("Título", style={"fontSize": "16px", "fontWeight": "600", "color": "#2d5016"})

# ✅ Agora (classe)
html.H5("Título", className="section-title")
```

### Cenário 2: Adicionar texto com tamanho específico

```python
# ❌ Antes (inline)
html.Span("Texto", style={"fontSize": "12px"})

# ✅ Agora (classe)
html.Span("Texto", className="text-sm")
```

### Cenário 3: Adicionar ícone colorido

```python
# ❌ Antes (inline)
html.I(className="fas fa-star", style={"color": "#ffc107", "fontSize": "14px"})

# ✅ Agora (classes)
html.I(className="fas fa-star icon-sm text-warning-custom")
```

### Cenário 4: Adicionar link de email no footer

```python
# ❌ Antes (inline)
html.A(
    "email@example.com",
    href="mailto:email@example.com",
    style={"color": "#2d5016", "textDecoration": "none"}
)

# ✅ Agora (classe)
html.A(
    "email@example.com",
    href="mailto:email@example.com",
    className="email-link"
)
```

---

## 🎯 Checklist de Migração

Ao criar novos componentes, verifique:

- [ ] Evitei `style=` inline?
- [ ] Usei variáveis CSS via classes quando possível?
- [ ] Criei nova classe em `styles.css` se necessário?
- [ ] Documentei a nova classe neste guia?
- [ ] Testei em múltiplos navegadores?
- [ ] Atualizei `styles.min.css` para produção?

---

## 🚀 Performance

### Tamanhos de arquivo:
- **styles.css**: ~8 KB (desenvolvimento)
- **styles.min.css**: ~3 KB (produção)
- **Redução**: ~62%

### Bene Cross-Browser Support:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ⚠️ IE11 (variáveis CSS não suportadas)

---

## 📞 Suporte

Para adicionar novos estilos ou classes:
1. Edite `styles.css`
2. Minifique para `styles.min.css`
3. Documente neste guia
4. Teste em múltiplos navegadores

**Desenvolvido com ❤️ pela equipe ESALQ/USP**
