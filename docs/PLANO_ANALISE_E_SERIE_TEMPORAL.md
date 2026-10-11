# Plano – Análise Estatística, Agrupamento e Série Temporal (Base 14 – Mineração)

Aula de 09/10/2026. Entrega: notebook aberto e apresentado ao professor, o mais perto possível da etapa final de série temporal. Prazo: ~2 semanas.

**Notebooks feitos:**
- `01_Dados_Limpeza_Estatistica_Agrupamento_Base14.ipynb`: tópicos 1 a 4 e conclusões;
- `02_Series_Temporais_Base14.ipynb`: tópico 5 e conclusões.

A numeração das perguntas nos notebooks (P1–P18) substitui a da seção 3 abaixo.

## 1. Notas da aula (resumo)

- A limpeza fecha aqui. Ela antecede qualquer análise.
- Cada algoritmo/análise responde uma pergunta. Primeiro o grupo conversa e lista **todas as perguntas possíveis** sobre o dado. Depois escolhe, no material do professor, o método que responde cada uma.
- **Não precisa usar tudo** do material. Só o que responde as nossas perguntas.
- Ordem: análise estatística → agrupamento (clustering) → série temporal.
- Série temporal: tratar o dado como série, extrair componentes (tendência, sazonalidade, resíduo). No material, a partir dos índices ~14–15 o conteúdo serve só para alguns casos. Filtrar o que serve.
- Exemplos do professor: bolsa (decidir vender ou não a ação) e jogadores ao longo do tempo (hora certa de comprar, "bom mas subaproveitado").
- Depois disso entra machine learning; redes neurais / deep learning só se alguma pergunta exigir.

## 2. O que o dado tem (base limpa)

- 9.850 registros de operação, 41 colunas.
- Período: 2025-01-01 a 2026-08-31 → **608 dias**, ~16 operações/dia, ~490/mês (volume estável).
- Dimensões: 6 minas (MG, GO, PA...), 6 frentes de lavra, 3 turnos, 4 tipos de minério, 5 escavadeiras, 8 caminhões, 1.497 operadores.
- Medidas: teor Fe/Si, umidade, granulometria, massas (extraída/processada/produto/rejeito), recuperação metalúrgica, distância, tempo de ciclo, viagens, diesel, energia, horas operação/parada, falhas, horas desde manutenção, custos, produtividade, CO2, índice de qualidade.
- Alvo natural: `status_operacao` (normal 7.186 / restrição 2.650 / crítica só 14 → muito desbalanceado) e `operacao_com_restricao` (0/1).

**Atenção para a série temporal:** 20 meses é pouco para sazonalidade anual (decomposição com período 12 exige no mínimo 24 pontos/2 ciclos). Usar série **diária** (sazonalidade semanal, período 7) ou **semanal** (~87 pontos). Mensal só para gráfico de tendência.

## 3. Perguntas → método

### 3.1 Estatística descritiva e inferencial

| # | Pergunta | Método |
|---|----------|--------|
| 1 | Qual mina/tipo de minério é mais produtiva e mais barata por tonelada? | groupby + média/mediana, boxplot, custo_operacional / massa_produto |
| 2 | Produtividade muda entre turnos (noite rende menos)? | ANOVA ou Kruskal-Wallis + post-hoc |
| 3 | Teor de Fe / sílica afeta a recuperação metalúrgica? | correlação Pearson/Spearman, regressão linear simples |
| 4 | Horas desde manutenção aumentam falhas e horas paradas? | correlação, scatter, regressão; teste qui-quadrado com faixas |
| 5 | Quais variáveis mais separam operação normal de com restrição? | teste t / Mann-Whitney por variável, heatmap de correlação |
| 6 | Distância de transporte explica diesel e CO2? | regressão linear; comparar diesel real vs estimado (erro do modelo atual) |
| 7 | Algum equipamento (escavadeira/caminhão) é outlier de falha ou custo? | boxplot, IQR, z-score por equipamento |
| 8 | Umidade/granulometria influenciam tempo de ciclo? | correlação, regressão múltipla |

### 3.2 Agrupamento (clustering)

| # | Pergunta | Método |
|---|----------|--------|
| 9 | Existem "perfis" de operação (ex.: alta produção/alto custo, baixa qualidade/alta restrição)? | K-Means (padronizar, método do cotovelo + silhouette), PCA para visualizar |
| 10 | Operadores formam grupos de desempenho? Há operador bom e subaproveitado? (analogia do jogador) | agregar por operador (produtividade, falhas, custo, nº de operações) → K-Means / hierárquico |
| 11 | Equipamentos se agrupam por padrão de desgaste? | agregar por equipamento → hierárquico (dendrograma) |

### 3.3 Série temporal

| # | Pergunta | Método |
|---|----------|--------|
| 12 | A produção (massa_produto_t) tem tendência ao longo do tempo? | resample diário/semanal, média móvel, decomposição (seasonal_decompose / STL) |
| 13 | Existe sazonalidade semanal (dia da semana) ou por mês (chuva → umidade)? | decomposição período 7; boxplot por dia da semana e mês |
| 14 | A série é estacionária? | teste ADF (e KPSS), diferenciação |
| 15 | Qual a dependência com o passado? | ACF / PACF → escolher ordens p, q |
| 16 | Dá para prever produção / custo / falhas das próximas semanas? | ARIMA/SARIMA (ou Holt-Winters); validar com treino/teste temporal (não aleatório), MAE/RMSE/MAPE |
| 17 | Quando parar um equipamento para manutenção? (analogia da bolsa: vender ou segurar) | série de falhas/paradas por equipamento + horas desde manutenção; sinal de alerta por média móvel / limite |
| 18 | O desempenho de cada operador melhora ou piora ao longo do tempo? (analogia do jogador) | série por operador (só os com volume), tendência via média móvel |

## 4. Estrutura do notebook

1. Carregar base limpa (`base_14_empresa_mineracao_limpa.csv`, `sep=';'`, `encoding='utf-8-sig'`, `parse_dates=['data_operacao']`).
2. Lista de perguntas do grupo (seção 3), em markdown.
3. Estatística descritiva + inferencial (perguntas 1–8), cada uma com gráfico e conclusão de 1–2 linhas.
4. Agrupamento (9–11): padronização, cotovelo/silhouette, interpretação dos clusters.
5. Série temporal (12–18): agregação, decomposição, ADF, ACF/PACF, modelo, previsão, métricas.
6. Conclusões: o que cada pergunta respondeu, quais ficam para a etapa de ML.

## 5. Divisão sugerida (2 semanas)

- Semana 1: reunião de perguntas, ler material do professor (marcar o que serve antes/depois dos índices 14–15), estatística + agrupamento.
- Semana 2: série temporal completa, revisão, ensaio da apresentação abrindo o notebook.
