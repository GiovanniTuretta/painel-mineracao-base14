"""Visual padronizado de todas as páginas.

Regras: aço para o que importa, pó (cinza) para o contexto, linhas finas,
sem legenda quando há uma série só, números no padrão brasileiro.
As cores dos tipos de minério imitam a cor de cada rocha.
"""
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dados import num

ACO = "#2F5F8F"
PO = "#B4B8B2"
GRAFITE = "#22303C"
TEXTO_SUAVE = "#4F5B66"
FONTE = "Bahnschrift, 'Segoe UI', sans-serif"

# Perfis do K-means (validados para daltonismo com o script da skill de dataviz)
PERFIS = {
    "Minério rico, operação limpa": "#1F8A62",
    "Minério pobre": "#2A66B8",
    "Operação com falha": "#C25E1C",
}
LARANJA = "#C25E1C"  # destaque de alerta / fora do padrão (sempre com rótulo)

# Escala divergente para correlação: azul (negativa), cinza (zero), vermelho-óxido (positiva)
DIVERGENTE = [[0, "#2A66B8"], [0.5, "#E6E7E3"], [1, "#A8402A"]]

MINERIOS = {  # ordem fixa: a cor segue o minério, nunca a posição
    "Hematita": "#8A2F1D",
    "Magnetita": "#3A3D42",
    "Itabirito": "#6E7F8D",
    "Minério misto": "#B88A2E",
    "Não informado": "#D6D8D3",
}


def cabecalho(titulo, recorte, d):
    """Título, frase do recorte e a faixa de estratos (produção por tipo de minério)."""
    st.title(titulo)
    st.markdown(f'<p class="recorte">{escape(recorte)}</p>', unsafe_allow_html=True)
    if d.empty:
        return
    fatias = d.groupby("tipo_minerio").massa_produto_t.sum()
    fatias = (fatias / fatias.sum()).reindex(MINERIOS).dropna()
    camadas = "".join(
        f'<span style="flex:{p:.4f} 1 0;background:{MINERIOS[t]}"></span>' for t, p in fatias.items()
    )
    legenda = "".join(
        f'<span><i style="background:{MINERIOS[t]}"></i>{escape(t)} {num(p * 100)}%</span>' for t, p in fatias.items()
    )
    descricao = ", ".join(f"{t} {num(p * 100)}%" for t, p in fatias.items())
    st.markdown(
        f'<div class="estratos" role="img" aria-label="Produção por tipo de minério: {escape(descricao)}">{camadas}</div>'
        f'<div class="estratos-legenda" aria-hidden="true">{legenda}</div>',
        unsafe_allow_html=True,
    )


def paragrafo(texto, classe="abertura"):
    """Texto com **negrito** em markdown simples, dentro de um parágrafo estilizado."""
    partes = escape(texto).split("**")
    html = "".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(partes))
    st.markdown(f'<p class="{classe}">{html}</p>', unsafe_allow_html=True)


def estilo(fig, altura):
    fig.update_layout(
        height=altura,
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        font=dict(family=FONTE, color=TEXTO_SUAVE, size=13),
        separators=",.",
        hoverlabel=dict(font_size=14, font_family=FONTE),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    # automargin: a margem cresce para caber os rótulos dos eixos (sem isso, eles são cortados)
    fig.update_xaxes(title=None, showgrid=False, linecolor="#C9CCC6", automargin=True)
    fig.update_yaxes(title=None, gridcolor="#DADCD7", gridwidth=1, zeroline=False, automargin=True)
    return fig


_estilo = estilo


def mostrar(fig):
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def barras(tabela, rotulo, valor, unidade, casas, destaque=None, altura=None):
    """Barras deitadas, uma por grupo, com o valor na ponta.
    Com `destaque`, só ela fica em aço; as outras, em pó."""
    cores = [ACO if destaque is None or r == destaque else PO for r in tabela[rotulo]]
    textos = [f"{num(v, casas)} {unidade}" for v in tabela[valor]]
    fig = go.Figure(
        go.Bar(
            x=tabela[valor], y=tabela[rotulo], orientation="h",
            marker_color=cores, text=textos, textposition="outside", cliponaxis=False,
            textfont_color=GRAFITE,
            hovertemplate="<b>%{text}</b><br>%{y}<extra></extra>",
        )
    )
    fig.update_layout(barcornerradius=3, bargap=0.5)
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont_color=GRAFITE)
    fig.update_xaxes(visible=False, range=[0, tabela[valor].max() * 1.25])
    return estilo(fig, altura or 30 + 40 * len(tabela))  # ~20px por barra


