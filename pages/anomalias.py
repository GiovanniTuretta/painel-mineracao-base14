"""Operações fora do padrão (notebook 01, P14): Isolation Forest na base inteira."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analises import ATRIB, NOMES, nao_supervisionado
from dados import carregar, num
from visual import GRAFITE, LARANJA, PO, cabecalho, estilo, mostrar, paragrafo

r = st.session_state.recorte
base = carregar()
ns = nao_supervisionado()
f = r["atual"]
cabecalho(
    "Operações fora do padrão",
    "O detector foi treinado na base inteira, como no notebook; aqui aparecem as operações do recorte. " + r["periodo"],
    f,
)

anom = ns["anomalia"]
criticas = base.status_operacao == "Operação crítica"
achadas = int((anom & criticas).sum())
media = base.groupby(anom)[ATRIB + ["custo_por_t"]].mean().T
media.columns = ["Normal", "Fora do padrão"]

paragrafo(
    f"Um algoritmo procurou combinações raras de medidas e marcou **{int(anom.sum())} operações** (1% da base). "
    f"Elas têm em média {num(media.loc['qtd_falhas_equipamento', 'Fora do padrão'], 1)} falhas e custam "
    f"**R$ {num(media.loc['custo_por_t', 'Fora do padrão'], 2)} por tonelada**, quase "
    f"{num(media.loc['custo_por_t', 'Fora do padrão'] / media.loc['custo_por_t', 'Normal'])} vezes o normal. "
    f"O mais importante: **sem saber qual era o status**, ele encontrou **{achadas} das {int(criticas.sum())} operações "
    "críticas**. Serve como alerta automático."
)

k1, k2, k3 = st.columns(3, gap="medium")
no_recorte = anom.reindex(f.index)
k1.metric("Fora do padrão neste recorte", num(int(no_recorte.sum())), help="Operações do recorte que o detector marcou.")
k2.metric("Críticas encontradas", f"{achadas} de {int(criticas.sum())}", help="Na base inteira, sem usar o status.")
k3.metric("Custo por tonelada", f"R$ {num(media.loc['custo_por_t', 'Fora do padrão'], 2)}",
          help=f"Média das operações fora do padrão. As normais custam R$ {num(media.loc['custo_por_t', 'Normal'], 2)}.")

st.subheader("Onde estão as operações estranhas")
st.caption(
    "Mesmo mapa da página de perfis: para a direita, minério mais rico; para cima, mais falha. "
    "As operações fora do padrão (laranja) ficam no alto, onde falha e custo explodem."
)
vis = f.assign(pc1=ns["pc1"], pc2=ns["pc2"], anomalia=anom)
normais = vis[~vis.anomalia].sample(min(4000, int((~vis.anomalia).sum())), random_state=42)
estranhas = vis[vis.anomalia]
fig = go.Figure()
fig.add_scatter(
    x=normais.pc1, y=normais.pc2, mode="markers", name="Normal",
    marker=dict(color=PO, size=4, opacity=0.5, line=dict(width=0)), hoverinfo="skip",
)
fig.add_scatter(
    x=estranhas.pc1, y=estranhas.pc2, mode="markers", name="Fora do padrão",
    marker=dict(color=LARANJA, size=9, line=dict(width=1.5, color="#EEEFEC")),
    customdata=estranhas[["registro_id", "mina", "turno", "status_operacao", "custo_por_t"]],
    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}, %{customdata[2]}<br>%{customdata[3]}<br>"
                  "R$ %{customdata[4]:.2f}/t<extra></extra>",
)
estilo(fig, 420)
fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.06, x=0))
fig.update_xaxes(title="Minério mais rico →", showticklabels=False, zeroline=False)
fig.update_yaxes(title="Mais falha e mais custo →", showticklabels=False)
mostrar(fig)

st.subheader("Normal contra fora do padrão")
comp = media.rename(index=NOMES).round(2)
comp["Diferença"] = (comp["Fora do padrão"] / comp["Normal"] - 1).map(lambda v: f"{v * 100:+.0f}%".replace(".", ","))
st.dataframe(comp, width="stretch")

st.subheader("Lista para investigar")
st.caption(
    "Ordenada da mais estranha para a menos estranha. É uma lista de candidatos a investigar, não prova de erro."
)
lista = (
    f.loc[no_recorte[no_recorte].index]
    .assign(estranheza=ns["estranheza"])
    .sort_values("estranheza", ascending=False)
)
st.dataframe(
    lista[["registro_id", "data_operacao", "mina", "turno", "status_operacao", "qtd_falhas_equipamento",
           "horas_parada", "produtividade_t_h", "custo_por_t", "estranheza"]],
    hide_index=True,
    width="stretch",
    column_config=dict(
        registro_id="Operação",
        data_operacao=st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        mina="Mina", turno="Turno", status_operacao="Status",
        qtd_falhas_equipamento="Falhas", horas_parada=st.column_config.NumberColumn("Horas paradas", format="%.1f"),
        produtividade_t_h=st.column_config.NumberColumn("t/h", format="%.0f"),
        custo_por_t=st.column_config.NumberColumn("R$/t", format="%.2f"),
        estranheza=st.column_config.ProgressColumn("Quão estranha", min_value=float(ns["estranheza"].min()),
                                                   max_value=float(ns["estranheza"].max()), format=" "),
    ),
)

with st.expander("Detalhes técnicos"):
    st.markdown(
        "**Isolation Forest** com contaminação de 1%, sobre os mesmos 10 atributos padronizados do agrupamento. "
        "A ideia: uma operação estranha é isolada com poucos cortes aleatórios nas medidas. "
        "Ele não recebe o status, então encontrar as críticas é uma confirmação independente de que elas são, "
        "de fato, combinações raras."
    )
    st.dataframe(
        pd.crosstab(base.status_operacao, anom.map({True: "Fora do padrão", False: "Normal"})),
        width="stretch",
    )
