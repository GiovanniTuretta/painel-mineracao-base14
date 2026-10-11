"""Página 3 — Ao longo do tempo (notebook 02, P15–P17).

Usa todo o histórico, porque previsão precisa de tempo. Os filtros de mina,
turno e minério continuam valendo; o de período, não.
"""
import warnings

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller, kpss

from dados import carregar, data_br, num
from visual import ACO, estilo, barras, cabecalho, historico_e_previsao, mostrar, paragrafo

DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

r = st.session_state.recorte
h = r["historico"]

cabecalho(
    "Ao longo do tempo",
    f"Todo o histórico, de {data_br(h.data_operacao.min())} a {data_br(h.data_operacao.max())}. "
    f"{r['alcance']} O filtro de período não vale aqui: para prever, é preciso olhar o passado inteiro.",
    h,
)

# Produtividade média de cada dia (t/h). Média, não soma: o número de operações por dia varia.
fim_base = carregar().data_operacao.max()  # fim da base, não do filtro
diario = (
    h.groupby(h.data_operacao.dt.normalize()).produtividade_t_h.mean()
    .reindex(pd.date_range(h.data_operacao.min(), fim_base, freq="D"))
)
dias = diario.dropna()
if len(dias) < 60:
    st.warning("Com esses filtros sobram menos de 60 dias com operação. Escolha mais minas, turnos ou tipos de minério.")
    st.stop()

media = dias.mean()
baixo, alto = dias.quantile([0.05, 0.95])
movel = diario.rolling(28, min_periods=14).mean()
trimestres = dias.resample("QS").mean()
estavel = (trimestres.max() - trimestres.min()) / media < 0.03
proximos = pd.date_range(diario.index[-1] + pd.Timedelta(days=1), periods=7, freq="D")
previsao = pd.Series(media, index=proximos)
serie = diario.interpolate(limit_direction="both")  # STL e testes não aceitam dias vazios
lb = acorr_ljungbox(serie, lags=[7, 14])
sem_memoria = (lb.lb_pvalue > 0.05).all()

# Dias fora do padrão (notebook 02, seção 2.5): resíduo do STL acima de 3 desvios robustos
stl = STL(serie, period=7, robust=True).fit()
z_rob = (stl.resid - stl.resid.median()) / (1.4826 * stats.median_abs_deviation(stl.resid))
anomalos = dias[dias.index.isin(z_rob[z_rob.abs() > 3].index)]

# 1. A resposta em texto corrido
if estavel:
    abertura = (
        f"**A produtividade está estável.** Desde {data_br(dias.index[0])[3:]}, a média de cada trimestre "
        f"ficou entre {num(trimestres.min())} e {num(trimestres.max())} t/h. "
    )
else:
    abertura = (
        f"**A produtividade mudou ao longo do tempo.** A média de cada trimestre foi de "
        f"{num(trimestres.min())} a {num(trimestres.max())} t/h. "
    )
paragrafo(
    abertura
    + f"Um dia rende mais ou menos que outro, mas **9 em cada 10 dias** ficaram entre {num(baixo)} e {num(alto)} t/h."
)

st.subheader("Cada dia comparado com o normal")
st.caption(
    "A linha clara é a produtividade de cada dia. A escura é a média das últimas 4 semanas. "
    "A faixa sombreada mostra onde caem 9 em cada 10 dias. Os pontos à direita são a previsão. "
    "Círculos laranja marcam dias fora do padrão. "
    "O gráfico abre nos últimos 4 meses: arraste para ver outros períodos ou dê dois cliques para ver tudo."
)
mostrar(historico_e_previsao(diario.dropna(), movel.dropna(), baixo, alto, previsao, anomalos))

with st.expander(f"{len(anomalos)} dias fora do padrão em todo o histórico"):
    por_dia_ops = h.groupby(h.data_operacao.dt.normalize()).agg(
        operacoes=("registro_id", "count"), falhas=("qtd_falhas_equipamento", "sum")
    )
    st.dataframe(
        por_dia_ops.loc[anomalos.index].assign(tph=anomalos.values).rename_axis("dia").reset_index(),
        hide_index=True,
        width="stretch",
        column_config=dict(
            dia=st.column_config.DateColumn("Dia", format="DD/MM/YYYY"),
            operacoes="Operações no dia", falhas="Falhas no dia",
            tph=st.column_config.NumberColumn("t/h no dia", format="%.0f"),
        ),
    )
    st.caption(
        "Dias cujo resultado foge muito do esperado depois de descontar o padrão semanal. "
        "No notebook, a maioria se explica por dias com muitas ou poucas operações (a média do dia fica instável), "
        "então eles foram mantidos na série. São candidatos a investigar, não erros."
    )

