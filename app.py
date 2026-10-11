"""Ponto de entrada: estilo, filtros (valem para todas as páginas) e menu de navegação."""
from pathlib import Path

import streamlit as st

from dados import barra_de_filtros, carregar

st.set_page_config(page_title="Painel da Mineração", page_icon=":material/landscape:", layout="wide")
st.html(Path(__file__).parent / "estilo.css")

st.session_state.recorte = barra_de_filtros(carregar())

# Menu na ordem dos notebooks: resumo, estatística (nb 01), agrupamento (nb 01), tempo (nb 02), sobre
st.navigation({
    "Resumo": [
        st.Page("pages/visao_geral.py", title="Como está a operação", icon=":material/landscape:", default=True),
        st.Page("pages/conclusoes.py", title="Conclusões e recomendações", icon=":material/flag:"),
    ],
    "Estatística": [
        st.Page("pages/distribuicao.py", title="Como os números se distribuem", icon=":material/bar_chart:"),
        st.Page("pages/comparacoes.py", title="Comparar grupos", icon=":material/compare_arrows:"),
        st.Page("pages/restricao.py", title="Problemas e custo", icon=":material/warning:"),
        st.Page("pages/explicacoes.py", title="O que explica os resultados", icon=":material/insights:"),
    ],
    "Agrupamento": [
        st.Page("pages/perfis.py", title="Perfis de operação", icon=":material/scatter_plot:"),
        st.Page("pages/equipamentos.py", title="Equipamentos e operadores", icon=":material/engineering:"),
        st.Page("pages/anomalias.py", title="Operações fora do padrão", icon=":material/report:"),
    ],
    "Ao longo do tempo": [
        st.Page("pages/tempo.py", title="Produtividade e previsão", icon=":material/show_chart:"),
        st.Page("pages/manutencao.py", title="Manutenção dos caminhões", icon=":material/local_shipping:"),
    ],
    "Sobre": [
        st.Page("pages/dados_limpeza.py", title="Dados e limpeza", icon=":material/cleaning_services:"),
        st.Page("pages/como_ler.py", title="Como ler este painel", icon=":material/help:"),
    ],
}, expanded=True).run()
