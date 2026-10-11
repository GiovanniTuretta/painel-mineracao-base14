"""Problemas e custo (notebook 01, P5, P6 e o achado de vazamento de dados)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from analises import cramer, hedges_g, p_txt, tamanho
from dados import num
from visual import ACO, GRAFITE, PO, barras, cabecalho, estilo, mostrar, paragrafo

r = st.session_state.recorte
f = r["atual"]
cabecalho("Problemas e custo", r["periodo"], f)

normal = f.loc[~f.com_problema, "custo_por_t"].dropna()
restr = f.loc[f.com_problema, "custo_por_t"].dropna()
if len(normal) < 10 or len(restr) < 10:
    st.warning("Poucas operações com problema neste recorte. Escolha um período maior ou mais minas.")
    st.stop()

w = stats.ttest_ind(restr, normal, equal_var=False)
ic = w.confidence_interval()
dif = restr.mean() - normal.mean()
g = hedges_g(restr, normal)

paragrafo(
    f"Uma operação com problema custa **R$ {num(dif, 2)} a mais por tonelada**: R$ {num(restr.mean(), 2)} contra "
    f"R$ {num(normal.mean(), 2)} numa operação normal, ou {num(restr.mean() / normal.mean(), 1)} vezes mais. "
    "O problema quase sempre vem de **falha de equipamento**, e as falhas se concentram no **turno da noite**."
)

# ---- P5 ----
st.subheader("Operação com problema custa mais?")
c1, c2 = st.columns([3, 2], gap="large")
with c1:
    t = pd.DataFrame({"status": ["Normal", "Com problema"], "custo": [normal.mean(), restr.mean()]})
    mostrar(barras(t, "status", "custo", "R$/t", 2, destaque="Com problema", altura=130))
    st.caption("Custo médio por tonelada. Aqui usamos a média, como no notebook, porque a comparação é de totais de gasto.")
with c2:
    paragrafo(
        f"**Sim, e muito.** Com 95% de confiança, a diferença fica entre R$ {num(ic.low, 2)} e R$ {num(ic.high, 2)} "
        f"por tonelada. O efeito é **{tamanho(g)}**.",
        "veredito",
    )

# ---- P6 ----
st.subheader("Onde os problemas acontecem mais?")
st.caption("Parte das operações com problema em cada grupo. A barra escura indica onde a diferença é real.")
colunas = st.columns(3, gap="large")
resultados = []
for col, (rotulo, coluna) in zip(colunas, [("Turno", "turno"), ("Tipo de minério", "tipo_minerio"), ("Mina", "mina")]):
    d = f[f[coluna] != "Não informado"]
    tab = pd.crosstab(d[coluna], d.com_problema)
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        continue
    chi2, p, gl, v = cramer(tab)
    taxa = (d.groupby(coluna).com_problema.mean() * 100).sort_values(ascending=False).rename("taxa").reset_index()
    resultados.append(dict(fator=rotulo, chi2=chi2, gl=gl, p=p, v=v))
    with col:
        st.markdown(f"**{rotulo}**")
        mostrar(barras(taxa, coluna, "taxa", "%", 0, destaque=taxa[coluna].iloc[0] if p < 0.05 else ""))

res = pd.DataFrame(resultados)
reais = res[res.p < 0.05]
if not reais.empty:
    frase = " e ".join(f"**{x.lower()}**" for x in reais.fator)
    outros = [x.lower() for x in res[res.p >= 0.05].fator]
    texto = f"Só {frase} muda a chance de problema." if len(reais) == 1 else f"{frase} mudam a chance de problema."
    if outros:
        texto += f" {' e '.join(outros).capitalize()} não fazem diferença real."
    if "Turno" in set(reais.fator):
        noite = f.loc[f.turno == "Noite", "com_problema"].mean() * 100
        manha = f.loc[f.turno == "Manhã", "com_problema"].mean() * 100
        texto += f" À noite, {num(noite)}% das operações têm problema; de manhã, {num(manha)}%."
    paragrafo(texto, "veredito")
else:
    paragrafo("Neste recorte, nenhum desses fatores muda a chance de problema de forma real.", "veredito incerto")

# ---- Vazamento ----
st.subheader("O que define o status da operação?")
cruz = pd.crosstab(f.qtd_falhas_equipamento, f.status_operacao).reindex(
    columns=["Operação normal", "Operação com restrição", "Operação crítica"], fill_value=0
)
c1, c2 = st.columns([3, 2], gap="large")
with c1:
    fig = go.Figure(go.Heatmap(
        z=cruz.values, x=["Normal", "Com restrição", "Crítica"], y=[f"{int(i)} falha(s)" for i in cruz.index],
        colorscale=[[0, "#EEEFEC"], [1, ACO]], showscale=False,
        text=cruz.values, texttemplate="%{text}", textfont=dict(color=GRAFITE),
        hovertemplate="%{y}, %{x}: <b>%{z} operações</b><extra></extra>", xgap=2, ygap=2,
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    mostrar(estilo(fig, 60 + 36 * len(cruz)))
with c2:
    paragrafo(
        "**O status é praticamente uma regra das falhas.** Com 2 ou 3 falhas, a operação é sempre \"com restrição\"; "
        "com 4, sempre \"crítica\"; com 0 ou 1, quase sempre \"normal\". "
        "Para a etapa de machine learning, isso é um alerta: um modelo que use as falhas para prever o status acerta "
        "quase tudo, mas não aprende nada útil (vazamento de dados).",
        "veredito incerto",
    )

with st.expander("Detalhes técnicos"):
    st.markdown(
        f"**Custo (P5):** teste t de Welch, p {p_txt(w.pvalue)}; diferença R$ {num(dif, 2)}/t, "
        f"IC 95% [{num(ic.low, 2)}; {num(ic.high, 2)}]; Hedges g = {num(g, 2)}. "
        f"Mann-Whitney (sem depender da média): p {p_txt(stats.mannwhitneyu(restr, normal).pvalue)}.\n\n"
        "**Associação (P6):** qui-quadrado de independência e **V de Cramér** (0 = sem associação, 1 = total; "
        "abaixo de 0,1 é desprezível, até 0,3 é fraca)."
    )
    st.dataframe(
        res.assign(p=res.p.map(p_txt)).round(3),
        hide_index=True, width="stretch",
        column_config=dict(fator="Fator", chi2="Qui-quadrado", gl="Graus de liberdade", p="p-valor", v="V de Cramér"),
    )
