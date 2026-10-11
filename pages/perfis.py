"""Perfis de operação (notebook 01, P11): PCA + K-means com k = 3, na base inteira."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analises import ATRIB, NOMES, nao_supervisionado
from dados import carregar, num
from visual import GRAFITE, MINERIOS, PERFIS, cabecalho, estilo, mostrar, paragrafo

r = st.session_state.recorte
base = carregar()
ns = nao_supervisionado()
f = r["atual"]

cabecalho(
    "Perfis de operação",
    "Os perfis foram encontrados na base inteira, como no notebook. Os filtros mudam só quais operações aparecem "
    "e a parte de cada perfil no recorte. " + r["periodo"],
    f,
)

perfil = ns["perfil"]
dados = base.assign(perfil=perfil)
resumo = dados.groupby("perfil")[["teor_fe_pct", "recuperacao_metalurgica_pct", "produtividade_t_h",
                                  "qtd_falhas_equipamento", "horas_parada", "custo_por_t", "com_problema"]].mean()
resumo["operacoes"] = perfil.value_counts()
resumo = resumo.reindex(PERFIS)
mix_tipo = (pd.crosstab(dados.perfil, dados.tipo_minerio, normalize="index") * 100).reindex(PERFIS)

limpo, pobre, falha = (resumo.loc[p] for p in PERFIS)
paragrafo(
    "Sem receber nenhuma resposta pronta, o algoritmo separou as operações em **três perfis**, "
    "e eles reencontram os dois fatores que a estatística já tinha apontado: o tipo de minério e a falha de equipamento. "
    f"A operação com falha custa **R$ {num(falha.custo_por_t, 2)} por tonelada**, o dobro da operação limpa "
    f"(R$ {num(limpo.custo_por_t, 2)})."
)

# Os três perfis lado a lado, com o que os define
cols = st.columns(3, gap="large")
descricao = {
    "Minério rico, operação limpa": "Principalmente hematita. Muito ferro, ótimo aproveitamento e quase sem falhas.",
    "Minério pobre": "Principalmente itabirito. Pouco ferro e mais sílica, o que derruba o aproveitamento na usina.",
    "Operação com falha": "Qualquer minério. Muitas falhas e horas paradas: produz menos e custa mais.",
}
for col, (nome, cor) in zip(cols, PERFIS.items()):
    x = resumo.loc[nome]
    tipo_principal = mix_tipo.loc[nome].idxmax()
    with col:
        st.markdown(
            f'<div style="border-top:4px solid {cor};padding-top:.6rem">'
            f'<h3 style="margin:0 0 .3rem">{nome}</h3>'
            f'<p class="recorte" style="margin-bottom:.6rem">{descricao[nome]}</p></div>',
            unsafe_allow_html=True,
        )
        st.metric("Custo por tonelada", f"R$ {num(x.custo_por_t, 2)}")
        st.metric("Toneladas por hora", f"{num(x.produtividade_t_h)} t/h")
        st.metric("Aproveitamento", f"{num(x.recuperacao_metalurgica_pct, 1)}%")
        st.metric("Falhas por operação", num(x.qtd_falhas_equipamento, 2))
        st.caption(
            f"{num(x.operacoes)} operações, {num(x.com_problema * 100)}% delas com problema. "
            f"{num(mix_tipo.loc[nome, tipo_principal])}% são de {tipo_principal.lower()}."
        )

st.space("medium")
st.subheader("Como os perfis se espalham")
st.caption(
    "Cada ponto é uma operação, posicionada pelos dois eixos que mais resumem os dados: "
    "para a direita, minério mais rico; para cima, mais falha e mais custo. Mostramos até 4.000 pontos do recorte."
)
vis = f.assign(perfil=perfil, pc1=ns["pc1"], pc2=ns["pc2"])
vis = vis.sample(min(4000, len(vis)), random_state=42)
fig = go.Figure()
for nome, cor in PERFIS.items():
    x = vis[vis.perfil == nome]
    fig.add_scatter(
        x=x.pc1, y=x.pc2, mode="markers", name=nome,
        marker=dict(color=cor, size=5, opacity=0.6, line=dict(width=0)),
        customdata=x[["mina", "turno", "produtividade_t_h", "custo_por_t"]],
        hovertemplate=f"<b>{nome}</b><br>%{{customdata[0]}}, %{{customdata[1]}}<br>"
                      "%{customdata[2]:.0f} t/h, R$ %{customdata[3]:.2f}/t<extra></extra>",
    )
estilo(fig, 440)
fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.06, x=0))
fig.update_xaxes(title="Minério mais rico →", showticklabels=False, zeroline=False)
fig.update_yaxes(title="Mais falha e mais custo →", showticklabels=False)
mostrar(fig)

st.subheader("Quanto de cada perfil neste recorte")
mix_atual = f.assign(perfil=perfil).perfil.value_counts(normalize=True).reindex(PERFIS).fillna(0) * 100
fig = go.Figure()
for nome, cor in PERFIS.items():
    fig.add_bar(
        x=[mix_atual[nome]], y=[""], orientation="h", name=nome, marker_color=cor,
        text=f"{nome} {num(mix_atual[nome])}%", textposition="inside", insidetextanchor="middle",
        textfont=dict(color="white"), hovertemplate=f"{nome}: <b>%{{x:.1f}}%</b><extra></extra>",
    )
estilo(fig, 70)
fig.update_layout(barmode="stack", bargap=0.1)
fig.update_xaxes(visible=False, range=[0, 100])
fig.update_yaxes(visible=False)
mostrar(fig)
st.caption("Se um filtro faz o laranja crescer, aquele recorte tem mais operações com falha. Tente filtrar o turno da noite.")

with st.expander("Detalhes técnicos"):
    var = ns["variancia"]
    st.markdown(
        f"**Atributos** (padronizados, vazios com a mediana): {', '.join(NOMES[a] for a in ATRIB)}. "
        "Ficam fora identificadores, pares redundantes e o próprio status (usado só para interpretar).\n\n"
        f"**PCA:** o eixo 1 ({num(var[0] * 100)}% da variação) é a qualidade do minério; o eixo 2 ({num(var[1] * 100)}%) "
        f"é a falha. São precisos 6 eixos para 90% da variação, então o gráfico acima é uma aproximação.\n\n"
        f"**K-means, k = 3:** silhuetas baixas (0,11 a 0,19) mostram que os grupos não são ilhas separadas, "
        "mas uma nuvem contínua. Davies-Bouldin prefere k = 3, e os 3 perfis têm leitura operacional clara. "
        f"**Estabilidade:** ARI entre sementes de {num(min(ns['ari']), 2)} a {num(max(ns['ari']), 2)} (1 = idêntico)."
    )
    st.dataframe(
        ns["escolha_k"].round(3), width="stretch",
        column_config=dict(inercia="Inércia (cotovelo)", silhueta="Silhueta ↑", davies_bouldin="Davies-Bouldin ↓", calinski_harabasz="Calinski-Harabasz ↑"),
    )
    st.dataframe(ns["cargas"].rename(index=NOMES).round(3), width="stretch")
    st.dataframe(mix_tipo.round(1), width="stretch")
