"""Dados e limpeza (notebook 01, tópicos 1 e 2)."""
import pandas as pd
import streamlit as st

from analises import NOMES, diagnostico_original
from dados import carregar, num
from visual import cabecalho, paragrafo

base = carregar()
d = diagnostico_original()

cabecalho(
    "Dados e limpeza",
    f"Base inteira: {num(len(base))} operações em {base.data_operacao.nunique()} dias, de 01/01/2025 a 31/08/2026.",
    base,
)

paragrafo(
    f"Cada linha é **uma operação de lavra**: um turno numa frente de lavra, com um operador, uma escavadeira e um "
    f"caminhão. A escavadeira tira o minério, o caminhão leva até a usina e a usina separa o produto do rejeito. "
    f"A base original tinha **{num(d['linhas'])} linhas** com problemas típicos de digitação; depois da limpeza "
    f"ficaram **{num(len(base))}**, sem nenhum dia faltando."
)

k1, k2, k3, k4 = st.columns(4, gap="medium")
k1.metric("Linhas duplicadas removidas", num(d["duplicadas"]))
k2.metric("Grafias de turno", f"{d['grafias']['turno']} viraram 3")
k3.metric("Grafias de minério", f"{d['grafias']['tipo_minerio']} viraram 4")
k4.metric("Grafias de status", f"{d['grafias']['status_operacao']} viraram 3")

st.subheader("O que estava errado e o que foi feito")
st.dataframe(
    pd.DataFrame([
        ("Linhas duplicadas", f"{d['duplicadas']} linhas", "Removidas", "A mesma operação contada duas vezes distorce médias e contagens."),
        ("Mesma categoria escrita de vários jeitos", "ex.: " + ", ".join(d["exemplos"]["turno"][:5]),
         "Texto padronizado e mapeado para o nome certo", "Sem isso, \"Manhã\" e \"MANHA\" seriam turnos diferentes."),
        ("Custo com \"R$\" e ponto de milhar", f"{d['com_rs']} valores", "Convertido para número", "O Python só entende 30037.21."),
        ("Datas no formato americano", f"{d['datas_eua']} datas só existem assim", "Tentado dia/mês; se falha, mês/dia", "Recupera a data sem perder a linha."),
        ("Valores fisicamente impossíveis", f"{int(d['impossiveis'].qtd.sum())} valores", "Transformados em vazio",
         "Limites do processo de mineração (ex.: ferro acima de 72% não existe), não da distribuição."),
        ("Aproveitamento vazio ou acima de 100%", "—", "Recalculado pelas massas", "É uma conta exata: produto ÷ processada × 100."),
        ("Demais vazios (cerca de 1% por coluna)", "—", "Mantidos vazios", "Preencher inventaria dados; cada análise trata do seu jeito."),
    ], columns=["Problema", "Quanto", "O que foi feito", "Por quê"]),
    hide_index=True, width="stretch",
)

c1, c2 = st.columns(2, gap="large")
with c1:
    st.subheader("Valores impossíveis na base original")
    st.dataframe(
        d["impossiveis"].rename(columns=dict(coluna="Medida", regra="Impossível quando", qtd="Encontrados", vazios="Vazios")),
        hide_index=True, width="stretch",
    )
with c2:
    st.subheader("Vazios que sobraram")
    vazios = base.drop(columns=["custo_por_t", "com_problema"]).isna().sum()
    vazios = vazios[vazios > 0].sort_values(ascending=False)
    st.dataframe(
        pd.DataFrame({"Vazios": vazios, "%": (vazios / len(base) * 100).round(2)}).rename(index=NOMES),
        width="stretch",
    )
    st.caption("Tipo de minério vazio aparece no painel como \"Não informado\".")

st.subheader("Verificações finais")
checks = {
    "Cada operação aparece uma vez só": base.registro_id.is_unique,
    "Turnos são só Manhã, Tarde e Noite": set(base.turno.dropna()) == {"Manhã", "Tarde", "Noite"},
    "Teor de ferro entre 0% e 72%": base.teor_fe_pct.dropna().between(0, 72).all(),
    "Aproveitamento entre 0% e 100%": base.recuperacao_metalurgica_pct.between(0, 100).all(),
    "Produto ≤ processado ≤ extraído": ((base.massa_produto_t <= base.massa_processada_t)
                                         & (base.massa_processada_t <= base.massa_extraida_t)).all(),
}
for texto, ok in checks.items():
    st.markdown(f"{':material/check_circle:' if ok else ':material/cancel:'} {texto}: **{'passou' if ok else 'falhou'}**")

with st.expander("Dicionário de dados"):
    st.dataframe(
        pd.DataFrame([
            ("registro_id", "Identificador da operação", "texto único"),
            ("data_operacao", "Dia da operação", "01/2025 a 08/2026"),
            ("mina, estado", "Mina e estado", "6 minas, 4 estados"),
            ("frente_lavra", "Frente de lavra dentro da mina", "F01 a F06"),
            ("turno", "Turno de trabalho", "Manhã, Tarde, Noite"),
            ("tipo_minerio", "Tipo de minério", "Hematita, Itabirito, Magnetita, Minério misto"),
            ("equipamento_escavacao", "Escavadeira", "ESC-01 a ESC-05"),
            ("equipamento_transporte", "Caminhão", "CAM-101 a CAM-108"),
            ("operador_id", "Operador", "1.497 operadores"),
            ("teor_fe_pct, teor_si_pct", "Teor de ferro e de sílica", "%"),
            ("umidade_minerio_pct", "Umidade do minério", "%"),
            ("granulometria_media_mm", "Tamanho médio das partículas", "mm"),
            ("massa_extraida/processada/produto_t", "Massa em cada etapa", "t"),
            ("recuperacao_metalurgica_pct", "Aproveitamento: produto ÷ processada × 100", "%"),
            ("rejeito_gerado_t", "Material descartado na usina", "t"),
            ("distancia, tempo_ciclo, qtd_viagens", "Transporte", "km, min, viagens"),
            ("consumo_diesel_l, _estimado_l", "Diesel real e estimado pela empresa", "L"),
            ("consumo_energia_kwh", "Energia elétrica", "kWh"),
            ("horas_operacao, horas_parada", "Tempo trabalhando e parado", "h"),
            ("qtd_falhas_equipamento", "Falhas na operação", "0 a 4"),
            ("horas_desde_manutencao", "Horas desde a última manutenção", "h"),
            ("custo_manutencao/operacional(_estimado)_rs", "Custos real e estimado", "R$"),
            ("produtividade_t_h", "Toneladas por hora de operação", "t/h"),
            ("emissao_co2_kg", "Emissão de CO2", "kg"),
            ("indice_qualidade_minerio", "Índice de qualidade", "0 a 100"),
            ("status_operacao", "Situação da operação", "normal, com restrição, crítica"),
            ("custo_por_t", "Custo operacional ÷ produto (criada na análise)", "R$/t"),
        ], columns=["Coluna", "Significado", "Unidade / valores"]),
        hide_index=True, width="stretch",
    )
