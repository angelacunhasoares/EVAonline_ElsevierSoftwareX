#!/bin/bash

# Instalar dependências do sistema
apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/*

# Configurar localidade
echo "pt_BR.UTF-8 UTF-8" > /etc/locale.gen
locale-gen pt_BR.UTF-8
update-locale LANG=pt_BR.UTF-8

# Instalar dependências Python
pip install --no-cache-dir -r requirements.txt