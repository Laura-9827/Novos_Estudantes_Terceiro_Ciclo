# Script para publicar o projeto no GitHub

# Configurar git
git config user.email "Laura@example.com"
git config user.name "Laura"

# Adicionar e fazer commit
git add .
git commit -m "Initial commit: Dashboard Streamlit para análise de estudantes de doutoramento"

# Adicionar remote
git remote add origin https://github.com/Laura-9827/Novos_Estudantes_Terceiro_Ciclo.git

# Renomear branch para main
git branch -M main

# Push
git push -u origin main

Write-Host "Projeto publicado com sucesso!"