# 2. Previsão
st.subheader("O que esperar na próxima semana")
p1, p2, p3 = st.columns(3, gap="medium")
p1.metric("Previsão para cada dia", f"{num(media)} t/h", help="Média de todo o histórico com os filtros atuais.")
p2.metric("Faixa provável", f"{num(baixo)} a {num(alto)} t/h", help="Onde caíram 9 em cada 10 dias até hoje.")
p3.metric("Dias previstos", f"{proximos[0]:%d/%m} a {proximos[-1]:%d/%m}")
motivo = (
    "O motivo: o resultado de um dia não ajuda a adivinhar o do dia seguinte."
    if sem_memoria
    else "Com os filtros atuais, porém, os dias mostram alguma dependência entre si; veja os detalhes técnicos."
)
paragrafo(
    "A previsão é a média do histórico. O grupo testou modelos mais elaborados (Holt-Winters, SARIMA e "
    f"Random Forest) e nenhum acertou mais do que ela. {motivo}",
    "veredito" if sem_memoria else "veredito incerto",
)

# 3. Dia da semana
st.subheader("Algum dia da semana rende mais?")
por_dia = dias.groupby(dias.index.dayofweek).mean().rename(index=dict(enumerate(DIAS)))
_, p_dia = stats.kruskal(*[g for _, g in dias.groupby(dias.index.dayofweek)])
c1, c2 = st.columns([3, 2], gap="large")
with c1:
    # Sem diferença real, nenhuma barra ganha destaque: todas ficam em cinza
    destaque = por_dia.idxmax() if p_dia < 0.05 else ""
    mostrar(barras(por_dia.rename("tph").rename_axis("dia").reset_index(), "dia", "tph", "t/h", 0, destaque=destaque))
with c2:
    diferenca = por_dia.max() - por_dia.min()
    if p_dia >= 0.05:
        paragrafo(
            f"**Não.** O melhor e o pior dia da semana ficam a {num(diferenca, 1)} t/h de distância, "
            "e o teste estatístico diz que isso é acaso. Não vale planejar a semana em torno de um dia específico.",
            "veredito incerto",
        )
    else:
        paragrafo(
            f"**Sim.** {por_dia.idxmax()} rende {num(diferenca, 1)} t/h a mais que {por_dia.idxmin()}, "
            "e o teste estatístico confirma que a diferença é real.",
            "veredito",
        )

# 4. Para quem quer conferir
with st.expander("Detalhes técnicos"):
    f_tend = max(0, 1 - stl.resid.var() / (stl.trend + stl.resid).var())
    f_saz = max(0, 1 - stl.resid.var() / (stl.seasonal + stl.resid).var())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p_adf = adfuller(serie)[1]
        p_kpss = kpss(serie, regression="c", nlags="auto")[1]

    st.markdown(
        f"Decomposição STL com período de 7 dias: força da tendência {num(f_tend, 2)} e "
        f"da sazonalidade semanal {num(f_saz, 2)} (de 0 a 1; abaixo de 0,4 é fraco). "
        f"ADF p {'< 0,001' if p_adf < 0.001 else '= ' + num(p_adf, 3)}; "
        f"KPSS p {'≥ 0,10' if p_kpss >= 0.1 else '= ' + num(p_kpss, 3)}; "
        f"Ljung-Box p = {num(lb.lb_pvalue.iloc[0], 2)} (7 dias) e {num(lb.lb_pvalue.iloc[1], 2)} (14 dias). "
        f"Kruskal-Wallis por dia da semana: p = {num(p_dia, 2)}."
    )
    partes = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                           subplot_titles=("Tendência", "Padrão semanal", "O que sobra (ruído)"))
    for i, comp in enumerate([stl.trend, stl.seasonal, stl.resid], start=1):
        partes.add_trace(go.Scatter(x=comp.index, y=comp.values, mode="lines", line=dict(color=ACO, width=1),
                                    hovertemplate="%{x|%d/%m/%Y}: %{y:,.1f}<extra></extra>"), row=i, col=1)
    estilo(partes, 460)
    partes.update_annotations(font_size=13, x=0, xanchor="left")
    mostrar(partes)

    st.markdown(
        "Comparação de modelos feita no notebook 02, com todas as minas e turnos, com divisão por data "
        "(treino até fev/26, validação mar–mai/26, teste jun–ago/26). Erro médio (MAE) em t/h; menor é melhor. "
        "O modelo foi escolhido na validação e avaliado uma única vez no teste. No notebook, o intervalo de 90% "
        "calibrado nos erros da validação foi de 165 a 185 t/h e cobriu 76% dos dias do teste, porque o teste "
        "variou mais. Por isso o painel usa a faixa dos próprios dias (5% a 95%), mais larga."
    )
    st.dataframe(
        pd.DataFrame(
            {
                "Modelo": ["Média histórica", "Holt-Winters", "SARIMA", "Random Forest",
                           "Média móvel de 7 dias", "Repetir o último dia", "Repetir a semana anterior"],
                "Validação (mar–mai/26)": [4.84, 4.82, 4.87, 5.03, 5.41, 6.73, 6.97],
                "Teste (jun–ago/26)": [5.89, 5.95, 5.91, 6.00, None, 8.99, 8.20],
            }
        ),
        hide_index=True,
        width="stretch",
    )
