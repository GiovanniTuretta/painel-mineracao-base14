# Base 14 — Mineração: análise e dashboard

PI Engenharia da Computação — FHO, 6º semestre.

## Estrutura

| Item | O que é |
|---|---|
| `01_...Estatistica_Agrupamento_Base14.ipynb` | Notebook 1: limpeza, estatística, agrupamento (P1–P14) |
| `02_Series_Temporais_Base14.ipynb` | Notebook 2: séries temporais (P15–P18) |
| `Limpeza_de_Dados_Base14_Mineracao.ipynb` | Limpeza completa da base |
| `base_14_empresa_mineracao_limpa.csv` | Base oficial do app (9.850 linhas) |
| `base_14_empresa_mineracao_original.csv` | Base bruta |
| `dados_prontos_ml_*.csv` | Treino/teste para a etapa de ML |
| `app.py` | Entrada do dashboard: filtros (valem para todas as páginas) e menu |
| `dados.py` | Carga da base, filtros, nomes simples dos indicadores, formatação brasileira |
| `analises.py` | Métodos dos notebooks: testes, regressões, K-means, PCA, Isolation Forest, alerta dos caminhões |
| `visual.py` | Cabeçalho com faixa de minério e gráficos padronizados (aço = destaque, cinza = contexto) |
| `estilo.css` | Ajustes visuais que o tema do Streamlit não cobre |
| `pages/` | 13 páginas, uma por bloco de perguntas (ver abaixo) |
| `.streamlit/config.toml` | Tema: cores, letra Bahnschrift, cantos |
| `docs/` | Plano de análise, PDF da análise inicial, schema SQL |

Os notebooks leem os CSVs pelo nome, na mesma pasta. Não mover os CSVs sem ajustar `CAMINHO` neles.

## Rodar

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Abre em http://localhost:8501.

No PowerShell, rodar um comando por linha (o `&&` não funciona no PowerShell 5).

## Publicar no Streamlit Community Cloud

1. Enviar esta pasta para um repositório público no GitHub (o `.gitignore` já deixa de fora o `.venv` e os arquivos que o painel não usa).
2. Em [share.streamlit.io](https://share.streamlit.io), **Create app** → **Deploy a public app from GitHub**.
3. Repositório: o deste projeto; branch `main`; arquivo principal `app.py`.
4. Em **Advanced settings**, escolher **Python 3.13** (a mesma versão testada).
5. **Deploy**. A primeira instalação leva alguns minutos. Depois, todo `git push` atualiza o app sozinho.

As versões das bibliotecas estão travadas no `requirements.txt` com as mesmas usadas nos testes.

## Regras de design (para qualquer pessoa entender)

- **Pirâmide invertida:** texto de abertura no topo, depois a linha de números, os gráficos e, no fim, a tabela escondida.
- **Regra dos 5 segundos:** o texto de abertura responde "como estamos?" sem precisar ler gráfico.
- **Todo número tem contexto:** unidade, comparação com o período anterior e explicação no ícone `?`.
- **Linguagem simples:** nada de nome de coluna; termos técnicos só em "Detalhes técnicos".
- **Cor com função:** azul-aço = o que importa, cinza = contexto; verde/vermelho só para melhorou/piorou.
- **Eixos honestos:** barras começam no zero; linha com folga de ±15% para variação pequena parecer pequena.

## Identidade visual

Pensada para não parecer template:

- **Letra:** Bahnschrift, a DIN que já vem no Windows (letra de placa industrial). Funciona sem internet.
- **Cores da rocha:** fundo cinza-mineral `#EEEFEC`, texto grafite `#22303C`, dado em aço `#2F5F8F`.
- **Faixa de estratos** no topo de cada página: cada camada é a parte da produção de um tipo de minério
  (hematita, magnetita, itabirito, misto), na cor da própria rocha. É o único elemento decorativo, e mesmo ele traz dado.
- **Sem cartões nem sombras:** números separados por linhas finas; conclusões em frase, com uma barra lateral.
- **Sem emoji:** ícones Material no menu.

## Páginas

Cada pergunta dos notebooks (P1 a P18) tem uma seção, com o mesmo método.

| Menu | Página | Arquivo | Perguntas |
|---|---|---|---|
| Resumo | Como está a operação | `visao_geral.py` | visão geral |
| Resumo | Conclusões e recomendações | `conclusoes.py` | todas (base inteira) |
| Estatística | Como os números se distribuem | `distribuicao.py` | P1, P2 |
| Estatística | Comparar grupos | `comparacoes.py` | P3, P4 |
| Estatística | Problemas e custo | `restricao.py` | P5, P6, vazamento |
| Estatística | O que explica os resultados | `explicacoes.py` | P7, P8, P9, P10 |
| Agrupamento | Perfis de operação | `perfis.py` | P11 |
| Agrupamento | Equipamentos e operadores | `equipamentos.py` | P12, P13 |
| Agrupamento | Operações fora do padrão | `anomalias.py` | P14 |
| Ao longo do tempo | Produtividade e previsão | `tempo.py` | P15, P16, P17 |
| Ao longo do tempo | Manutenção dos caminhões | `manutencao.py` | P18 |
| Sobre | Dados e limpeza | `dados_limpeza.py` | tópicos 1 e 2 |
| Sobre | Como ler este painel | `como_ler.py` | ajuda |

Testes e gráficos respeitam os filtros. Perfis e anomalias usam modelos treinados uma vez na base inteira
(como no notebook), guardados em cache. As páginas de tempo usam o histórico inteiro.
