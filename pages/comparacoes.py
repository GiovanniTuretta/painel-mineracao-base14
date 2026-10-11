"""Comparar grupos (notebook 01, P3 e P4). Responde em frase; os testes ficam nos detalhes."""
import plotly.express as px
import streamlit as st

from analises import comparar, p_txt
from dados import GRUPOS, METRICAS, num
from visual import ACO, barras, cabecalho, estilo, mostrar, paragrafo

r = st.session_state.recorte
f = r["atual"]

cabecalho("Comparar grupos", r["periodo"], f)

nomes = {m["nome"]: c for c, m in METRICAS.items()}
a, b = st.columns(2, gap="medium")
coluna = nomes[a.selectbox("O que você quer comparar?", nomes)]
nome_grupo = b.selectbox("Entre quais grupos?", GRUPOS)
grupo = GRUPOS[nome_grupo]
m = METRICAS[coluna]
st.caption(m["explica"])

g = f[f[grupo] != "Não informado"]
amostras = [x[coluna].dropna() for _, x in g.groupby(grupo)]
if len(amostras) < 2 or min(map(len, amostras)) < 3:
    st.warning(
        f"Com os filtros atuais sobra só um {nome_grupo.lower()} ou poucas operações por grupo. "
        "Escolha outro agrupamento acima ou marque mais opções na barra da esquerda."
    )
    st.stop()

# Melhor grupo primeiro (respeitando se maior ou menor é melhor)
tabela = g.groupby(grupo)[coluna].agg(m["agg"]).sort_values(ascending=not m["maior_melhor"]).reset_index()
melhor, pior = tabela.iloc[0], tabela.iloc[-1]
valor = lambda v: f"{num(v, m['casas'])} {m['unidade']}"
res = comparar(g, coluna, grupo)
real = res["kruskal_p"] < 0.05

st.subheader(f"{m['nome']} por {nome_grupo.lower()}")
mostrar(barras(tabela, grupo, coluna, m["unidade"], m["casas"], destaque=melhor[grupo] if real else ""))

maior_par = res["pares"].iloc[0]
texto = (
    f"**{melhor[grupo]}** tem o melhor resultado, {valor(melhor[coluna])}, e "
    f"**{pior[grupo]}** o pior, {valor(pior[coluna])}. "
)
if real:
    texto += (
        f"**A diferença é real**: um teste estatístico mostrou que ela não é fruto do acaso. "
        f"O maior contraste, {maior_par.par.replace(' × ', ' contra ')}, tem efeito **{maior_par.efeito}**."
    )
    if coluna == "produtividade_t_h":
        horas = g.horas_operacao.mean()
        texto += (
            f" Numa operação de {num(horas)} horas, isso dá cerca de "
            f"**{num(maior_par.diferenca * horas)} toneladas** a mais ou a menos."
        )
    paragrafo(texto, "veredito")
else:
    texto += (
        "**Essa diferença pode ser acaso**: o teste não confirma que os grupos sejam diferentes. "
        f"Na prática, {nome_grupo.lower()} não é um bom critério para priorizar ações."
    )
    paragrafo(texto, "veredito incerto")

st.subheader("Quanto diferem, par a par")
st.caption(
    "Com milhares de operações, quase toda diferença vira estatisticamente significativa. "
    "Por isso, além do teste, olhamos o tamanho do efeito: desprezível, pequeno, médio ou grande."
)
pares = res["pares"].assign(
    diferenca=lambda t: t.diferenca.map(lambda v: valor(v)),
    real=lambda t: t.p_holm.map(lambda p: "sim" if p < 0.05 else "não"),
)
st.dataframe(
    pares[["par", "diferenca", "efeito", "real"]],
    hide_index=True,
    width="stretch",
    column_config={
        "par": "Comparação (maior × menor)",
        "diferenca": "Diferença das médias",
        "efeito": "Tamanho do efeito",
        "real": "Diferença real?",
    },
)

with st.expander("Detalhes técnicos"):
    st.markdown(
        f"1. **Levene** (centrado na mediana) testa se a variação é igual entre os grupos: p {p_txt(res['levene'])}. "
        f"{'As variâncias diferem, por isso' if res['levene'] < 0.05 else 'Mesmo assim,'} usamos a ANOVA de Welch, que não exige variâncias iguais.\n"
        f"2. **ANOVA de Welch**: p {p_txt(res['welch'])}.\n"
        f"3. **Kruskal-Wallis** (não supõe curva normal): H = {num(res['kruskal_h'], 1)}, p {p_txt(res['kruskal_p'])}.\n"
        "4. **Pós-teste**: teste t de Welch para cada par, com correção de **Holm** para comparações múltiplas. "
        "Tamanho do efeito pelo **g de Hedges** (até 0,2 desprezível; 0,5 pequeno; 0,8 médio; acima, grande).\n\n"
        "Cuidado: as operações não são totalmente independentes (o mesmo equipamento e a mesma mina se repetem), "
        "por isso a conclusão se apoia no tamanho do efeito, não só no p-valor."
    )
    st.dataframe(
        res["pares"].assign(p=lambda t: t.p.map(p_txt), p_holm=lambda t: t.p_holm.map(p_txt)).round(3),
        hide_index=True,
        width="stretch",
        column_config=dict(par="Par", diferenca="Diferença", g="Hedges g", p="p (Welch)", p_holm="p (Holm)", efeito="Efeito"),
    )
    caixa = px.box(g, x=coluna, y=grupo, points=False, color_discrete_sequence=[ACO])
    estilo(caixa, 80 + 50 * len(tabela))
    caixa.update_xaxes(title=f"{m['nome']} ({m['unidade']})")
    mostrar(caixa)
    st.caption("Cada caixa mostra onde fica a metade central das operações. A linha no meio é a mediana.")
    st.dataframe(
        g.groupby(grupo)[coluna].agg(Operações="count", Média="mean", Mediana="median", Desvio="std").round(2),
        width="stretch",
    )
