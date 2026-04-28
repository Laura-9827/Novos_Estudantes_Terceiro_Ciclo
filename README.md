# Dashboard dos Novos Estudantes de 3.º Ciclo

Aplicação Streamlit para explorar os resultados do inquérito aos novos estudantes do 3.º ciclo de 2025/2026.

## Como executar

1. Instalar dependências:

```bash
pip install -r requirements.txt
```

2. Iniciar o dashboard:

```bash
streamlit run app.py
```

No dashboard, a navegação principal é feita no topo com dois seletores em cascata:

- primeiro escolhe-se a Escola
- depois escolhe-se o Curso dessa Escola

Ao selecionar uma escola, os gráficos passam a refletir apenas os dados dessa escola. Ao selecionar um curso, o painel reduz-se a esse curso.

## Ficheiros principais

- `app.py`: dashboard principal
- `Cópia_bd_selo.XLS`: base de respostas
- `Inquérito aos Novos Alunos do 3ºCiclo (25-26) - Versão Final_21-04-2025.docx`: guião do questionário
