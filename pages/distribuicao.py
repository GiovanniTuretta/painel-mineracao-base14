"""Como os números se distribuem (notebook 01, P1 e P2)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from analises import NOMES, wilson
from dados import num
from visual import ACO, GRAFITE, PO, cabecalho, estilo, histograma, mostrar, paragrafo

r = st.session_state.recorte
f = r["atual"]
cabecalho("Como os números se distribuem", r["periodo"], f)
if len(f) < 30:
    st.warning("Poucas operações com esses filtros. Escolha um período maior ou mais minas.")
    st.stop()

# Medidas do notebook (seção 3.2), com unidade e casas decimais para exibir
MEDIDAS = {
    "produtividade_t_h": ("t/h", 0),
    "custo_por_t": ("R$/t", 2),
    "recuperacao_metalurgica_pct": ("%", 1),
    "horas_parada": ("h", 1),
    "qtd_falhas_equipamento": ("falhas", 2),
    "teor_fe_pct": ("%", 1),
    "massa_produto_t": ("t", 0),
    "consumo_diesel_l": ("L", 0),
    "tempo_ciclo_min": ("min", 1),
}

prod, custo = f.produtividade_t_h, f.custo_por_t
paragrafo(
    f"Uma operação típica produz **{num(prod.median())} t/h**, e metade delas fica entre "
    f"{num(prod.quantile(.25))} e {num(prod.quantile(.75))} t/h. "
    f"O custo por tonelada é diferente: o valor típico é **R$ {num(custo.median(), 2)}**, mas a média sobe para "
    f"R$ {num(custo.mean(), 2)} porque poucas operações muito caras puxam a conta. "
    "Por isso, para custo, o painel sempre mostra o valor típico (mediana), não a média."
)

st.subheader("Como uma medida se espalha")
escolha = st.selectbox("Medida", list(MEDIDAS), format_func=lambda c: NOMES[c])
unidade, casas = MEDIDAS[escolha]
s = f[escolha].dropna()
st.caption(
    "Cada barra conta quantas operações tiveram aquele valor. A linha escura marca o valor típico (mediana); "
    "a pontilhada, a média. Quando as duas se afastam, há valores extremos puxando a média."
)
mostrar(histograma(s, unidade, casas))

cv = s.std() / s.mean() * 100
assim = s.skew()
forma = (
    "quase simétrica: média e mediana contam a mesma história"
    if abs(assim) < 0.5
    else "com cauda longa à direita: alguns valores bem altos" if assim > 0
    else "com cauda longa à esquerda: alguns valores bem baixos"
)
paragrafo(
    f"A distribuição é {forma}. 9 em cada 10 operações ficam entre **{num(s.quantile(.05), casas)}** e "
    f"**{num(s.quantile(.95), casas)} {unidade}**. A variação típica em relação à média é de {num(cv)}%.",
    "veredito",
)

with st.expander("Tabela completa de resumo (todas as medidas)"):
    def resumo(x):
        x = x.dropna()
        return pd.Series({
            "Operações": len(x), "Média": x.mean(), "Mediana": x.median(), "Desvio": x.std(),
            "Variação (CV %)": x.std() / x.mean() * 100, "5%": x.quantile(.05), "95%": x.quantile(.95),
            "IQR": x.quantile(.75) - x.quantile(.25), "MAD": stats.median_abs_deviation(x),
            "Assimetria": x.skew(), "Curtose": x.kurt(),
        })
    tabela = pd.DataFrame({NOMES[c]: resumo(f[c]) for c in MEDIDAS}).T.round(2)
    st.dataframe(tabela, width="stretch")
    st.caption(
        "IQR é a largura da metade central; MAD é o desvio típico em torno da mediana. As duas resistem a valores extremos. "
        "Assimetria acima de 1 indica cauda longa; o custo por tonelada é o caso mais forte da base."
    )

# ---- P2: com que frequência a operação dá problema ----
st.subheader("Com que frequência a operação dá problema?")
n = len(f)
ordem = ["Operação normal", "Operação com restrição", "Operação crítica"]
linhas = []
for status in ordem:
    k = int((f.status_operacao == status).sum())
    p, li, ls = wilson(k, n)
    linhas.append(dict(status=status, k=k, p=p * 100, li=li * 100, ls=ls * 100))
t = pd.DataFrame(linhas)

fig = go.Figure(go.Bar(
    x=t.p, y=t.status, orientation="h",
    marker_color=[PO, ACO, GRAFITE],
    error_x=dict(type="data", symmetric=False, array=t.ls - t.p, arrayminus=t.p - t.li, color=GRAFITE, thickness=1),
    text=[f"{num(v, 1 if v >= 1 else 2)}%" for v in t.p], textposition="outside", cliponaxis=False,
    textfont_color=GRAFITE,
    customdata=t[["k", "li", "ls"]],
    hovertemplate="<b>%{x:.2f}%</b> (%{customdata[0]} operações)<br>"
                  "95% de confiança: %{customdata[1]:.2f}% a %{customdata[2]:.2f}%<extra></extra>",
))
fig.update_layout(barcornerradius=3, bargap=0.5)
fig.update_yaxes(autorange="reversed", showgrid=False, tickfont_color=GRAFITE)
fig.update_xaxes(visible=False, range=[0, 100])
mostrar(estilo(fig, 170))

criticas = t.iloc[2]
if criticas.k > 0:
    paragrafo(
        f"Operação crítica é rara: **{int(criticas.k)} de {num(n)}**, cerca de **1 em cada {num(100 / criticas.p)}**. "
        f"Com 95% de confiança, a taxa real fica entre {num(criticas.li, 2)}% e {num(criticas.ls, 2)}%. "
        "Com tão poucos casos, não dá para treinar um modelo só para eles; a página "
        "**Operações fora do padrão** mostra outra forma de encontrá-los.",
        "veredito",
    )
else:
    paragrafo("Nenhuma operação crítica neste recorte.", "veredito incerto")

with st.expander("Detalhes técnicos"):
    st.markdown(
        "Intervalo de confiança de **Wilson** (95%): funciona bem para proporções pequenas, onde o intervalo "
        "comum falha e pode até dar valores negativos. Ele é assimétrico perto de zero, como deve ser."
    )
    st.dataframe(
        t.rename(columns=dict(status="Status", k="Operações", p="%", li="IC 95% inferior", ls="IC 95% superior")).round(3),
        hide_index=True, width="stretch",
    )
    st.markdown("**Composição da base** no recorte atual:")
    c1, c2, c3 = st.columns(3)
    for col, (rotulo, coluna) in zip((c1, c2, c3), [("Turno", "turno"), ("Tipo de minério", "tipo_minerio"), ("Mina", "mina")]):
        comp = f[coluna].value_counts().to_frame("Operações")
        comp["%"] = (comp["Operações"] / n * 100).round(1)
        col.dataframe(comp.rename_axis(rotulo), width="stretch")
