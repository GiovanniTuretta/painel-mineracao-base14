"""Página 1 — Como está a operação. Ordem de leitura: texto -> números -> gráficos -> tabela."""
import pandas as pd
import streamlit as st

from dados import METRICAS, num, resumo, toneladas, uma_em_cada
from visual import barras, cabecalho, linha_tempo, mostrar, paragrafo

r = st.session_state.recorte
f, ant = r["atual"], r["anterior"]

cabecalho("Como está a operação", r["descricao"], f)

if f.empty:
    st.warning("Nenhuma operação encontrada com esses filtros. Escolha um período maior ou mais minas.")
    st.stop()

tem_anterior = ant is not None and not ant.empty


def variacao(atual, anterior):
    """Variação em % como texto ('+2,3%'), ou None se não há período anterior."""
    if not tem_anterior:
        return None
    return f"{(atual - anterior) / anterior * 100:+.1f}%".replace(".", ",")


producao = f.massa_produto_t.sum()
tph = resumo(f, "produtividade_t_h")
custo = resumo(f, "custo_por_t")
problema = f.com_problema.mean()
por_mina = f.groupby("mina").produtividade_t_h.mean().sort_values(ascending=False)
semanal = f.groupby(pd.Grouper(key="data_operacao", freq="W"))
# Só semanas completas (7 dias): semana pela metade gera picos falsos no gráfico
completa = semanal.data_operacao.nunique() == 7
if not completa.any():
    completa[:] = True

# 1. O resumo em texto corrido: a mensagem principal em 5 segundos
tendencia = ""
if tem_anterior:
    v = (tph - resumo(ant, "produtividade_t_h")) / resumo(ant, "produtividade_t_h") * 100
    tendencia = (
        ", praticamente o mesmo que no período anterior" if abs(v) < 0.5
        else f", {num(abs(v), 1)}% {'a mais' if v > 0 else 'a menos'} que no período anterior"
    )
ranking_minas = (
    f"A **{por_mina.index[0]}** é a que mais produz por hora; a **{por_mina.index[-1]}**, a que menos."
    if len(por_mina) > 1 else ""
)
paragrafo(
    f"Foram **{num(len(f))} operações**, que geraram **{toneladas(producao)}** de produto. "
    f"Cada hora de trabalho rendeu **{num(tph)} toneladas**{tendencia}. "
    f"**{uma_em_cada(problema)} operações** teve algum problema, seja restrição ou situação crítica. "
    + ranking_minas
)

# 2. Régua de números (verde = melhorou, vermelho = piorou)
k1, k2, k3, k4 = st.columns(4, gap="medium")
k1.metric(
    "Produção (toneladas)", toneladas(producao, curto=True),
    variacao(producao, ant.massa_produto_t.sum()) if tem_anterior else None,
    help="Total de minério pronto para venda no período. A seta compara com o período anterior.",
    chart_data=semanal.massa_produto_t.sum()[completa].tolist(), delta_description="vs. período anterior",
)
k2.metric(
    "Toneladas por hora", f"{num(tph)} t/h",
    variacao(tph, resumo(ant, "produtividade_t_h")) if tem_anterior else None,
    help=METRICAS["produtividade_t_h"]["explica"],
    chart_data=semanal.produtividade_t_h.mean()[completa].tolist(), delta_description="vs. período anterior",
)
k3.metric(
    "Custo por tonelada", f"R$ {num(custo, 2)}",
    variacao(custo, resumo(ant, "custo_por_t")) if tem_anterior else None,
    delta_color="inverse",  # custo caindo é bom -> verde
    help=METRICAS["custo_por_t"]["explica"],
    chart_data=semanal.custo_por_t.median()[completa].tolist(), delta_description="vs. período anterior",
)
k4.metric(
    "Operações com problema", f"{num(problema * 100)}%",
    f"{(problema - ant.com_problema.mean()) * 100:+.1f} pontos".replace(".", ",") if tem_anterior else None,
    delta_color="inverse",  # menos problema é bom -> verde
    help="Parte das operações que teve restrição ou situação crítica. Quanto menor, melhor.",
    chart_data=(semanal.com_problema.mean() * 100)[completa].tolist(), delta_description="vs. período anterior",
)

st.space("medium")

# 3. Tendência e comparação
g1, g2 = st.columns([3, 2], gap="large")
with g1:
    st.subheader("A produtividade está subindo ou caindo?")
    serie = semanal.produtividade_t_h.mean()[completa]
    st.caption(f"Toneladas por hora, média de cada semana. A linha clara marca a média do período, {num(serie.mean())} t/h.")
    mostrar(linha_tempo(serie, "t/h", 0))
with g2:
    st.subheader("Qual mina produz mais por hora?")
    st.caption("A barra escura é a melhor mina no período.")
    mostrar(barras(por_mina.reset_index(), "mina", "produtividade_t_h", "t/h", 0, destaque=por_mina.index[0]))

# 4. Detalhe para quem quer conferir
with st.expander("Ver os números por mina"):
    tabela = (
        f.groupby("mina")
        .agg(
            operacoes=("registro_id", "count"),
            producao=("massa_produto_t", "sum"),
            tph=("produtividade_t_h", "mean"),
            custo=("custo_por_t", "median"),
            problema=("com_problema", "mean"),
        )
        .assign(problema=lambda t: t.problema * 100)
        .sort_values("tph", ascending=False)
    )
    st.dataframe(
        tabela,
        width="stretch",
        column_config={
            "mina": "Mina",
            "operacoes": st.column_config.NumberColumn("Operações", format="localized"),
            "producao": st.column_config.NumberColumn("Produção (t)", format="localized"),
            "tph": st.column_config.NumberColumn("Toneladas por hora", format="%.0f"),
            "custo": st.column_config.NumberColumn("Custo típico (R$/t)", format="%.2f"),
            "problema": st.column_config.NumberColumn("Com problema (%)", format="%.0f%%"),
        },
    )
