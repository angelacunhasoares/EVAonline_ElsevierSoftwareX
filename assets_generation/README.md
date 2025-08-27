# Assets Generation Scripts

Esta pasta contém scripts utilizados para gerar assets estáticos para o EVAonline.

## Estrutura

- `maps/`: Scripts para geração de mapas estáticos
  - `matopiba_map.py`: Gera o mapa estático da região do MATOPIBA

## Como usar

Os scripts nesta pasta são ferramentas auxiliares que geram assets estáticos para o EVAonline. Os assets gerados são salvos na pasta `assets/` do projeto.

### Gerando mapas

1. Para gerar o mapa do MATOPIBA:
   ```bash
   python maps/matopiba_map.py
   ```
   O mapa será salvo em `../../frontend/assets/images/matopiba.png`

Estrutura de diretórios:
```
EVAonline_ElsevierSoftwareX/
├── frontend/
│   └── assets/
│       └── images/          # Todos os assets de imagem do projeto
│           ├── logo_c4ai.png
│           ├── logo_esalq.png
│           └── matopiba.png # Mapa gerado pelo script
├── assets_generation/
│   └── maps/           
│       └── matopiba_map.py  # Script gerador
```

O script deve ser configurado para salvar o mapa na pasta `frontend/assets/images/`, onde ficam todas as imagens do projeto EVAonline.

## Observações

- Estes scripts não são parte do funcionamento do software EVAonline
- São utilizados apenas para gerar assets estáticos que serão incluídos no projeto
- Podem ter dependências adicionais não necessárias para o EVAonline
