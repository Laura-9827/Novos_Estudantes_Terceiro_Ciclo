# Dashboard dos Novos Estudantes de 3.º Ciclo

Aplicação Streamlit para explorar os resultados do inquérito aos novos estudantes do 3.º ciclo de 2025/2026.

O código foi separado em módulos: `app.py` funciona como ponto de entrada, `src/services/` concentra a lógica de dados e regras, `src/config/` guarda mapeamentos e parâmetros, e `src/viz/` trata da aparência.

Há também uma camada ETL leve em `src/etl/` que lê o ficheiro bruto em `data/raw/` e gera `data/processed/dashboard_data.csv`. O dashboard passa a consumir esse ficheiro tratado.

## Como executar

1. Instalar dependências:

```bash
pip install -r requirements.txt
```

2. Iniciar o dashboard:

```bash
streamlit run app.py
```

Se quiseres regenerar o ficheiro tratado manualmente:

```bash
python tools/build_processed_data.py
```

No dashboard, a navegação principal é feita no topo com dois seletores em cascata:

- primeiro escolhe-se a Escola
- depois escolhe-se o Curso dessa Escola

Ao selecionar uma escola, os gráficos passam a refletir apenas os dados dessa escola. Ao selecionar um curso, o painel reduz-se a esse curso.

## Ficheiros principais

- `app.py`: ponto de entrada do dashboard
- `src/etl/`: extração, transformação e geração do ficheiro tratado
- `src/config/`: constantes e mapeamentos
- `src/services/`: leitura, filtros, métricas e perfis
- `src/viz/`: tema e layout
- `data/raw/Cópia_bd_selo.XLS`: entrada oficial do ETL
- `data/processed/dashboard_data.csv`: dataset preparado para o dashboard
- `Inquérito aos Novos Alunos do 3ºCiclo (25-26) - Versão Final_21-04-2025.docx`: guião do questionário
