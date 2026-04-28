#!/bin/bash

# Configurar git localmente
git config user.email "Laura@example.com"
git config user.name "Laura"

# Adicionar todos os arquivos
git add .

# Fazer commit
git commit -m "Initial commit: Dashboard Streamlit para análise de estudantes de doutoramento"

# Adicionar remote
git remote add origin https://github.com/Laura-9827/Novos_Estudantes_Terceiro_Ciclo.git

# Renomear branch para main
git branch -M main

# Push para o repositório
git push -u origin main

echo "Projeto publicado com sucesso!"
