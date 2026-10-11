"""Carga da base, filtros compartilhados e textos em linguagem simples."""
from pathlib import Path

import pandas as pd
import streamlit as st

CSV = Path(__file__).parent / "base_14_empresa_mineracao_limpa.csv"
NORMAL = "Operação normal"

# Cada indicador com nome simples, unidade e o que significa.
# "agg": como resumir um grupo. Custo usa mediana porque tem valores extremos.
METRICAS = {
    "produtividade_t_h": dict(
        nome="Toneladas por hora", unidade="t/h", casas=0, maior_melhor=True, agg="mean",
        explica="Quanto minério é produzido, em média, a cada hora de trabalho. Quanto maior, melhor.",
    ),
    "custo_por_t": dict(
        nome="Custo por tonelada", unidade="R$/t", casas=2, maior_melhor=False, agg="median",
        explica="Quanto custa produzir 1 tonelada. Mostramos o valor típico (mediana), "
        "porque algumas operações muito caras puxariam a média para cima. Quanto menor, melhor.",
    ),
    "recuperacao_metalurgica_pct": dict(
        nome="Aproveitamento do minério", unidade="%", casas=1, maior_melhor=True, agg="mean",
        explica="De todo o ferro que entra na usina, quanto vira produto vendável. Quanto maior, melhor.",
    ),
    "horas_parada": dict(
        nome="Horas paradas", unidade="h", casas=1, maior_melhor=False, agg="mean",
        explica="Tempo médio em que os equipamentos ficaram parados em cada operação. Quanto menor, melhor.",
    ),
    "qtd_falhas_equipamento": dict(
        nome="Falhas de equipamento", unidade="falhas", casas=2, maior_melhor=False, agg="mean",
        explica="Número médio de falhas de máquina em cada operação. Quanto menor, melhor.",
    ),
}

GRUPOS = {"Turno": "turno", "Mina": "mina", "Tipo de minério": "tipo_minerio"}

PERIODOS = {
    "Últimos 3 meses": 3,
    "Últimos 6 meses": 6,
    "Últimos 12 meses": 12,
    "Todo o período": None,
    "Escolher datas": "datas",
}


@st.cache_data
def carregar():
    d = pd.read_csv(CSV, sep=";", encoding="utf-8-sig", parse_dates=["data_operacao"])
    d = d.sort_values("data_operacao").reset_index(drop=True)  # mesma ordem do notebook 01
    d["custo_por_t"] = d.custo_operacional_rs / d.massa_produto_t
    d["com_problema"] = d.status_operacao != NORMAL
    d["tipo_minerio"] = d.tipo_minerio.fillna("Não informado")
    return d


def num(x, casas=0):
    """Número no formato brasileiro: 1.234,5"""
    return f"{x:,.{casas}f}".translate(str.maketrans(",.", ".,"))


def toneladas(t, curto=False):
    """2323200 -> '2,3 milhões de t' (curto: '2,3 milhões'); 45200 -> '45,2 mil t'"""
    un = "" if curto else (" de t" if t >= 1e6 else " t")
    if t >= 1e6:
        return f"{num(t / 1e6, 1)} milhões{un}"
    return f"{num(t / 1e3, 1)} mil{un}" if t >= 1e3 else f"{num(t)}{un}"


def data_br(d):
    return pd.Timestamp(d).strftime("%d/%m/%Y")


def uma_em_cada(p):
    """0.27 -> '1 em cada 4'. Mais fácil de entender que porcentagem."""
    return f"1 em cada {round(1 / p)}" if p > 0 else "nenhuma"


def _todos_se_vazio(escolha, todos):
    return escolha or todos


def barra_de_filtros(df):
    """Desenha os filtros na barra lateral e devolve o recorte atual e o do período anterior."""
    base_ini, base_fim = df.data_operacao.min(), df.data_operacao.max()
    with st.sidebar:
        st.header("Filtros")
        st.caption("Valem para todas as páginas.")
        escolha = st.selectbox("Período", list(PERIODOS), key="periodo")
        meses = PERIODOS[escolha]
        if meses == "datas":
            datas = st.date_input("De / até", (base_ini, base_fim), base_ini, base_fim, format="DD/MM/YYYY", key="datas")
            ini, fim = (datas[0], datas[-1]) if datas else (base_ini, base_fim)
        elif meses is None:
            ini, fim = base_ini, base_fim
        else:
            fim = base_fim
            ini = base_fim - pd.DateOffset(months=meses) + pd.Timedelta(days=1)
        ini, fim = pd.Timestamp(ini), pd.Timestamp(fim)

        todas_minas = sorted(df.mina.unique())
        todos_turnos = ["Manhã", "Tarde", "Noite"]
        todos_tipos = sorted(df.tipo_minerio.unique())
        minas = _todos_se_vazio(st.multiselect("Minas", todas_minas, placeholder="Todas", key="minas"), todas_minas)
        turnos = _todos_se_vazio(st.multiselect("Turnos", todos_turnos, placeholder="Todos", key="turnos"), todos_turnos)
        tipos = _todos_se_vazio(st.multiselect("Tipo de minério", todos_tipos, placeholder="Todos", key="tipos"), todos_tipos)

    dims = df.mina.isin(minas) & df.turno.isin(turnos) & df.tipo_minerio.isin(tipos)
    atual = df[dims & df.data_operacao.between(ini, fim)]

    # Período anterior com a mesma duração, para comparar ("subiu ou caiu?")
    duracao = fim - ini
    ant_fim = ini - pd.Timedelta(days=1)
    ant_ini = ant_fim - duracao
    anterior = df[dims & df.data_operacao.between(ant_ini, ant_fim)] if ant_ini >= base_ini else None

    alcance = [
        "todas as minas" if len(minas) == len(todas_minas) else lista_pt(minas),
        "todos os turnos" if len(turnos) == 3 else f"turno da {lista_pt([t.lower() for t in turnos])}",
    ]
    if len(tipos) < len(todos_tipos):
        alcance.append(f"minério {lista_pt([t.lower() for t in tipos])}")
    periodo = f"De {data_br(ini)} a {data_br(fim)}, {lista_pt(alcance)}."
    descricao = periodo
    if anterior is not None:
        descricao += f" As setas comparam com {data_br(ant_ini)} a {data_br(ant_fim)}."
    return dict(
        atual=atual,
        anterior=anterior,
        historico=df[dims],  # sem corte de datas: para a página de série temporal
        descricao=descricao,  # com a frase das setas: só para a página que tem setas
        periodo=periodo,
        alcance=f"{lista_pt(alcance)[0].upper()}{lista_pt(alcance)[1:]}.",
    )


def lista_pt(itens):
    """['a', 'b', 'c'] -> 'a, b e c'"""
    itens = list(itens)
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def resumo(d, coluna):
    """Resume uma coluna do jeito definido em METRICAS (média ou mediana)."""
    return d[coluna].agg(METRICAS[coluna]["agg"])
