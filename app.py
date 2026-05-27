from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dashboard - Novos Estudantes 3.º Ciclo",
    page_icon="📊",
    layout="wide",
)


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "Cópia_bd_selo.XLS"
OPEN_ENDED_EXCLUSIONS = {
    "1-5",
    "1-7",
    "1-9",
    "1-12",
    "1-14",
    "1-16",
    "1-21",
    "1-23",
    "1-25",
    "1-27",
}
UNIVERSE_SIZE = 387
RESPONSE_RATE_NUMERATOR = 281


Q_111 = {
    1: "Carreira docente no ensino superior",
    2: "Trabalhar em investigação",
    3: "Progressão na carreira profissional",
    4: "Aprofundar conhecimentos numa área académica específica",
    5: "Aplicar conhecimentos no contexto profissional",
    6: "Realização pessoal",
    7: "Obter mais um grau académico",
    8: "Assegurar rendimento através de bolsa",
    9: "Formação numa área diferente da de origem",
    10: "Encorajamento do/a orientador/a ou coordenador/a",
    11: "Aumentar as possibilidades de obter emprego qualificado",
    12: "Outro",
}

Q_117 = {
    1: "Sim, integrado na atividade profissional",
    2: "Sim, integrado num projeto de investigação",
    3: "Não",
    4: "Ainda não defini o tema da tese",
}

Q_124 = {
    1: "Situação no emprego igual à atual",
    2: "Progressão de carreira/categoria profissional",
    3: "Funções mais ajustadas a um nível de qualificação mais elevado",
    4: "Atividade profissional mais relacionada com a área do doutoramento",
    5: "Outra situação",
}

Q_126 = {
    1: "Ensino Superior",
    2: "Administração Pública",
    3: "Empresa privada",
    4: "Instituição privada sem fins lucrativos",
    5: "Outro",
}

Q_12 = {1: "Sim", 2: "Não"}
Q_13 = {1: "Sim", 2: "Não"}
Q_14 = {
    1: "Sim",
    2: "Não, mas pondero vir a manifestar interesse",
    3: "Não pondero vir a manifestar interesse",
}
Q_18 = {
    1: "Ensino Superior",
    2: "Administração Pública",
    3: "Empresa privada",
    4: "Instituição privada sem fins lucrativos",
    5: "Outro setor",
}

DOUBLE_SCHOOL_COURSES = {
    "Doutoramento em Economia": ["EG", "ECSH"],
}


def read_data() -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE)
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def load_processed() -> pd.DataFrame:
    df = read_data()
    df["RESPONDENT_AGE"] = pd.to_numeric(df.get("RESPONDENT_AGE"), errors="coerce")
    df["ANO_CONCLUSAO_DA_HABILITACAO_ANTERIOR"] = pd.to_numeric(
        df.get("ANO_CONCLUSAO_DA_HABILITACAO_ANTERIOR"), errors="coerce"
    )
    df["NOTA_CONCLUSAO_HABILITACAO_ANTERIOR"] = pd.to_numeric(
        df.get("NOTA_CONCLUSAO_HABILITACAO_ANTERIOR"), errors="coerce"
    )
    return df


def eligible_questions(df: pd.DataFrame) -> list[str]:
    question_columns = [col for col in df.columns if col.startswith("1-")]
    eligible = [col for col in question_columns if col.split()[0] not in OPEN_ENDED_EXCLUSIONS and col not in OPEN_ENDED_EXCLUSIONS]
    return eligible


def eligible_mask(df: pd.DataFrame, minimum_ratio: float = 0.75) -> pd.Series:
    questions = eligible_questions(df)

    def answered(value) -> bool:
        if pd.isna(value):
            return False
        if isinstance(value, str):
            return bool(value.strip()) and value.strip().lower() not in {"nan", "none"}
        return True

    answered_counts = df[questions].apply(lambda column: column.map(answered)).sum(axis=1)
    return (answered_counts / len(questions)) >= minimum_ratio


def find_column(df: pd.DataFrame, prefix: str) -> str:
    exact = [col for col in df.columns if col == prefix]
    if exact:
        return exact[0]
    matches = [col for col in df.columns if col.startswith(prefix)]
    if matches:
        return matches[0]
    raise KeyError(prefix)


