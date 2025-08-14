#!/bin/bash

# Configura a localidade pt_BR.UTF-8
echo "Configurando localidade pt_BR.UTF-8..."
apt-get update && apt-get install -y locales
echo "pt_BR.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen pt_BR.UTF-8
update-locale LANG=pt_BR.UTF-8
export LC_ALL=pt_BR.UTF-8

# Instala as dependências Python
echo "Atualizando pip e instalando dependências..."
pip install --upgrade pip
pip install -r requirements-$SERVICE.txt

# Verifica se a instalação foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "Dependências instaladas com sucesso."
else
    echo "Erro ao instalar dependências." >&2
    exit 1
fi