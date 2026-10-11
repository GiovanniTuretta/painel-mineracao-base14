"""Manutenção dos caminhões (notebook 02, P18): sinal de parada, como ordem automática na bolsa."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from analises import FIM_TREINO, alerta_caminhoes
from dados import data_br, num
from visual import ACO, GRAFITE, LARANJA, PO, cabecalho, estilo, mostrar, paragrafo

r = st.session_state.recorte
h = r["historico"]
cabecalho(
    "Manutenção dos caminhões",
    f"Todo o histórico, como na página Produtividade e previsão. {r['alcance']} O filtro de período não vale aqui.",
    h,
)

sem, suave, limite, alertas = alerta_caminhoes(h)
if suave.dropna(how="all").empty or limite.isna().all():
    st.warning("Poucos dados por caminhão com esses filtros. Escolha mais minas, turnos ou tipos de minério.")
    st.stop()

ultima = suave.dropna(how="all").index[-1]
agora = suave.loc[ultima]
parar = agora > limite
total_alertas = int(alertas.sum().sum())

paragrafo(
    "Funciona como uma ordem automática na bolsa de valores. Enquanto a média de falhas do caminhão nas últimas "
    "4 semanas fica abaixo do limite, **segura**: o caminhão continua rodando. Quando passa do limite, **vende**: "
    "para o caminhão e faz manutenção preventiva. "
    f"Desde {data_br(FIM_TREINO + pd.Timedelta(days=1))}, a regra disparou **{total_alertas} "
    f"{'vez' if total_alertas == 1 else 'vezes'}**"
    + (f", só no {', '.join(alertas.columns[alertas.any()])}" if 0 < total_alertas else "")
    + ". Nesta base os caminhões se comportam igual, porque a falha depende do turno e não do desgaste."
)

# Quadro de situação: um caminhão por coluna, com ícone + palavra (nunca só cor)
st.subheader(f"Situação de cada caminhão até {data_br(h.data_operacao.max())}")
cols = st.columns(4, gap="medium")
for i, cam in enumerate(suave.columns):
    with cols[i % 4]:
        st.markdown(f"**{cam}**")
        if parar[cam]:
            st.markdown(":orange[:material/build: **Parar para revisão**]")
        else:
            st.markdown(":material/check_circle: Pode rodar")
        st.caption(f"{num(agora[cam], 2)} falhas por operação na média de 4 semanas. Limite: {num(limite[cam], 2)}.")

st.subheader("Falhas de cada caminhão, semana a semana")
st.caption(
    "Linha clara: falhas médias por operação em cada semana. Linha escura: média das últimas 4 semanas. "
    "Linha laranja tracejada: limite de alerta. Pontos laranja: semanas em que a regra mandaria parar."
)
grade = make_subplots(rows=2, cols=4, shared_yaxes=True, shared_xaxes=True, subplot_titles=list(suave.columns),
                      vertical_spacing=0.14, horizontal_spacing=0.03)
for i, cam in enumerate(suave.columns):
    lin, col = i // 4 + 1, i % 4 + 1
    grade.add_scatter(x=sem.index, y=sem[cam], mode="lines", line=dict(color=PO, width=1),
                      hovertemplate=f"{cam}<br>semana de %{{x|%d/%m/%Y}}<br>%{{y:.2f}} falhas<extra></extra>", row=lin, col=col)
    grade.add_scatter(x=suave.index, y=suave[cam], mode="lines", line=dict(color=ACO, width=2),
                      hovertemplate=f"{cam}<br>%{{x|%d/%m/%Y}}<br><b>%{{y:.2f}}</b> na média de 4 semanas<extra></extra>",
                      row=lin, col=col)
    grade.add_hline(y=limite[cam], line=dict(color=LARANJA, width=1, dash="dash"), row=lin, col=col)
    a = suave[cam][FIM_TREINO:][alertas[cam]]
    if not a.empty:
        grade.add_scatter(x=a.index, y=a.values, mode="markers", marker=dict(color=LARANJA, size=9),
                          hovertemplate=f"<b>{cam}: parar</b><br>%{{x|%d/%m/%Y}}<extra></extra>", row=lin, col=col)
    grade.add_vline(x=FIM_TREINO, line=dict(color="#C9CCC6", width=1), row=lin, col=col)
estilo(grade, 460)
grade.update_annotations(font_size=13, font_color=GRAFITE)
grade.update_layout(margin_t=30)  # espaço para o nome dos caminhões da primeira linha
grade.update_xaxes(tickformat="%m/%y", nticks=4)
mostrar(grade)
st.caption(f"A linha vertical fina marca {data_br(FIM_TREINO)}: o limite é calculado com os dados até ali, e os alertas valem depois.")

with st.expander("Detalhes técnicos"):
    st.markdown(
        "Para cada caminhão: média semanal de falhas por operação, suavizada por média móvel de 4 semanas "
        f"(mínimo 3). O limite é **média + 2 desvios** da série suavizada no período de treino (até {data_br(FIM_TREINO)}), "
        "a mesma divisão cronológica do notebook 02. Semana acima do limite depois do treino = sinal de parada."
    )
    st.dataframe(
        pd.DataFrame({
            "Limite": limite, "Média de 4 semanas agora": agora,
            "Semanas em alerta": alertas.sum(),
        }).round(3),
        width="stretch",
    )