def split_codes(value) -> list[int]:
    if pd.isna(value):
        return []
    if isinstance(value, (int, float)) and not pd.isna(value):
        return [int(value)]
    text = str(value).strip()
    if not text:
        return []
    codes = []
    for token in text.replace(";", ",").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            codes.append(int(float(token)))
        except ValueError:
            continue
    return codes


def code_counts(series: pd.Series, mapping: dict[int, str]) -> pd.DataFrame:
    counts = {label: 0 for label in mapping.values()}
    for value in series:
        for code in split_codes(value):
            label = mapping.get(code)
            if label:
                counts[label] += 1
    result = pd.DataFrame({"Opção": list(counts.keys()), "Respostas": list(counts.values())})
    result = result[result["Respostas"] > 0].sort_values("Respostas", ascending=False)
    return result.reset_index(drop=True)


def mean_likert(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows = []
    for column in columns:
        values = pd.to_numeric(df[column], errors="coerce")
        values = values[values != 66]
        if values.count() == 0:
            continue
        label = column.split(" ")[0]
        rows.append({"Indicador": label, "Média": values.mean(), "N": int(values.count())})
    return pd.DataFrame(rows).sort_values("Média", ascending=True).reset_index(drop=True)


def format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def categorical_summary(series: pd.Series, drop_missing: bool = True, missing_label: str = "Sem resposta") -> pd.DataFrame:
    values = series.copy()
    if drop_missing:
        values = values.replace({"nan": pd.NA, "None": pd.NA}).dropna()
    else:
        values = values.replace({"nan": missing_label, "None": missing_label}).fillna(missing_label)

    counts = values.astype(str).value_counts(dropna=False).reset_index()
    counts.columns = ["Categoria", "Respostas"]
    total = counts["Respostas"].sum()
    counts["Percentagem"] = (counts["Respostas"] / total * 100).round(1) if total else 0
    return counts


def share_label(counts: pd.DataFrame, category: str) -> str:
    row = counts[counts["Categoria"].astype(str) == str(category)]
    if row.empty:
        return "-"
    return f"{int(row.iloc[0]['Respostas'])} ({row.iloc[0]['Percentagem']}%)"


def split_school_codes(value) -> list[str]:
    if pd.isna(value):
        return []
    return re.findall(r"\b[A-Z]{2,}\b", str(value))


def school_options(df: pd.DataFrame) -> list[str]:
    codes = []
    for _, row in df[["NOME_CURSO", "ESCOLAS_CURSO"]].dropna(subset=["NOME_CURSO"]).iterrows():
        codes.extend(schools_for_course(str(row["NOME_CURSO"]), row.get("ESCOLAS_CURSO")))
    return sorted({code for code in codes if code not in {"NA", "NAN"}})


def schools_for_course(course: str, raw_value: str | None) -> list[str]:
    if course in DOUBLE_SCHOOL_COURSES:
        return DOUBLE_SCHOOL_COURSES[course]
    if raw_value:
        schools = split_school_codes(raw_value)
        if schools:
            return schools
    return []


def course_options(df: pd.DataFrame, selected_school: str | None) -> list[str]:
    filtered = df
    if selected_school:
        filtered = filtered[filtered.apply(lambda row: selected_school in schools_for_course(str(row["NOME_CURSO"]), row.get("ESCOLAS_CURSO")), axis=1)]
    return sorted(filtered["NOME_CURSO"].dropna().astype(str).unique().tolist())


def filter_data(df: pd.DataFrame, selected_school: str | None, selected_course: str | None) -> pd.DataFrame:
    filtered = df.copy()
    if selected_school:
        filtered = filtered[filtered.apply(lambda row: selected_school in schools_for_course(str(row["NOME_CURSO"]), row.get("ESCOLAS_CURSO")), axis=1)]
    if selected_course:
        filtered = filtered[filtered["NOME_CURSO"].astype(str) == selected_course]
    return filtered


def apply_blue_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --brand: rgb(0, 0, 255);
            --brand-soft: rgba(0, 0, 255, 0.10);
            --brand-softer: rgba(0, 0, 255, 0.06);
            --ink: #0f172a;
            --muted: #475569;
            --card: #ffffff;
            --border: rgba(15, 23, 42, 0.08);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(0, 0, 255, 0.08), transparent 30%),
                linear-gradient(180deg, #f8fbff 0%, #ffffff 45%, #f6f9ff 100%);
            color: var(--ink);
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        .hero {
            padding: 1.4rem 1.5rem;
            border: 1px solid var(--border);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(0, 0, 255, 0.97), rgba(0, 0, 255, 0.78));
            color: white;
            box-shadow: 0 18px 40px rgba(0, 0, 255, 0.16);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.1;
        }
        .hero p {
            margin: 0.4rem 0 0;
            opacity: 0.92;
            max-width: 900px;
        }
        .section-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--ink);
            margin-bottom: 0.5rem;
        }
        div[data-baseweb="select"] > div {
            border-radius: 14px;
        }
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 0.8rem 0.9rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.75rem;
            line-height: 1.1;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.05rem;
            line-height: 1.05;
        }
        div[data-testid="stMetricValue"] svg {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_box(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


def render_charts(df: pd.DataFrame) -> None:
    top_metrics = st.columns(3)
    with top_metrics[0]:
        metric_box("Respostas válidas", f"{len(df)}")
    with top_metrics[1]:
        response_rate = RESPONSE_RATE_NUMERATOR / UNIVERSE_SIZE * 100
        metric_box("Taxa de resposta", format_percentage(response_rate), "281 respostas válidas no critério de 75% de preenchimento do questionário, sobre um total de 387 de novos estudantes de doutoramento")
    with top_metrics[2]:
        school_count = df["NOME_CURSO"].nunique()
        metric_box("Cursos representados", f"{school_count}")

    profile_blocks = profile_subsections(df)

    st.markdown('<div class="section-title">Perfil Sociodemográsfico Típico</div>', unsafe_allow_html=True)
    soc1, soc2, soc3 = st.columns(3)
    for col, (label, value) in zip([soc1, soc2, soc3], profile_blocks["sociodemográfico"]):
        with col:
            metric_box(label, value)

    st.markdown('<div class="section-title">Situação Profissional</div>', unsafe_allow_html=True)
    pro1, pro2 = st.columns(2)
    for col, (label, value) in zip([pro1, pro2], profile_blocks["profissional"]):
        with col:
            metric_box(label, value)

    tab1, tab2, tab3, tab4 = st.tabs(["Perfil", "Motivações", "Fatores", "Expectativas"])

    with tab1:
        left, right = st.columns(2)
        with left:
            gender_counts = categorical_summary(df["RESPONDENT_GENDER"], drop_missing=True)
            fig = px.pie(
                gender_counts,
                names="Categoria",
                values="Respostas",
                hole=0.42,
                color_discrete_sequence=["rgb(0,0,255)", "#6ea8fe", "#9ec5fe"],
                title="Distribuição por género",
            )
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                customdata=gender_counts[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{label}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), legend_title_text="", font=dict(size=12))
            st.plotly_chart(fig, width="stretch")

        with right:
            age_bins = [18, 24, 29, 34, 39, 44, 49, 59, 100]
            age_labels = ["18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-59", "60+"]
            age_bucket = pd.cut(df["RESPONDENT_AGE"], bins=age_bins, labels=age_labels, right=True, include_lowest=True)
            age_counts = age_bucket.value_counts().reindex(age_labels).fillna(0).reset_index()
            age_counts.columns = ["Escalão etário", "Respostas"]
            age_counts["Percentagem"] = age_counts["Respostas"] / age_counts["Respostas"].sum() * 100
            age_counts["PercentagemTexto"] = age_counts["Percentagem"].round(1)
            age_counts = age_counts.sort_values("Percentagem", ascending=True)
            age_counts["TextoPerc"] = age_counts["PercentagemTexto"].astype(str) + "%"
            age_fig = px.bar(
                age_counts,
                x="Percentagem",
                y="Escalão etário",
                text="TextoPerc",
                color="Percentagem",
                orientation="h",
                color_continuous_scale=["#dbeafe", "rgb(0,0,255)"],
                title="Distribuição por escalão etário",
            )
            age_fig.update_traces(
                textposition="outside",
                customdata=age_counts[["Respostas", "PercentagemTexto"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>",
            )
            age_fig.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                coloraxis_showscale=False,
                xaxis_title="",
                yaxis_title="",
                xaxis=dict(range=[0, 100]),
                font=dict(size=11),
            )
            st.plotly_chart(age_fig, width="stretch")

        st.markdown('<div class="section-title">Situação Profissional/Ocupacional</div>', unsafe_allow_html=True)
        prof_left, prof_right = st.columns(2)
        with prof_left:
            occupation_counts = categorical_summary(df["CONDICAO_PROFISSIONAL_ALUNO"], drop_missing=True)
            occupation_counts["TextoPerc"] = occupation_counts["Percentagem"].astype(str) + "%"
            fig = px.bar(
                occupation_counts,
                y="Categoria",
                x="Percentagem",
                orientation="h",
                text="TextoPerc",
                color="Percentagem",
                color_continuous_scale=["#dbeafe", "rgb(0,0,255)"],
                title="Distribuição por situação profissional",
            )
            fig.update_traces(
                textposition="outside",
                customdata=occupation_counts[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>"
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                coloraxis_showscale=False,
                xaxis_title="%",
                xaxis=dict(range=[0, 100]),
                yaxis_title="",
                font=dict(size=11),
            )
            st.plotly_chart(fig, width="stretch")

        with prof_right:
            sector_counts = code_counts(df[find_column(df, "1-8")], Q_18)
            sector_counts["TextoPerc"] = sector_counts["Respostas"].map(lambda value: f"{value:.1f}")
            fig = px.bar(
                sector_counts,
                y="Opção",
                x="Respostas",
                orientation="h",
                text="TextoPerc",
                color="Respostas",
                color_continuous_scale=["#dbeafe", "rgb(0,0,255)"],
                title="Distribuição por setor profissional",
            )
            fig.update_traces(
                textposition="outside",
                customdata=sector_counts[["Respostas"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<extra></extra>"
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                coloraxis_showscale=False,
                xaxis_title="Respostas",
                yaxis_title="",
                font=dict(size=11),
            )
            st.plotly_chart(fig, width="stretch")

        nationality_counts = categorical_summary(df["NACIONALIDADE_1"], drop_missing=True).head(10)
        nationality_fig = px.bar(
            nationality_counts,
            x="Percentagem",
            y="Categoria",
            orientation="h",
            color_discrete_sequence=["rgb(0,0,255)"],
            title="Principais nacionalidades",
        )
        nationality_fig.update_traces(
            text=nationality_counts["Percentagem"].map(lambda value: f"{value:.1f}%"),
            textposition="outside",
            customdata=nationality_counts[["Respostas", "Percentagem"]],
            hovertemplate="%{y}<br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>",
        )
        nationality_fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            xaxis_title="Percentagem",
            yaxis_title="",
            font=dict(size=11),
        )
        st.plotly_chart(nationality_fig, width="stretch")

        st.markdown('<div class="section-title">Aspetos do Doutoramento</div>', unsafe_allow_html=True)
        dout1, dout2, dout3 = st.columns(3)
        with dout1:
            q2_col = find_column(df, "1-2")
            q2_counts = code_counts(df[q2_col], Q_12)
            q2_total = q2_counts["Respostas"].sum()
            q2_counts["Percentagem"] = (q2_counts["Respostas"] / q2_total * 100).round(1)
            q2_counts["TextoPerc"] = q2_counts["Percentagem"].astype(str) + "%"
            fig = px.bar(
                q2_counts,
                x="Percentagem",
                y="Opção",
                orientation="h",
                text="TextoPerc",
                color="Percentagem",
                color_continuous_scale=["#dbeafe", "rgb(0,0,255)"],
                title="Vai iniciar logo a seguir?",
            )
            fig.update_traces(
                textposition="outside",
                customdata=q2_counts[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>"
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), yaxis_title="", coloraxis_showscale=False, xaxis=dict(range=[0, 100]), xaxis_title="%", font=dict(size=11))
            st.plotly_chart(fig, width="stretch")

        with dout2:
            q3_col = find_column(df, "1-3")
            q3_counts = code_counts(df[q3_col], Q_13)
            q3_total = q3_counts["Respostas"].sum()
            q3_counts["Percentagem"] = (q3_counts["Respostas"] / q3_total * 100).round(1)
            q3_counts["TextoPerc"] = q3_counts["Percentagem"].astype(str) + "%"
            fig = px.bar(
                q3_counts,
                x="Percentagem",
                y="Opção",
                orientation="h",
                text="TextoPerc",
                color="Percentagem",
                color_continuous_scale=["#dbeafe", "rgb(0,0,255)"],
                title="Candidatura à bolsa FCT?",
            )
            fig.update_traces(
                textposition="outside",
                customdata=q3_counts[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>"
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), yaxis_title="", coloraxis_showscale=False, xaxis=dict(range=[0, 100]), xaxis_title="%", font=dict(size=11))
            st.plotly_chart(fig, width="stretch")

        with dout3:
            q4_col = find_column(df, "1-4")
            q4_counts = code_counts(df[q4_col], Q_14)
            q4_total = q4_counts["Respostas"].sum()
            q4_counts["Percentagem"] = (q4_counts["Respostas"] / q4_total * 100).round(1)
            q4_counts["TextoPerc"] = q4_counts["Percentagem"].astype(str) + "%"
            fig = px.bar(
                q4_counts,
                x="Percentagem",
                y="Opção",
                orientation="h",
                text="TextoPerc",
                color="Percentagem",
                color_continuous_scale=["#dbeafe", "rgb(0,0,255)"],
                title="Manifestação para bolsa de mérito?",
            )
            fig.update_traces(
                textposition="outside",
                customdata=q4_counts[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>"
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), yaxis_title="", coloraxis_showscale=False, xaxis=dict(range=[0, 100]), xaxis_title="%", font=dict(size=11))
            st.plotly_chart(fig, width="stretch")


    with tab2:
        q11_col = find_column(df, "1-11")
        motives = code_counts(df[q11_col], Q_111)
        motives = motives.copy()
        total_respondentes = int(df[q11_col].map(lambda value: bool(split_codes(value))).sum())
        motives["Percentagem"] = (motives["Respostas"] / total_respondentes * 100).round(1) if total_respondentes else 0
        motives["Destaque"] = ["Top" if i < 3 else "Outros" for i in range(len(motives))]
        if len(motives) >= 3:
            cutoff = motives.iloc[2]["Respostas"]
            top_motives = motives[motives["Respostas"] >= cutoff].copy()
        else:
            top_motives = motives.copy()
        top_cols = st.columns(3)
        for idx, (_, row) in enumerate(top_motives.head(3).iterrows()):
            with top_cols[idx]:
                metric_box(f"Top {idx + 1}", row["Opção"], f'{row["Respostas"]} respondentes ({row["Percentagem"]}%)')
        left, right = st.columns([1.15, 0.85])
        with left:
            motives_chart = motives.sort_values(["Percentagem", "Respostas"], ascending=[False, False]).reset_index(drop=True)
            fig = px.bar(
                motives_chart,
                y="Opção",
                orientation="h",
                x="Percentagem",
                color="Destaque",
                color_discrete_sequence=["rgb(0,0,255)", "#9ec5fe"],
                title="Principais motivos para iniciar o doutoramento",
            )
            fig.update_traces(
                text=motives_chart["Percentagem"].map(lambda value: f"{value:.1f}%"),
                textposition="outside",
                customdata=motives_chart[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>% dos respondentes=%{customdata[1]}%<extra></extra>",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), yaxis_title="", xaxis_title="% dos respondentes", xaxis=dict(range=[0, 100]))
            st.plotly_chart(fig, width="stretch")

        st.caption("Cada motivo é calculado como percentagem dos respondentes que assinalaram essa opção; se houver empate no corte, ele é preservado no resumo.")

        q13_cols = [col for col in df.columns if col.startswith("1-13.")]
        q13 = mean_likert(df, q13_cols)
        fig = px.bar(
            q13,
            x="Média",
            y="Indicador",
            orientation="h",
            color_discrete_sequence=["rgb(0,0,255)"],
            title="Fatores na escolha do Iscte",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), yaxis_title="", xaxis=dict(range=[0, 5]))
        st.plotly_chart(fig, width="stretch")

        q15_cols = [col for col in df.columns if col.startswith("1-15.")]
        q15 = mean_likert(df, q15_cols)
        fig = px.bar(
            q15,
            x="Média",
            y="Indicador",
            orientation="h",
            color_discrete_sequence=["rgb(0,0,255)"],
            title="Fatores na escolha do curso",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), yaxis_title="", xaxis=dict(range=[0, 5]))
        st.plotly_chart(fig, width="stretch")

        bottom_left, bottom_right = st.columns(2)
        q20_col = find_column(df, "1-20")
        q22_col = find_column(df, "1-22")
        with bottom_left:
            q20_counts = code_counts(
                df[q20_col],
                {
                    1: "Conciliação com vida pessoal/familiar",
                    2: "Conciliação com atividade profissional",
                    3: "Área de formação diferente",
                    4: "Dificuldades económicas/financeiras",
                    5: "Falta de acompanhamento do orientador",
                    6: "Desmotivação",
                    7: "Gestão do tempo",
                    8: "Dificuldades metodológicas",
                    9: "Falta de financiamento",
                    10: "Não espero obstáculos",
                    11: "Outro",
                },
            )
            fig = px.bar(
                q20_counts,
                x="Respostas",
                y="Opção",
                orientation="h",
                color_discrete_sequence=["rgb(0,0,255)"],
                title="Fatores que podem afetar a finalização no tempo previsto",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), yaxis_title="", xaxis_title="Respostas")
            st.plotly_chart(fig, width="stretch")

        with bottom_right:
            q22_counts = code_counts(
                df[q22_col],
                {
                    1: "Acompanhamento eficaz do orientador",
                    2: "Formação em competências transversais",
                    3: "Formação específica",
                    4: "Plano de trabalhos bem definido",
                    5: "Prazos e metas claras",
                    6: "Serviços de apoio",
                    7: "Recursos institucionais",
                    8: "Reconhecimento pela concessão de bolsa",
                    9: "Reconhecimento por prémios",
                    10: "Seminários e atividades científicas",
                    11: "Inserção em grupos e redes científicas",
                    12: "Projetos ou publicações em coautoria",
                    13: "Outro",
                },
            )
            fig = px.bar(
                q22_counts,
                x="Respostas",
                y="Opção",
                orientation="h",
                color_discrete_sequence=["rgb(0,0,255)"],
                title="Fatores que podem contribuir para concluir no tempo previsto",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), yaxis_title="", xaxis_title="Respostas")
            st.plotly_chart(fig, width="stretch")

    with tab4:
        q17_col = find_column(df, "1-17")
        q24_col = find_column(df, "1-24")
        q26_col = find_column(df, "1-26")

        top_left, top_right = st.columns(2)
        with top_left:
            q17_counts = code_counts(df[q17_col], Q_117)
            fig = px.pie(
                q17_counts,
                names="Opção",
                values="Respostas",
                color_discrete_sequence=["rgb(0,0,255)", "#6ea8fe", "#9ec5fe", "#cfe2ff"],
                title="Integração do projeto de tese",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
            st.plotly_chart(fig, width="stretch")

        with top_right:
            q24_counts = code_counts(df[q24_col], Q_124)
            fig = px.bar(
                q24_counts,
                x="Respostas",
                y="Opção",
                orientation="h",
                color_discrete_sequence=["rgb(0,0,255)"],
                title="Situação profissional um ano após o doutoramento",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), yaxis_title="", xaxis=dict(range=[0, 100]))
            st.plotly_chart(fig, width="stretch")

        bottom_left, bottom_right = st.columns(2)
        with bottom_left:
            q26_counts = code_counts(df[q26_col], Q_126)
            fig = px.bar(
                q26_counts,
                x="Respostas",
                y="Opção",
                orientation="h",
                color_discrete_sequence=["rgb(0,0,255)"],
                title="Setor de atividade pretendido após o doutoramento",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), xaxis_title="", yaxis_title="")
            st.plotly_chart(fig, width="stretch")


def typical_profile(df: pd.DataFrame) -> dict[str, str]:
    age_bins = [18, 24, 29, 34, 39, 44, 49, 59, 100]
    age_labels = ["18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-59", "60+"]
    age_bucket = pd.cut(df["RESPONDENT_AGE"], bins=age_bins, labels=age_labels, right=True, include_lowest=True)
    age_mode = age_bucket.value_counts().index[0] if not age_bucket.dropna().empty else "-"

    def modal_value(column: str) -> str:
        series = df[column].replace({"nan": pd.NA, "None": pd.NA}).dropna()
        if series.empty:
            return "-"
        return str(series.astype(str).value_counts().index[0])

    return {
        "género": modal_value("RESPONDENT_GENDER"),
        "faixa_etária": str(age_mode),
        "nacionalidade": modal_value("NACIONALIDADE_1"),
        "situação profissional": modal_value("CONDICAO_PROFISSIONAL_ALUNO"),
        "setor profissional": modal_value("SCHOLARSHIP_GRANT_OWNER"),
    }


def profile_subsections(df: pd.DataFrame) -> dict[str, list[tuple[str, str]]]:
    def first_category(column: str) -> str:
        counts = categorical_summary(df[column], drop_missing=True)
        if counts.empty:
            return "-"
        first = counts.iloc[0]
        return f"{first['Categoria']} ({first['Percentagem']}%)"

    def coded_category(column: str, mapping: dict[int, str]) -> str:
        counts = code_counts(df[column], mapping)
        if counts.empty:
            return "-"
        first = counts.iloc[0]
        total = counts["Respostas"].sum()
        percentage = round(first["Respostas"] / total * 100, 1) if total else 0
        return f"{first['Opção']} ({percentage}%)"

    age_bins = [18, 24, 29, 34, 39, 44, 49, 59, 100]
    age_labels = ["18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-59", "60+"]
    age_bucket = pd.cut(df["RESPONDENT_AGE"], bins=age_bins, labels=age_labels, right=True, include_lowest=True)
    age_counts = age_bucket.value_counts().reset_index()
    age_counts.columns = ["Categoria", "Respostas"]
    age_counts["Percentagem"] = (age_counts["Respostas"] / age_counts["Respostas"].sum() * 100).round(1)
    age_mode = age_counts.iloc[0] if not age_counts.empty else None

    sociodemografico = [
        ("Género", first_category("RESPONDENT_GENDER")),
        ("Idade", f"{age_mode['Categoria']} ({age_mode['Percentagem']}%)" if age_mode is not None else "-"),
        ("Nacionalidade", first_category("NACIONALIDADE_1")),
    ]

    profissional = [
        ("Situação profissional", first_category("CONDICAO_PROFISSIONAL_ALUNO")),
        ("Setor de trabalho", coded_category(find_column(df, "1-8"), Q_18)),
    ]

    return {
        "sociodemográfico": sociodemografico,
        "profissional": profissional,
    }


def main() -> None:
    if not DATA_FILE.exists():
        st.error(f"Não foi encontrado o ficheiro de dados: {DATA_FILE.name}")
        st.stop()

    apply_blue_theme()

    df = load_processed()
    eligible = df[eligible_mask(df, 0.75)].copy()
    schools = school_options(df)

    st.markdown(
        """
        <div class="hero">
            <h1>Dashboard dos novos estudantes do 3.º ciclo</h1>
            <p>
                Exploração hierárquica por escola e curso, com leitura direta do inquérito 2025/2026.
                O foco está no perfil, motivações, fatores de decisão e expectativas pós-doutoramento.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selector_left, selector_right = st.columns(2)
    with selector_left:
        st.markdown('<div class="section-title">Seleção de Escola</div>', unsafe_allow_html=True)
        selected_school = st.selectbox("Escola", options=["Todas"] + schools, index=0, label_visibility="collapsed")

    selected_school_value = None if selected_school == "Todas" else selected_school
    courses = course_options(df, selected_school_value)

    with selector_right:
        st.markdown('<div class="section-title">Seleção de Curso</div>', unsafe_allow_html=True)
        if courses:
            selected_course = st.selectbox("Curso", options=["Todos"] + courses, index=0, label_visibility="collapsed")
        else:
            selected_course = "Todos"

    selected_course_value = None if selected_course == "Todos" else selected_course
    filtered = filter_data(eligible, selected_school_value, selected_course_value)

    st.caption(f"{len(filtered)} respostas válidas no critério de 75% no contexto selecionado.")
    render_charts(filtered)


if __name__ == "__main__":
    main()