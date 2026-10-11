"""O que explica os resultados (notebook 01, P7 a P10)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import statsmodels.api as sm
import statsmodels.formula.api as smf
import streamlit as st
from scipy import stats

from analises import NOMES, p_txt
from dados import num
from visual import ACO, DIVERGENTE, GRAFITE, MINERIOS, PO, barras, cabecalho, estilo, histograma, mostrar, paragrafo

r = st.session_state.recorte
f = r["atual"]
cabecalho("O que explica os resultados", r["periodo"], f)
if len(f) < 100:
    st.warning("Os modelos desta página precisam de pelo menos 100 operações. Escolha um período maior ou mais minas.")
    st.stop()

paragrafo(
    "Quatro perguntas sobre causas. O que derruba a produtividade são as **horas paradas**, não a qualidade do minério. "
    "O aproveitamento na usina depende do **tipo de minério**. As falhas se concentram **à noite**. "
    "E a estimativa de diesel da empresa erra **um pouco para menos**."
)

aba1, aba2, aba3, aba4 = st.tabs([
    "O que anda junto", "Aproveitamento do minério", "Falhas e manutenção", "Estimativa de diesel",
])

# ---- P7: Spearman ----
with aba1:
    NUM = [
        "teor_fe_pct", "teor_si_pct", "umidade_minerio_pct", "granulometria_media_mm", "massa_extraida_t",
        "massa_produto_t", "recuperacao_metalurgica_pct", "rejeito_gerado_t", "distancia_transporte_km",
        "tempo_ciclo_min", "qtd_viagens", "consumo_diesel_l", "consumo_energia_kwh", "horas_operacao",
        "horas_parada", "qtd_falhas_equipamento", "horas_desde_manutencao", "custo_manutencao_rs",
        "custo_operacional_rs", "produtividade_t_h", "emissao_co2_kg", "indice_qualidade_minerio",
    ]
    corr = f[NUM].corr(method="spearman")
    rotulos = [NOMES[c] for c in NUM]
    st.subheader("Quais medidas sobem e descem juntas?")
    st.caption(
        "Vermelho: quando uma sobe, a outra também sobe. Azul: quando uma sobe, a outra desce. "
        "Cinza: não têm relação. Passe o mouse para ver o valor (de −1 a +1)."
    )
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=rotulos, y=rotulos, zmin=-1, zmax=1, colorscale=DIVERGENTE,
        hovertemplate="%{y}<br>%{x}<br><b>%{z:.2f}</b><extra></extra>", xgap=1, ygap=1,
        colorbar=dict(thickness=10, len=0.6, tickvals=[-1, 0, 1], ticktext=["−1", "0", "+1"]),
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(tickangle=-45)
    mostrar(estilo(fig, 640))

    pares = corr.where(np.triu(np.ones(corr.shape, dtype=bool), 1)).stack()
    fortes = pares[pares.abs() > 0.9].sort_values(key=abs, ascending=False)
    rho_parada = corr.loc["produtividade_t_h", "horas_parada"]
    rho_fe = corr.loc["produtividade_t_h", "teor_fe_pct"]
    paragrafo(
        f"A produtividade quase não tem relação com a qualidade do minério ({num(rho_fe, 2)} com o teor de ferro). "
        f"O que a derruba são as **horas paradas** ({num(rho_parada, 2)}). "
        f"Há também **{len(fortes)} pares que medem praticamente a mesma coisa** (acima de 0,9), "
        "por isso o agrupamento usa só uma medida de cada par.",
        "veredito",
    )
    st.dataframe(
        pd.DataFrame({
            "Medida A": [NOMES[a] for a, _ in fortes.index],
            "Medida B": [NOMES[b] for _, b in fortes.index],
            "Correlação": fortes.values.round(3),
        }),
        hide_index=True, width="stretch",
    )
    with st.expander("Detalhes técnicos"):
        st.markdown(
            "Correlação de **Spearman**: mede relação que só sobe ou só desce (monotônica) e resiste a valores extremos. "
            "|ρ| > 0,9 indica redundância: diesel × CO2 (o CO2 é calculado do diesel), teor de ferro × índice de "
            "qualidade, massa extraída × produto, custo de manutenção × custo operacional."
        )

# ---- P8: recuperação ----
with aba2:
    d = f[f.tipo_minerio != "Não informado"]
    st.subheader("O que define o aproveitamento do minério na usina?")
    por_tipo = d.groupby("tipo_minerio").recuperacao_metalurgica_pct.mean().sort_values(ascending=False)
    # Referência = hematita quando ela está no recorte; com um tipo só, o termo de tipo sai do modelo
    tipos = set(d.tipo_minerio)
    termo_tipo = (
        " + C(tipo_minerio, Treatment('Hematita'))" if "Hematita" in tipos and len(tipos) > 1
        else " + C(tipo_minerio)" if len(tipos) > 1 else ""
    )
    m_rec = smf.ols(
        "recuperacao_metalurgica_pct ~ teor_fe_pct + teor_si_pct + umidade_minerio_pct"
        " + granulometria_media_mm" + termo_tipo,
        data=d,
    ).fit(cov_type="HC3")
    m_fe = smf.ols("recuperacao_metalurgica_pct ~ teor_fe_pct", data=d).fit(cov_type="HC3")

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.caption("Cada ponto é uma operação, na cor do tipo de minério. Mostramos até 3.000 pontos sorteados.")
        amostra = d.sample(min(3000, len(d)), random_state=42)
        fig = go.Figure()
        for tipo, cor in MINERIOS.items():
            x = amostra[amostra.tipo_minerio == tipo]
            if x.empty:
                continue
            fig.add_scatter(
                x=x.teor_fe_pct, y=x.recuperacao_metalurgica_pct, mode="markers", name=tipo,
                marker=dict(color=cor, size=5, opacity=0.55, line=dict(width=0)),
                hovertemplate=f"{tipo}<br>Ferro %{{x:.1f}}%<br>Aproveitamento <b>%{{y:.1f}}%</b><extra></extra>",
            )
        estilo(fig, 380)
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=0))
        fig.update_xaxes(title="Teor de ferro (%)")
        fig.update_yaxes(title="Aproveitamento (%)")
        mostrar(fig)
    with c2:
        mostrar(barras(por_tipo.rename("rec").reset_index(), "tipo_minerio", "rec", "%", 1, destaque=por_tipo.index[0]))
        p_fe = m_rec.pvalues["teor_fe_pct"]
        paragrafo(
            f"**O que manda é o tipo de minério.** A hematita aproveita {num(por_tipo.get('Hematita', np.nan), 1)}%; "
            f"o itabirito, {num(por_tipo.get('Itabirito', np.nan), 1)}%. "
            "Parece que mais ferro dá mais aproveitamento, mas é porque cada tipo de minério tem sua própria faixa de ferro. "
            + (
                "Comparando dentro do mesmo tipo, mais ferro não aumenta o aproveitamento."
                if p_fe >= 0.05
                else "Mesmo dentro do mesmo tipo, o ferro ainda pesa um pouco."
            ),
            "veredito",
        )

    with st.expander("Detalhes técnicos"):
        st.markdown(
            f"Regressão linear múltipla com erros **HC3** (protegem contra variância desigual). "
            f"R² = {num(m_rec.rsquared, 3)} com o tipo de minério; R² = {num(m_fe.rsquared, 3)} só com o teor de ferro. "
            f"Coeficiente do ferro: {num(m_fe.params['teor_fe_pct'], 3)} sozinho e {num(m_rec.params['teor_fe_pct'], 3)} "
            f"(p {p_txt(p_fe)}) com o tipo no modelo. Isso é **associação condicionada**: o ferro só carregava a informação do tipo."
        )
        coef = pd.DataFrame({"Coeficiente": m_rec.params, "IC 2,5%": m_rec.conf_int()[0], "IC 97,5%": m_rec.conf_int()[1], "p": m_rec.pvalues})
        coef.index = [
            i.replace("C(tipo_minerio, Treatment('Hematita'))[T.", "Tipo: ").replace("C(tipo_minerio)[T.", "Tipo: ").replace("]", "")
            for i in coef.index
        ]
        coef.index = [NOMES.get(i, i) for i in coef.index]
        st.dataframe(coef.assign(p=coef.p.map(p_txt)).round(3), width="stretch")
        st.dataframe(
            d.groupby("tipo_minerio")[["teor_fe_pct", "teor_si_pct", "recuperacao_metalurgica_pct"]]
            .agg(["mean", "std"]).round(2),
            width="stretch",
        )

# ---- P9: falhas ----
with aba3:
    st.subheader("Mais horas sem manutenção trazem mais falhas?")
    turnos = set(f.turno)
    termo_turno = (
        " + C(turno, Treatment('Manhã'))" if "Manhã" in turnos and len(turnos) > 1
        else " + C(turno)" if len(turnos) > 1 else ""
    )
    m_fal = smf.glm(
        "qtd_falhas_equipamento ~ horas_desde_manutencao + horas_operacao" + termo_turno,
        data=f, family=sm.families.Poisson(),
    ).fit()
    irr = np.exp(m_fal.params)
    faixas = pd.cut(f.horas_desde_manutencao, [0, 50, 100, 150, 200, f.horas_desde_manutencao.max()])
    por_faixa = f.groupby(faixas, observed=True).qtd_falhas_equipamento.mean()
    por_faixa.index = [f"{int(i.left)} a {int(i.right)} h" for i in por_faixa.index]

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.caption("Falhas médias por operação, conforme as horas desde a última manutenção.")
        mostrar(barras(por_faixa.rename("falhas").rename_axis("faixa").reset_index(), "faixa", "falhas", "falhas", 2, destaque=""))
    with c2:
        efeito_100 = (irr["horas_desde_manutencao"] ** 100 - 1) * 100
        noite = (irr.get("C(turno, Treatment('Manhã'))[T.Noite]", np.nan) - 1) * 100
        paragrafo(
            f"**Os dados mostram o contrário do esperado.** A cada 100 horas a mais desde a manutenção, as falhas "
            f"{'caem' if efeito_100 < 0 else 'sobem'} cerca de {num(abs(efeito_100))}%. "
            "A explicação mais provável é que máquinas que quebram muito vão mais vezes para a oficina e por isso "
            "aparecem sempre com poucas horas desde a última manutenção. "
            "**Não use este resultado para espaçar manutenções** antes de confirmar com a empresa como esse campo é registrado.",
            "veredito incerto",
        )
        if not np.isnan(noite):
            st.caption(f"O turno pesa mais: à noite há {num(noite)}% mais falhas que de manhã, nas mesmas condições.")

    with st.expander("Detalhes técnicos"):
        disp = m_fal.pearson_chi2 / m_fal.df_resid
        st.markdown(
            "Falhas são contagens (0, 1, 2…), então o modelo é uma **regressão de Poisson**. "
            "A razão de taxas mostra quanto a taxa de falhas muda: 1,24 = 24% a mais. "
            f"Dispersão (Pearson χ²/gl) = {num(disp, 2)}: "
            + ("abaixo de 1, os dados variam menos que o esperado e os erros padrão ficam conservadores." if disp < 1
               else "perto ou acima de 1.")
        )
        tab = pd.DataFrame({
            "Razão de taxas": irr, "Efeito (%)": (irr - 1) * 100,
            "IC 2,5%": np.exp(m_fal.conf_int()[0]), "IC 97,5%": np.exp(m_fal.conf_int()[1]), "p": m_fal.pvalues,
        })
        tab.index = [
            NOMES.get(i, i.replace("C(turno, Treatment('Manhã'))[T.", "Turno: ").replace("C(turno)[T.", "Turno: ").replace("]", ""))
            for i in tab.index
        ]
        st.dataframe(tab.assign(p=tab.p.map(p_txt)).round(4), width="stretch")

# ---- P10: diesel ----
with aba4:
    st.subheader("A estimativa de diesel da empresa acerta?")
    erro = (f.consumo_diesel_l - f.consumo_diesel_estimado_l).dropna()
    t1 = stats.ttest_1samp(erro, 0)
    ic = t1.confidence_interval()
    por_dia = erro.mean() * f.groupby("data_operacao").size().mean()
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.caption("Diferença entre o diesel gasto e o estimado, em litros, em cada operação. Zero = estimativa exata.")
        mostrar(histograma(erro, "L", 1))
    with c2:
        vies = "subestima" if erro.mean() > 0 else "superestima"
        paragrafo(
            f"**A estimativa {vies} o consumo em {num(abs(erro.mean()), 2)} L por operação**, "
            f"cerca de {num(abs((erro / f.loc[erro.index, 'consumo_diesel_estimado_l']).mean() * 100), 1)}%. "
            f"Parece pouco, mas soma uns {num(abs(por_dia))} L por dia e {num(abs(por_dia) * 365)} L por ano. "
            f"Um ajuste de {num(abs((erro / f.loc[erro.index, 'consumo_diesel_estimado_l']).mean() * 100), 0)}% "
            "na estimativa corrige o orçamento de combustível.",
            "veredito" if t1.pvalue < 0.05 else "veredito incerto",
        )
    with st.expander("Detalhes técnicos"):
        st.markdown(
            f"Teste t de uma amostra contra zero: erro médio {num(erro.mean(), 2)} L, "
            f"IC 95% [{num(ic.low, 2)}; {num(ic.high, 2)}], p {p_txt(t1.pvalue)}. "
            f"Erro absoluto médio (MAE) {num(erro.abs().mean(), 2)} L, para um consumo médio de "
            f"{num(f.consumo_diesel_l.mean(), 1)} L."
        )
