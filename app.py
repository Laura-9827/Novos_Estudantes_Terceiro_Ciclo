from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config.mappings import Q_111, Q_117, Q_124, Q_126, Q_12, Q_13, Q_14, Q_18
from src.config.settings import (
    BRAND_BLUE,
    BRAND_CONTINUOUS_SCALE,
    BRAND_DISCRETE_SEQUENCE,
    DATA_FILE,
    RESPONSE_RATE_NUMERATOR,
    UNIVERSE_SIZE,
)
from src.services.data import (
    categorical_summary,
    code_counts,
    course_options,
    eligible_mask,
    filter_data,
    find_column,
    format_percentage,
    load_processed,
    mean_likert,
    school_options,
    split_codes,
)
from src.services.profiles import profile_subsections
from src.viz.layout import apply_blue_theme


st.set_page_config(
    page_title="Dashboard - Novos Estudantes 3.º Ciclo",
    page_icon="📊",
    layout="wide",
)


def metric_box(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


def render_charts(df: pd.DataFrame) -> None:
    top_metrics = st.columns(3)
    with top_metrics[0]:
        metric_box("Respostas válidas", f"{len(df)}")
    with top_metrics[1]:
        response_rate = RESPONSE_RATE_NUMERATOR / UNIVERSE_SIZE * 100
        metric_box(
            "Taxa de resposta",
            format_percentage(response_rate),
            "281 respostas válidas no critério de 75% de preenchimento do questionário, sobre um total de 387 de novos estudantes de doutoramento",
        )
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
                color_discrete_sequence=BRAND_DISCRETE_SEQUENCE,
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
                color_continuous_scale=BRAND_CONTINUOUS_SCALE,
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
                color_continuous_scale=BRAND_CONTINUOUS_SCALE,
                title="Distribuição por situação profissional",
            )
            fig.update_traces(
                textposition="outside",
                customdata=occupation_counts[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>",
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
                color_continuous_scale=BRAND_CONTINUOUS_SCALE,
                title="Distribuição por setor profissional",
            )
            fig.update_traces(
                textposition="outside",
                customdata=sector_counts[["Respostas"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<extra></extra>",
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
            color_discrete_sequence=[BRAND_BLUE],
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
                color_continuous_scale=BRAND_CONTINUOUS_SCALE,
                title="Vai iniciar logo a seguir?",
            )
            fig.update_traces(
                textposition="outside",
                customdata=q2_counts[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>",
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
                color_continuous_scale=BRAND_CONTINUOUS_SCALE,
                title="Candidatura à bolsa FCT?",
            )
            fig.update_traces(
                textposition="outside",
                customdata=q3_counts[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>",
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
                color_continuous_scale=BRAND_CONTINUOUS_SCALE,
                title="Manifestação para bolsa de mérito?",
            )
            fig.update_traces(
                textposition="outside",
                customdata=q4_counts[["Respostas", "Percentagem"]],
                hovertemplate="<b>%{y}</b><br>N=%{customdata[0]}<br>%{customdata[1]}%<extra></extra>",
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
                color_discrete_sequence=[BRAND_BLUE, "rgb(98, 131, 230)"],
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
            color_discrete_sequence=[BRAND_BLUE],
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
            color_discrete_sequence=[BRAND_BLUE],
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
                color_discrete_sequence=[BRAND_BLUE],
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
                color_discrete_sequence=[BRAND_BLUE],
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
                color_discrete_sequence=BRAND_DISCRETE_SEQUENCE + ["rgb(170, 188, 245)"],
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
                color_discrete_sequence=[BRAND_BLUE],
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
                color_discrete_sequence=[BRAND_BLUE],
                title="Setor de atividade pretendido após o doutoramento",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), xaxis_title="", yaxis_title="")
            st.plotly_chart(fig, width="stretch")


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