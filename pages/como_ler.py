"""Página de ajuda: explica o painel para quem nunca viu um dashboard."""
import streamlit as st

from dados import METRICAS
from visual import MINERIOS

st.title("Como ler este painel")

st.markdown(
    """
O painel mostra a operação de **6 minas de ferro** entre janeiro de 2025 e agosto de 2026.
Cada **operação** é um ciclo de trabalho: escavar o minério, transportar e processar na usina.

#### O que tem em cada parte do menu
- **Resumo:** como a operação está agora e as conclusões finais do grupo.
- **Estatística:** como os números se espalham, quais grupos são diferentes de verdade, o que causa problema e custo.
- **Agrupamento:** perfis de operação que o computador encontrou sozinho, equipamentos, operadores e casos estranhos.
- **Ao longo do tempo:** se a produtividade muda, o que esperar na próxima semana e quando parar um caminhão.
- **Sobre:** de onde vêm os dados e como foram limpos.

#### Por onde começar
1. Escolha o **período** e, se quiser, as minas e os turnos na barra da esquerda. Por padrão aparecem os últimos 3 meses.
2. Leia o **texto de abertura** de cada página. Ele conta em frases o que aconteceu.
3. Olhe a **linha de números** logo abaixo. A seta compara com o período anterior de mesmo tamanho:
   verde quando melhorou, vermelho quando piorou. No custo e nos problemas, **cair é bom**,
   por isso aparecem em verde quando diminuem.
4. Os **gráficos** respondem à pergunta escrita no título de cada um.
5. Para conferir os números, abra as seções que ficam no fim da página.

#### A faixa colorida do topo
Ela mostra quanto da produção veio de cada tipo de minério, no recorte que você escolheu.
Cada cor imita a rocha:
"""
)
st.markdown("\n".join(f"- {t}" for t in MINERIOS))
st.markdown(
    """
#### Cores dos gráficos
- **Azul-aço** marca o que importa: a melhor mina, a linha principal.
- **Cinza-claro** é contexto: as outras minas, a média, cada dia isolado.

#### Os indicadores
"""
)
for m in METRICAS.values():
    st.markdown(f"- **{m['nome']} ({m['unidade']}).** {m['explica']}")
st.markdown(
    """
- **Operações com problema (%).** Parte das operações que teve restrição ou situação crítica. Quanto menor, melhor.

#### "Essa diferença é real?"
Quando o painel compara grupos, ele também faz um **teste estatístico**. O teste diz se a diferença
é grande o bastante para não ser só acaso.

#### Previsão
A página **Produtividade e previsão** mostra o que esperar nos próximos 7 dias. Ela e a página
**Manutenção dos caminhões** usam todo o histórico, por isso o filtro de período não vale nelas.

#### Perfis e operações fora do padrão
Essas duas páginas usam modelos treinados uma vez com a base inteira, como no notebook. Os filtros mudam
quais operações aparecem, mas não refazem os modelos. Na primeira vez em que o painel abre, o cálculo leva
alguns segundos.
"""
)
