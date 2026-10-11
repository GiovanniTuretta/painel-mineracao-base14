"""Conclusões e recomendações dos notebooks 01 e 02 (base inteira)."""
import pandas as pd
import streamlit as st

from visual import paragrafo

st.title("Conclusões e recomendações")
st.markdown(
    '<p class="recorte">Respostas do grupo às 18 perguntas, com a base inteira (9.850 operações, jan/2025 a ago/2026). '
    "Os números das outras páginas mudam com os filtros; estes, não.</p>",
    unsafe_allow_html=True,
)

paragrafo(
    "A operação é **estável no tempo** e as minas são **parecidas entre si**. O que muda os resultados são duas coisas: "
    "o **turno da noite**, que rende 17 t/h a menos e tem 24% mais falhas, e a **falha de equipamento**, que dobra "
    "o custo por tonelada. Na usina, o aproveitamento depende do **tipo de minério**, não do teor de ferro isolado."
)

st.subheader("O que a empresa deve fazer")
recomendacoes = [
    ("Priorizar o turno da noite.",
     "É o maior fator que dá para controlar: −17 t/h, +24% de falhas e +16 pontos de operações com problema em "
     "relação à manhã. Investigar iluminação, fadiga e a equipe de manutenção noturna."),
    ("Reduzir falhas de equipamento.",
     "Elas são a causa direta das restrições e dobram o custo por tonelada (R$ 26,49 contra R$ 12,63)."),
    ("Planejar a usina pelo tipo de minério.",
     "Uma frente de itabirito perde cerca de 10 pontos de aproveitamento em relação à hematita."),
    ("Revisar como as horas desde a manutenção são registradas.",
     "Os dados mostram menos falhas longe da manutenção, o contrário do esperado. Confirmar antes de usar o campo."),
    ("Ajustar a estimativa de diesel em +1%.",
     "Ela subestima 0,65 L por operação, cerca de 3.800 L por ano."),
    ("Usar o detector de operações fora do padrão como alerta.",
     "Sem saber o status, ele encontrou 11 das 14 operações críticas."),
    ("Planejar a semana pela média histórica.",
     "176 t/h por dia, entre 165 e 185 t/h. Modelos complexos não preveem melhor."),
    ("Acompanhar os 23 operadores candidatos.",
     "Rendem acima da média do turno com poucas falhas, mas trabalharam pouco. Observar antes de dar mais escala."),
]
for i, (titulo, texto) in enumerate(recomendacoes, start=1):
    st.markdown(f"{i}. **{titulo}** {texto}")

st.subheader("As 18 perguntas")
respostas = pd.DataFrame([
    ("P1", "Como se distribuem produtividade, custo, aproveitamento e paradas?", "Produtividade simétrica (típico 174 t/h); custo com cauda longa, por isso usar a mediana (R$ 15,57/t).", "Como os números se distribuem"),
    ("P2", "Com que frequência a operação é crítica?", "0,14% (14 casos), cerca de 1 em 700; IC 95% de 0,09% a 0,24%.", "Como os números se distribuem"),
    ("P3", "O turno muda a produtividade?", "Sim. A noite rende 17,4 t/h a menos que a manhã (efeito médio, g = 0,60).", "Comparar grupos"),
    ("P4", "A mina muda a produtividade?", "Não na prática: diferença máxima de 1,9 t/h (p = 0,63).", "Comparar grupos"),
    ("P5", "Operação com problema custa mais?", "Sim: +R$ 13,74/t, quase o dobro (g = 1,33). O status é uma regra das falhas (vazamento).", "Problemas e custo"),
    ("P6", "O que se associa ao problema?", "Só o turno: noite 37% contra manhã 21%. Mina e minério, não.", "Problemas e custo"),
    ("P7", "Quais medidas andam juntas?", "5 pares redundantes (ex.: diesel e CO2). Horas paradas derrubam a produtividade.", "O que explica os resultados"),
    ("P8", "O que explica o aproveitamento?", "O tipo de minério (R² = 0,57). O teor de ferro só carrega essa informação.", "O que explica os resultados"),
    ("P9", "Mais horas sem manutenção geram mais falhas?", "Os dados mostram o contrário (−24% a cada 100 h). Provável causalidade reversa.", "O que explica os resultados"),
    ("P10", "A estimativa de diesel tem viés?", "Subestima 1% (0,65 L por operação).", "O que explica os resultados"),
    ("P11", "Existem perfis de operação?", "3 perfis: minério rico (R$ 12,63/t), minério pobre (R$ 17,15/t) e com falha (R$ 26,49/t).", "Perfis de operação"),
    ("P12", "Algum equipamento destoa?", "Não. Os 13 equipamentos são equivalentes (0,94 a 0,99 falha por operação).", "Equipamentos e operadores"),
    ("P13", "Há operadores bons e pouco aproveitados?", "23 candidatos, ainda com amostra pequena.", "Equipamentos e operadores"),
    ("P14", "Dá para achar casos graves sem o rótulo?", "Sim: 11 das 14 críticas entre as 99 operações fora do padrão.", "Operações fora do padrão"),
    ("P15", "A produtividade tem tendência ou ciclo?", "Não. Trimestres entre 175 e 177 t/h, sem padrão semanal ou mensal.", "Ao longo do tempo"),
    ("P16", "O dia de hoje ajuda a prever amanhã?", "Não: a série é ruído em torno da média e é estacionária.", "Ao longo do tempo"),
    ("P17", "Dá para prever a semana melhor que a média?", "Não. A média histórica venceu na validação e no teste (erro de 5,9 t/h).", "Ao longo do tempo"),
    ("P18", "Quando parar um caminhão?", "A regra está pronta; disparou só 1 vez (CAM-107).", "Manutenção dos caminhões"),
], columns=["#", "Pergunta", "Resposta", "Onde ver no painel"])
st.dataframe(respostas, hide_index=True, width="stretch", height=670,
             column_config={"Resposta": st.column_config.TextColumn(width="large")})

st.subheader("Limites desta análise")
st.markdown(
    "- **As operações não são totalmente independentes**: o mesmo equipamento e a mesma mina se repetem. "
    "Por isso as conclusões se apoiam no tamanho do efeito, não só no p-valor.\n"
    "- **20 meses não bastam para estudar a estação do ano** (chuva e seca); seriam precisos pelo menos 24.\n"
    "- **Cada operador tem cerca de 6 operações**, pouco para conclusões firmes por pessoa.\n"
    "- **A base parece simulada**: distribuições muito regulares, equipamentos idênticos, série sem padrão. "
    "Os métodos estão prontos para dados reais, mas os números valem só para esta base."
)

st.subheader("Próximos passos: machine learning")
st.markdown(
    "- Prever problema ou falha **sem usar falhas e custos como entrada** (seria vazamento). Usar só o que se sabe "
    "antes da operação: turno, tipo de minério, mina, frente, equipamento, horas desde a manutenção, distância.\n"
    "- Começar por regressão logística, depois árvores e Random Forest, com divisão por data e métricas para classes "
    "desbalanceadas (recall, F1, AUC-PR).\n"
    "- Prever o aproveitamento e o custo por tonelada.\n"
    "- Redes neurais só se esses modelos não bastarem; a estrutura dos dados é simples."
)