def linha_tempo(serie, unidade, casas, altura=320):
    """Linha ao longo do tempo + linha de pó com a média do período."""
    media = serie.mean()
    fig = go.Figure(
        go.Scatter(
            x=serie.index, y=serie.values, mode="lines",
            line=dict(color=ACO, width=2),
            hovertemplate=f"Semana de %{{x|%d/%m/%Y}}<br><b>%{{y:,.{casas}f}} {unidade}</b><extra></extra>",
        )
    )
    # Ponto e rótulo no último valor: "onde estamos agora"
    fig.add_scatter(
        x=[serie.index[-1]], y=[serie.iloc[-1]], mode="markers+text",
        marker=dict(color=ACO, size=9, line=dict(width=2, color="#EEEFEC")),
        text=[f"{num(serie.iloc[-1], casas)} {unidade}"], textposition="middle right",
        textfont_color=GRAFITE, hoverinfo="skip", cliponaxis=False,
    )
    fig.add_hline(y=media, line_color=PO, line_width=1)
    # Eixo com folga de ±15% em torno da média: variação pequena parece pequena
    fig.update_yaxes(range=[min(serie.min(), media * 0.85), max(serie.max(), media * 1.15)])
    fig.update_layout(hovermode="x")
    fig.update_xaxes(tickformat="%d/%m/%y")
    estilo(fig, altura)
    fig.update_layout(margin_r=70)  # espaço para o rótulo do último ponto
    return fig


def historico_e_previsao(diario, movel, baixo, alto, previsao, anomalos=None, janela_dias=120, altura=380):
    """Cada dia (pó), a média móvel (aço), a faixa normal e os próximos dias previstos.
    Abre mostrando só os últimos `janela_dias`; o resto fica a um arraste de distância."""
    inicio, fim = diario.index[0], previsao.index[-1]
    vista_ini = max(inicio, diario.index[-1] - pd.Timedelta(days=janela_dias))
    na_vista = diario[vista_ini:]
    fig = go.Figure()
    # Faixa normal: onde caem 9 em cada 10 dias
    fig.add_scatter(
        x=[inicio, fim, fim, inicio], y=[baixo, baixo, alto, alto], fill="toself", mode="lines",
        fillcolor="rgba(47,95,143,0.09)", line_width=0, hoverinfo="skip",
    )
    fig.add_scatter(
        x=diario.index, y=diario.values, mode="lines", line=dict(color=PO, width=1),
        hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:,.0f} t/h</b> no dia<extra></extra>",
    )
    fig.add_scatter(
        x=movel.index, y=movel.values, mode="lines", line=dict(color=ACO, width=2),
        hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:,.0f} t/h</b> na média de 4 semanas<extra></extra>",
    )
    # Previsão: tracejada porque é projeção, não medição
    fig.add_scatter(
        x=previsao.index, y=previsao.values, mode="lines+markers",
        line=dict(color=ACO, width=2, dash="dot"), marker=dict(size=7, color=ACO),
        hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:,.0f} t/h</b> previstas<extra></extra>",
    )
    if anomalos is not None and len(anomalos):
        fig.add_scatter(
            x=anomalos.index, y=anomalos.values, mode="markers",
            marker=dict(color="rgba(0,0,0,0)", size=11, line=dict(color=LARANJA, width=2)),
            hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:,.0f} t/h</b>: dia fora do padrão<extra></extra>",
        )
    fig.add_vline(x=diario.index[-1], line_color="#C9CCC6", line_width=1)
    fig.add_annotation(
        x=previsao.index[len(previsao) // 2], y=alto, yshift=14, showarrow=False,
        text="próximos 7 dias", font_color=GRAFITE,
    )
    fig.add_annotation(
        x=vista_ini, y=alto, xanchor="left", yshift=14, showarrow=False,
        text=f"faixa normal: {num(baixo)} a {num(alto)} t/h", font_color=TEXTO_SUAVE,
    )
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(tickformat="%d/%m/%y", range=[vista_ini, fim + pd.Timedelta(days=3)])
    meio = (baixo + alto) / 2
    fig.update_yaxes(range=[min(na_vista.min(), meio * 0.85) - 3, max(na_vista.max(), meio * 1.15) + 3])
    return estilo(fig, altura)


def histograma(serie, unidade, casas=0, altura=300):
    """Distribuição de uma medida, com linhas da mediana (escura) e da média (clara)."""
    serie = serie.dropna()
    mediana, media = serie.median(), serie.mean()
    fig = go.Figure(go.Histogram(
        x=serie, nbinsx=60, marker_color=PO, marker_line_width=0,
        hovertemplate=f"%{{x}} {unidade}<br><b>%{{y}} operações</b><extra></extra>",
    ))
    fig.add_vline(x=mediana, line_color=ACO, line_width=2)
    fig.add_vline(x=media, line_color=GRAFITE, line_width=1, line_dash="dot")
    alto_mediana = "right" if mediana <= media else "left"
    fig.add_annotation(x=mediana, y=1, yref="paper", showarrow=False, xanchor=alto_mediana,
                       xshift=-6 if alto_mediana == "right" else 6,
                       text=f"típico {num(mediana, casas)}", font_color=ACO)
    if abs(media - mediana) > serie.std() * 0.05:
        fig.add_annotation(x=media, y=0.88, yref="paper", showarrow=False,
                           xanchor="left" if alto_mediana == "right" else "right",
                           xshift=6 if alto_mediana == "right" else -6,
                           text=f"média {num(media, casas)}", font_color=GRAFITE)
    fig.update_layout(bargap=0.04)
    return estilo(fig, altura)
