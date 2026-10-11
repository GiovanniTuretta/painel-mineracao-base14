"""Equipamentos e operadores (notebook 01, P12 e P13)."""
import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go
import streamlit as st
from scipy.cluster.hierarchy import linkage
from sklearn.preprocessing import StandardScaler

from analises import NOMES, equipamentos, operadores
from dados import carregar, num
from visual import GRAFITE, LARANJA, PO, barras, cabecalho, estilo, mostrar, paragrafo

r = st.session_state.recorte
f = r["atual"]
cabecalho("Equipamentos e operadores", r["periodo"], f)
if len(f) < 100:
    st.warning("Poucas operações com esses filtros. Escolha um período maior ou mais minas.")
    st.stop()

eq, _ = equipamentos(f)
falhas = eq.qtd_falhas_equipamento.sort_values()
paragrafo(
    f"Nenhuma máquina é \"a problemática\". Os 13 equipamentos têm entre **{num(falhas.min(), 2)} e "
    f"{num(falhas.max(), 2)} falhas por operação**, e a produtividade varia só de "
    f"{num(eq.produtividade_t_h.min())} a {num(eq.produtividade_t_h.max())} t/h. "
    "A variação de falhas vem do turno, não da máquina. Já entre os operadores há candidatos a ganhar mais escala."
)

# ---- P12 ----
st.subheader("Algum equipamento destoa dos outros?")
c1, c2 = st.columns([2, 3], gap="large")
with c1:
    st.caption("Falhas médias por operação. Escavadeiras começam com ESC, caminhões com CAM.")
    mostrar(barras(falhas.rename("falhas").rename_axis("equip").reset_index(), "equip", "falhas", "", 2, destaque=""))
with c2:
    st.caption(
        "Árvore de parentesco: equipamentos ligados mais embaixo se parecem mais. "
        "Aqui todas as ligações são baixas, porque as máquinas são quase iguais."
    )
    Z = StandardScaler().fit_transform(eq)
    arvore = ff.create_dendrogram(Z, labels=eq.index.tolist(), linkagefun=lambda d: linkage(d, "ward"))
    for tr in arvore.data:
        tr.line.color = GRAFITE
        tr.line.width = 1.2
        tr.hoverinfo = "skip"
    estilo(arvore, 340)
    arvore.update_yaxes(title="Distância", showticklabels=True)
    mostrar(arvore)

with st.expander("Médias de cada equipamento"):
    st.dataframe(eq.rename(columns=NOMES).round(2), width="stretch")
    st.caption("Agrupamento hierárquico de Ward sobre as médias padronizadas. Com só 13 equipamentos, o dendrograma sempre agrupa algo; a altura das ligações mostra se a diferença importa.")

# ---- P13 ----
st.subheader("Há operadores bons e pouco aproveitados?")
st.caption(
    "Como o professor comparou com jogadores de futebol: um operador que rende acima da média do próprio turno, "
    "tem poucas falhas, mas trabalhou pouco. Usa a base inteira, porque cada operador tem poucas operações."
)
op, op8, lim = operadores(carregar())
cand = op8[op8.candidato].sort_values("prod_vs_turno", ascending=False)

rng = np.random.default_rng(0)
jitter = rng.uniform(-0.25, 0.25, len(op8))  # espalha pontos que caem no mesmo número de operações
fig = go.Figure()
for eh, cor, nome, tam in [(False, PO, "Outros operadores", 6), (True, LARANJA, "Bons e pouco aproveitados", 9)]:
    x = op8[op8.candidato == eh]
    j = jitter[(op8.candidato == eh).values]
    fig.add_scatter(
        x=x.n_operacoes + j, y=x.prod_vs_turno, mode="markers", name=nome,
        marker=dict(color=cor, size=tam, opacity=0.9 if eh else 0.5, line=dict(width=1 if eh else 0, color="#EEEFEC")),
        customdata=np.c_[x.index, x.n_operacoes, x.falhas_media],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} operações<br>"
                      "%{y:+.1f} t/h vs. média do turno<br>%{customdata[2]:.2f} falhas por operação<extra></extra>",
    )
fig.add_hline(y=0, line_color="#C9CCC6", line_width=1)
estilo(fig, 400)
fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=0))
fig.update_xaxes(title="Operações feitas no período todo", dtick=1)
fig.update_yaxes(title="Toneladas por hora acima (+) ou abaixo (−) da média do turno")
mostrar(fig)

paragrafo(
    f"Dos {num(len(op8))} operadores com pelo menos 8 operações, **{len(cand)} são candidatos**: estão entre os 20% "
    f"mais produtivos do turno (+{num(lim['lim_prod'], 1)} t/h ou mais), entre os 20% com menos falhas "
    f"({num(lim['lim_fal'], 2)} ou menos por operação) e trabalharam até {num(lim['mediana_n'])} vezes. "
    + (f"Os três primeiros: {', '.join(cand.index[:3])}. " if len(cand) >= 3 else "")
    + "Com tão poucas operações por pessoa, parte do destaque pode ser sorte: **acompanhe antes de decidir**, "
    "como se observa um jogador antes de contratar.",
    "veredito",
)

with st.expander(f"Lista dos {len(cand)} candidatos"):
    st.dataframe(
        cand.drop(columns="candidato").round(2),
        width="stretch",
        column_config=dict(
            n_operacoes="Operações",
            prod_vs_turno=st.column_config.NumberColumn("t/h vs. média do turno", format="%+.1f"),
            falhas_media="Falhas por operação",
            custo_por_t=st.column_config.NumberColumn("Custo típico (R$/t)", format="%.2f"),
        ),
    )
    st.caption(
        f"Ao todo são {num(len(op))} operadores, com média de {num(op.n_operacoes.mean(), 1)} operações cada. "
        "A produtividade é comparada com a média do mesmo turno, porque o turno da noite rende menos para todos."
    )
