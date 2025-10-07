# ✅ Checklist de Testes Visuais - EVAonline

**Data**: 7 de Outubro de 2025  
**URL**: http://127.0.0.1:8050

---

## 🌐 1. TESTES NO CHROME/EDGE

### 🏠 Página Home (`/`)

#### Navbar
- [ ] Logo ESALQ aparece corretamente (50px altura)
- [ ] Título "EVAonline" em branco e visível
- [ ] Links da navbar em branco
- [ ] Hover nos links (fundo verde claro transparente)
- [ ] Botão de idioma com borda branca
- [ ] Navbar responsiva (colapsa em mobile)

#### Mapa
- [ ] Mapa carrega corretamente
- [ ] Clique no mapa mostra lat/long/altitude
- [ ] Marker aparece ao clicar
- [ ] Zoom funciona

#### Seção de Informações
- [ ] Ícones FontAwesome aparecem
- [ ] Fonte de 13px legível
- [ ] Cores corretas (vermelho, azul, amarelo)

#### Botões de Ação Rápida
- [ ] Botão de geolocalização (ícone apenas)
- [ ] Botão de calcular ETo
- [ ] Botão de visualizar gráficos
- [ ] Tamanho fixo 36x31px
- [ ] Hover eleva o botão (sombra)

#### Accordion "Como usar o mapa"
- [ ] Inicia colapsado
- [ ] Expande ao clicar
- [ ] Fundo verde ESALQ claro quando expandido
- [ ] Ícones visíveis
- [ ] Fonte 14px legível

#### Accordion "Favoritos"
- [ ] Inicia colapsado
- [ ] Expande ao clicar
- [ ] Fundo verde ESALQ claro quando expandido
- [ ] Dropdown de paginação (5/10/20)
- [ ] Botões prev/next funcionam
- [ ] Botão "Limpar Tudo" aparece
- [ ] Modal de confirmação abre

#### Footer
- [ ] Logos de parceiros aparecem
- [ ] Logos em grayscale (30%)
- [ ] Hover nos logos (escala 1.1, cor total)
- [ ] Emails dos desenvolvedores visíveis
- [ ] Links de email funcionam
- [ ] Copyright aparece

---

### 📊 Página ETo Calculator (`/eto`)

- [ ] Título "ETo Calculator" centralizado
- [ ] Descrição legível
- [ ] Campos de data aparecem
- [ ] Botão "Calcular ETo" em verde ESALQ
- [ ] Hover no botão (verde claro)
- [ ] Favoritos carregam (localStorage compartilhado)
- [ ] Navbar e Footer consistentes

---

### ℹ️ Página About (`/about`)

- [ ] Conteúdo carrega
- [ ] Navbar e Footer consistentes
- [ ] Cores ESALQ aplicadas

---

### 📚 Página Documentation (`/documentation`)

- [ ] Conteúdo carrega
- [ ] Navbar e Footer consistentes
- [ ] Cores ESALQ aplicadas

---

## 🦊 2. TESTES NO FIREFOX

### Repetir todos os testes acima
- [ ] Navbar
- [ ] Cores ESALQ
- [ ] Botões
- [ ] Accordion
- [ ] Footer
- [ ] Responsividade

### Específico do Firefox:
- [ ] Scrollbar customizado aparece (verde ESALQ)
- [ ] Transições suaves
- [ ] Font Awesome carrega

---

## 🧭 3. TESTES NO SAFARI (se disponível)

### Repetir todos os testes
- [ ] Variáveis CSS funcionam
- [ ] Cores ESALQ corretas
- [ ] Transições suaves

---

## 📱 4. TESTES DE RESPONSIVIDADE

### Desktop (>1200px)
- [ ] Logo ESALQ visível
- [ ] Layout horizontal correto
- [ ] Mapa ocupa 70% da largura
- [ ] Sidebar de informações 30%

### Tablet (768px - 1199px)
- [ ] Logo ESALQ visível
- [ ] Layout adaptado
- [ ] Navbar colapsa

### Mobile (<767px)
- [ ] Logo ESALQ oculto
- [ ] Navbar toggler aparece
- [ ] Menu hambúrguer funciona
- [ ] Layout vertical
- [ ] Botões acessíveis
- [ ] Footer responsivo

---

## 🎨 5. TESTES DE CORES

### Verde ESALQ Escuro (#2d5016)
- [ ] Navbar background
- [ ] Botões primários
- [ ] Links (não-navbar)
- [ ] Títulos de seção no footer
- [ ] Ícones ESALQ

### Verde ESALQ Claro (#4a7c2c)
- [ ] Hover em botões
- [ ] Hover em links

### Verde ESALQ Background (#f0f4ed)
- [ ] Accordion expandido
- [ ] Fundo suave em seções

### Cores do Sistema
- [ ] Vermelho (#dc3545) - Ícone de geolocalização
- [ ] Azul (#0d6efd) - Ícone de clique no mapa
- [ ] Amarelo (#ffc107) - Ícone de favoritos

---

## ⚡ 6. TESTES DE PERFORMANCE

### DevTools (F12)
- [ ] CSS carrega em <100ms
- [ ] Sem erros 404 no console
- [ ] Sem warnings de CSS
- [ ] FontAwesome carrega (6.4.0)

### Network Tab
- [ ] `styles.css` cacheado após primeiro carregamento
- [ ] Tamanho ~8 KB (não-minificado) ou ~3 KB (minificado)

---

## 🔍 7. TESTES DE ACESSIBILIDADE

### Contraste de Cores
- [ ] Navbar (branco sobre verde) - WCAG AAA
- [ ] Botões (branco sobre verde) - WCAG AAA
- [ ] Texto principal legível

### Navegação por Teclado
- [ ] Tab percorre links da navbar
- [ ] Enter ativa botões
- [ ] Escape fecha modais

---

## 🐛 8. TESTES DE BUGS CONHECIDOS (Regressão)

### Bugs Anteriormente Corrigidos
- [ ] Botão de geolocalização não desaparece em erro ✅
- [ ] 21º favorito não sobrescreve ✅
- [ ] Botões não mudam de tamanho ao adicionar texto ✅
- [ ] Navegação entre páginas não causa erro ✅
- [ ] Paginação não causa erro com uma página ✅
- [ ] Título "EVAonline" não desaparece ✅

---

## 📝 NOTAS DE TESTE

**Navegador:** ___________________  
**Versão:** ___________________  
**Data:** ___________________

### Problemas Encontrados:
```
1. ________________________________
2. ________________________________
3. ________________________________
```

### Observações:
```
__________________________________________
__________________________________________
__________________________________________
```

---

## ✅ APROVAÇÃO FINAL

- [ ] Todos os testes passaram
- [ ] Sem erros críticos
- [ ] Performance aceitável
- [ ] Responsividade OK
- [ ] Cores ESALQ corretas

**Assinatura:** ___________________  
**Data:** ___________________

---

## 🚀 PRÓXIMOS PASSOS

Após aprovação dos testes:

1. [ ] Trocar para `styles.min.css` em produção
2. [ ] Fazer commit das mudanças
3. [ ] Atualizar README com link para documentação CSS
4. [ ] Considerar refatoração opcional (HOME.PY)
5. [ ] Considerar adicionar tema escuro no futuro

---

**Gerado em**: 2025-10-07  
**Versão**: 1.0
