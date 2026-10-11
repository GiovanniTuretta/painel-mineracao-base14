"""Métodos dos notebooks 01 e 02, reaproveitados pelo painel.

Os testes rodam no recorte filtrado. Os modelos não supervisionados (PCA, K-means,
Isolation Forest) rodam uma vez na base inteira, como no notebook 01, e ficam em cache.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats
from scipy.cluster.hierarchy import linkage
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.oneway import anova_oneway
from statsmodels.stats.proportion import proportion_confint

from dados import carregar

SEED = 42
FIM_TREINO = pd.Timestamp("2026-02-28")  # mesma divisão cronológica do notebook 02

# Atributos do agrupamento (notebook 01, seção 4.1): sem identificadores, sem pares redundantes
ATRIB = [
    "teor_fe_pct", "teor_si_pct", "umidade_minerio_pct", "recuperacao_metalurgica_pct",
    "produtividade_t_h", "horas_parada", "qtd_falhas_equipamento", "custo_operacional_rs",
    "distancia_transporte_km", "massa_produto_t",
]

# Nomes simples para as colunas da base
NOMES = {
    "teor_fe_pct": "Teor de ferro (%)",
    "teor_si_pct": "Teor de sílica (%)",
    "umidade_minerio_pct": "Umidade (%)",
    "granulometria_media_mm": "Tamanho das partículas (mm)",
    "massa_extraida_t": "Massa extraída (t)",
    "massa_processada_t": "Massa processada (t)",
    "massa_produto_t": "Produto final (t)",
    "recuperacao_metalurgica_pct": "Aproveitamento do minério (%)",
    "rejeito_gerado_t": "Rejeito (t)",
    "distancia_transporte_km": "Distância de transporte (km)",
    "tempo_ciclo_min": "Tempo de ciclo (min)",
    "qtd_viagens": "Viagens",
    "consumo_diesel_l": "Diesel (L)",
    "consumo_energia_kwh": "Energia (kWh)",
    "horas_operacao": "Horas de operação",
    "horas_parada": "Horas paradas",
    "qtd_falhas_equipamento": "Falhas de equipamento",
    "horas_desde_manutencao": "Horas desde a manutenção",
    "custo_manutencao_rs": "Custo de manutenção (R$)",
    "custo_operacional_rs": "Custo operacional (R$)",
    "produtividade_t_h": "Toneladas por hora",
    "emissao_co2_kg": "Emissão de CO2 (kg)",
    "indice_qualidade_minerio": "Índice de qualidade",
    "custo_por_t": "Custo por tonelada (R$/t)",
    "com_problema": "Com problema",
}


# ---------- Estatística (notebook 01, tópico 3) ----------

def hedges_g(a, b):
    """Tamanho do efeito: diferença de médias em desvios-padrão, com correção para amostra pequena."""
    a, b = np.asarray(a), np.asarray(b)
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return (a.mean() - b.mean()) / sp * (1 - 3 / (4 * (na + nb) - 9))


def tamanho(g):
    """Hedges g em palavras (convenção de Cohen)."""
    g = abs(g)
    return "desprezível" if g < 0.2 else "pequeno" if g < 0.5 else "médio" if g < 0.8 else "grande"


def cramer(tab):
    """Qui-quadrado de independência + V de Cramér (0 = sem associação, 1 = total)."""
    chi2, p, gl, _ = stats.chi2_contingency(tab)
    v = np.sqrt(chi2 / (tab.values.sum() * (min(tab.shape) - 1)))
    return chi2, p, gl, v


def wilson(k, n):
    """Proporção com intervalo de confiança de 95% de Wilson (bom para eventos raros)."""
    li, ls = proportion_confint(k, n, alpha=0.05, method="wilson")
    return k / n, li, ls


def comparar(f, coluna, grupo):
    """Levene, ANOVA de Welch, Kruskal-Wallis e pós-teste par a par (Welch + Holm + Hedges g)."""
    grupos = {nome: g[coluna].dropna() for nome, g in f.groupby(grupo)}
    amostras = list(grupos.values())
    kw = stats.kruskal(*amostras)
    nomes = list(grupos)
    pares = []
    for i in range(len(nomes)):
        for j in range(i + 1, len(nomes)):
            (na, a), (nb, b) = (nomes[i], grupos[nomes[i]]), (nomes[j], grupos[nomes[j]])
            if a.mean() < b.mean():  # sempre "maior × menor": diferença positiva, mais fácil de ler
                (na, a), (nb, b) = (nb, b), (na, a)
            pares.append(dict(
                par=f"{na} × {nb}",
                diferenca=a.mean() - b.mean(),
                g=hedges_g(a, b),
                p=stats.ttest_ind(a, b, equal_var=False).pvalue,
            ))
    pares = pd.DataFrame(pares)
    pares["p_holm"] = multipletests(pares.p, method="holm")[1]
    pares["efeito"] = pares.g.map(tamanho)
    return dict(
        levene=stats.levene(*amostras, center="median").pvalue,
        welch=anova_oneway(amostras, use_var="unequal").pvalue,
        kruskal_h=kw.statistic,
        kruskal_p=kw.pvalue,
        pares=pares.reindex(pares.diferenca.abs().sort_values(ascending=False).index),
    )


def p_txt(p):
    """p-valor legível: '< 0,001' ou '= 0,123'."""
    return "< 0,001" if p < 0.001 else f"= {p:.3f}".replace(".", ",")


# ---------- Agrupamento e anomalias (notebook 01, tópico 4) ----------

# persist="disk": o resultado fica salvo e não é recalculado a cada vez que o painel abre
@st.cache_data(show_spinner="Calculando perfis e anomalias (só na primeira vez, leva alguns segundos)...", persist="disk")
def nao_supervisionado():
    # Sem argumento: o cache não precisa gerar hash da tabela inteira a cada chamada (era o que demorava)
    df = carregar()
    X = df[ATRIB].fillna(df[ATRIB].median())
    Z = StandardScaler().fit_transform(X)

    pca = PCA(random_state=SEED).fit(Z)
    P = pca.transform(Z)[:, :2]

    escolha = []
    for k in range(2, 9):
        km_k = KMeans(k, n_init=10, random_state=SEED).fit(Z)
        escolha.append(dict(
            k=k, inercia=km_k.inertia_,
            silhueta=silhouette_score(Z, km_k.labels_, sample_size=4000, random_state=SEED),
            davies_bouldin=davies_bouldin_score(Z, km_k.labels_),
            calinski_harabasz=calinski_harabasz_score(Z, km_k.labels_),
        ))

    km = KMeans(3, n_init=10, random_state=SEED).fit(Z)
    rotulos = [KMeans(3, n_init=10, random_state=s).fit_predict(Z) for s in range(5)]
    ari = [adjusted_rand_score(rotulos[0], r) for r in rotulos[1:]]

    # Os números do K-means são arbitrários; o nome vem do que cada grupo tem de típico
    medias = pd.DataFrame(X).groupby(km.labels_).mean()
    falha = medias.qtd_falhas_equipamento.idxmax()
    resto = medias.drop(falha)
    rico = resto.teor_fe_pct.idxmax()
    nome = {falha: "Operação com falha", rico: "Minério rico, operação limpa"}
    perfil = pd.Series([nome.get(l, "Minério pobre") for l in km.labels_], index=df.index)

    iso = IsolationForest(contamination=0.01, random_state=SEED).fit(Z)

    return dict(
        perfil=perfil,
        pc1=pd.Series(P[:, 0], index=df.index),
        pc2=pd.Series(P[:, 1], index=df.index),
        variancia=pca.explained_variance_ratio_,
        cargas=pd.DataFrame(pca.components_[:3].T, index=ATRIB, columns=["PC1", "PC2", "PC3"]),
        escolha_k=pd.DataFrame(escolha).set_index("k"),
        ari=ari,
        anomalia=pd.Series(iso.predict(Z) == -1, index=df.index),
        estranheza=pd.Series(-iso.score_samples(Z), index=df.index),
    )


def equipamentos(f):
    """Médias por escavadeira e caminhão + ligação hierárquica (Ward) sobre as médias padronizadas."""
    at = ["qtd_falhas_equipamento", "horas_parada", "custo_manutencao_rs", "produtividade_t_h", "tempo_ciclo_min"]
    eq = pd.concat([
        f.groupby("equipamento_escavacao")[at].mean(),
        f.groupby("equipamento_transporte")[at].mean(),
    ])
    return eq, linkage(StandardScaler().fit_transform(eq), method="ward")


def operadores(df, minimo=8):
    """Analogia do jogador: produtividade acima da média do próprio turno, poucas falhas e pouca escala."""
    d = df.assign(prod_vs_turno=df.produtividade_t_h - df.groupby("turno").produtividade_t_h.transform("mean"))
    op = d.groupby("operador_id").agg(
        n_operacoes=("registro_id", "count"),
        prod_vs_turno=("prod_vs_turno", "mean"),
        falhas_media=("qtd_falhas_equipamento", "mean"),
        custo_por_t=("custo_por_t", "median"),
    )
    op8 = op[op.n_operacoes >= minimo].copy()
    lim_prod = op8.prod_vs_turno.quantile(0.8)
    lim_fal = op8.falhas_media.quantile(0.2)
    mediana_n = op8.n_operacoes.median()
    op8["candidato"] = (op8.prod_vs_turno >= lim_prod) & (op8.falhas_media <= lim_fal) & (op8.n_operacoes <= mediana_n)
    return op, op8, dict(lim_prod=lim_prod, lim_fal=lim_fal, mediana_n=mediana_n)


# ---------- Manutenção (notebook 02, P18) ----------

def alerta_caminhoes(h):
    """Falhas médias por semana e caminhão, média móvel de 4 semanas e limite = média + 2 desvios do treino."""
    sem = (
        h.groupby([pd.Grouper(key="data_operacao", freq="W"), "equipamento_transporte"])
        .qtd_falhas_equipamento.mean()
        .unstack()
    )
    suave = sem.rolling(4, min_periods=3).mean()
    treino = suave[:FIM_TREINO]
    limite = treino.mean() + 2 * treino.std()
    alertas = suave[FIM_TREINO:] > limite
    return sem, suave, limite, alertas


# ---------- Limpeza (notebook 01, tópico 2) ----------

@st.cache_data
def diagnostico_original():
    """Problemas da base original, lida toda como texto para nenhuma conversão esconder erro."""
    caminho = Path(__file__).parent / "base_14_empresa_mineracao_original.csv"
    orig = pd.read_csv(caminho, sep=";", dtype=str, encoding="utf-8-sig")

    def para_numero(s):
        return pd.to_numeric(s.str.replace("R$", "", regex=False).str.replace(" ", ""), errors="coerce")

    regras = {
        "teor_fe_pct": ("acima de 72% (máximo físico do ferro)", lambda x: x > 72),
        "umidade_minerio_pct": ("acima de 30%", lambda x: x > 30),
        "indice_qualidade_minerio": ("acima de 100", lambda x: x > 100),
        "recuperacao_metalurgica_pct": ("acima de 100%", lambda x: x > 100),
        "distancia_transporte_km": ("negativa", lambda x: x < 0),
        "consumo_diesel_l": ("negativo", lambda x: x < 0),
        "horas_desde_manutencao": ("negativa", lambda x: x < 0),
    }
    impossiveis = pd.DataFrame([
        dict(coluna=NOMES.get(c, c), regra=txt, qtd=int(regra(para_numero(orig[c])).sum()), vazios=int(orig[c].isna().sum()))
        for c, (txt, regra) in regras.items()
    ])
    partes = orig.data_operacao.str.split("/", expand=True).astype(int)
    return dict(
        linhas=len(orig),
        colunas=orig.shape[1],
        duplicadas=int(orig.duplicated().sum()),
        grafias={c: orig[c].nunique() for c in ["turno", "tipo_minerio", "status_operacao"]},
        exemplos={c: orig[c].dropna().unique()[:8].tolist() for c in ["turno", "tipo_minerio", "status_operacao"]},
        com_rs=int(orig.custo_operacional_rs.str.contains("R$", regex=False, na=False).sum()),
        datas_eua=int((partes[1] > 12).sum()),
        impossiveis=impossiveis,
    )
