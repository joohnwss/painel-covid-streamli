import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

st.set_page_config(
    page_title="PNAD COVID-19 | Painel Hospitalar",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
DATA_DIR     = BASE_DIR / "dados_dashboard"
GEOJSON_PATH = BASE_DIR / "data" / "brazil_uf.geojson"

# ── Constantes ────────────────────────────────────────────────────────────────
UF_INFO = {
    11:("RO","Rondônia","Norte"),       12:("AC","Acre","Norte"),
    13:("AM","Amazonas","Norte"),       14:("RR","Roraima","Norte"),
    15:("PA","Pará","Norte"),           16:("AP","Amapá","Norte"),
    17:("TO","Tocantins","Norte"),      21:("MA","Maranhão","Nordeste"),
    22:("PI","Piauí","Nordeste"),       23:("CE","Ceará","Nordeste"),
    24:("RN","Rio Grande do Norte","Nordeste"), 25:("PB","Paraíba","Nordeste"),
    26:("PE","Pernambuco","Nordeste"),  27:("AL","Alagoas","Nordeste"),
    28:("SE","Sergipe","Nordeste"),     29:("BA","Bahia","Nordeste"),
    31:("MG","Minas Gerais","Sudeste"), 32:("ES","Espírito Santo","Sudeste"),
    33:("RJ","Rio de Janeiro","Sudeste"), 35:("SP","São Paulo","Sudeste"),
    41:("PR","Paraná","Sul"),           42:("SC","Santa Catarina","Sul"),
    43:("RS","Rio Grande do Sul","Sul"),
    50:("MS","Mato Grosso do Sul","Centro-Oeste"),
    51:("MT","Mato Grosso","Centro-Oeste"),
    52:("GO","Goiás","Centro-Oeste"),   53:("DF","Distrito Federal","Centro-Oeste"),
}

FAIXA_ORDEM = {"0-17":0,"18-29":1,"30-39":2,"40-49":3,"50-59":4,"60+":5}

RENDA_ORDEM = {"Até 1 SM":0,"1 a 2 SM":1,"2 a 4 SM":2,"Acima 4 SM":3,"Sem informação":4}

TRADUCAO = {
    "Hipertensao":             "Hipertensão",
    "Depressao":               "Depressão",
    "Cancer":                  "Câncer",
    "Doenca do coracao":       "Doença do coração",
    "Dor de cabeca":           "Dor de cabeça",
    "Nausea":                  "Náusea",
    "Dificuldade para respirar": "Dificuldade para respirar",
    "Pos-graduacao":           "Pós-graduação",
    "Medio completo":          "Médio completo",
    "Medio incompleto":        "Médio incompleto",
    "Sem instrucao":           "Sem instrução",
    "Ate 1 SM":                "Até 1 SM",
    "Sem informacao":          "Sem informação",
    "Relacao muito fraca":     "Relação muito fraca",
    "Nao":                     "Não",
    "Sim":                     "Sim",
}

MESES_ORDEM = {
    "Janeiro":1,"Fevereiro":2,"Marco":3,"Março":3,"Abril":4,"Maio":5,
    "Junho":6,"Julho":7,"Agosto":8,"Setembro":9,"Outubro":10,"Novembro":11,"Dezembro":12,
}

PALETA = ["#1F4E79","#2E75B6","#D85A30","#475569","#1A7A4A","#6B7280","#7C3AED"]

ARQUIVOS = {
    "kpis":                "descritiva_kpis.csv",
    "perfil_populacao":    "descritiva_perfil_populacao.csv",
    "sintomas":            "descritiva_sintomas.csv",
    "faixa_etaria":        "descritiva_faixa_etaria.csv",
    "comorbidades":        "descritiva_comorbidades.csv",
    "itens_protecao":      "descritiva_itens_protecao.csv",
    "barreira":            "analise_01_barreira_economica.csv",
    "informalidade":       "analise_02_informalidade_risco.csv",
    "perfil_grave":        "analise_03_perfil_grave.csv",
    "protecao_social":     "analise_04_protecao_social.csv",
    "mapa_desigualdade":   "analise_05_mapa_desigualdade.csv",
    "evolucao":            "analise_06_evolucao_mensal.csv",
    "escolaridade_genero": "analise_07_escolaridade_genero.csv",
    "moradia":             "analise_08_moradia_endividamento.csv",
    "sus_privado":         "analise_09_sus_privado.csv",
    "correlacoes":         "correlacoes_economico_clinico.csv",
}

LABELS = {
    "pct_buscou_atendimento":               "% buscou atendimento",
    "pct_internado_entre_atendidos":        "% internação entre atendidos",
    "pct_entubado_entre_internados":        "% entubação entre internados",
    "pct_fez_teste":                        "% fez teste",
    "pct_positivo_entre_resultados_validos":"% positividade",
    "pct_dificuldade_respirar":             "% dificuldade respiratória",
    "pct_perda_cheiro_sabor":               "% perda cheiro/sabor",
    "pct_alguma_comorbidade":               "% alguma comorbidade",
    "pct_sem_plano":                        "% sem plano de saúde",
    "pct_ate_1_sm_entre_renda_informada":   "% até 1 salário mínimo",
    "pct_informal_entre_ocupados_com_info": "% informalidade",
    "pct_recebeu_auxilio":                  "% recebeu auxílio emergencial",
    "pct_recebeu_bolsa_familia":            "% recebeu Bolsa Família",
    "pct_recebeu_seguro_desemprego":        "% recebeu seguro-desemprego",
    "pct_pegou_emprestimo":                 "% pegou empréstimo",
    "pct_home_office":                      "% home office",
    "pct_com_sintoma":                      "% com sintoma",
    "pct_com_comorbidade":                  "% com comorbidade",
    "pct_tem_item":                         "% tem item de proteção",
    "media_itens_protecao":                 "média de itens de proteção",
}

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS_BASE = (
    ".block-container{"
    "padding-top:.5rem;padding-bottom:2rem;"
    "padding-left:clamp(1rem,2.4vw,2.75rem);"
    "padding-right:clamp(1rem,2.4vw,2.75rem);"
    "max-width:1280px;}"
    ".hero-title{font-size:clamp(1.55rem,2.4vw,2.1rem);font-weight:750;"
    "line-height:1.15;margin-bottom:.25rem;}"
    ".hero-sub{font-size:.98rem;margin-bottom:.4rem;}"
    ".sec-sub{font-size:.93rem;margin-bottom:1rem;}"
    ".small-note{font-size:.83rem;}"
    ".tese-box{border-radius:10px;padding:1rem 1.25rem;margin:1rem 0 1.5rem 0;}"
    ".tese-box p{font-size:1.02rem;margin:0;line-height:1.6;}"
    ".callout{border-left-width:5px;border-left-style:solid;"
    "padding:.8rem 1rem;border-radius:8px;margin:.6rem 0;"
    "box-shadow:0 1px 3px rgba(0,0,0,.06);}"
    "[data-testid='stMetric']{border-top-width:3px;border-top-style:solid;"
    "padding:.85rem .9rem;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.07);}"
    "[data-testid='stMetricValue']{font-weight:750;}"
    "div[data-testid='stDataFrame']{border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.04);}"
    ".stPlotlyChart,[data-testid='stPlotlyChart']{"
    "border-radius:10px;overflow:hidden;padding:.25rem;"
    "box-shadow:0 1px 4px rgba(0,0,0,.05);}"
    "@media(max-width:1100px){"
    ".block-container{padding-top:4.75rem;padding-left:1rem;padding-right:1rem;}}"
)

_CSS_LIGHT = (
    "<style>"
    ":root{--ink:#172033;--muted:#5F6B7A;--line:#D9E2EC;--navy:#1F4E79;"
    "--blue:#2E75B6;--orange:#D85A30;--green:#1A7A4A;--red:#991B1B;}"
    "html,body,.stApp,[data-testid='stAppViewContainer'],"
    "[data-testid='stMain'],[data-testid='stMainBlockContainer']"
    "{background:#F6F8FB!important;color:#172033!important;}"
    ".block-container{background:#F6F8FB!important;}"
    "[data-testid='stHeader']{display:none!important;}"
    "[data-testid='stSidebar']{background:#EEF2F7!important;border-right:1px solid #D9E2EC;}"
    "div[data-testid='stVerticalBlockBorderWrapper']:first-of-type>"
    "div[data-testid='stVerticalBlock']{"
    "background:#FFFFFF;border-radius:10px;padding:.25rem .5rem;}"
    "[data-testid='stSidebar'] *{color:#172033!important;}"
    "h1,h2,h3{color:#1F4E79;}"
    ".hero-title{color:#1F4E79;}"
    ".hero-sub,.sec-sub,.small-note{color:#5F6B7A;}"
    ".tese-box{border:2px solid #1F4E79;background:#EEF4FB;}"
    ".tese-box p{color:#1F4E79;}"
    ".callout{background:#FFFFFF;border-color:#D9E2EC;border-left-color:#2E75B6;}"
    ".callout strong{color:#172033;}"
    ".callout-insight{border-left-color:#2E75B6!important;background:#F0F6FF!important;}"
    ".callout-action{border-left-color:#1A7A4A!important;background:#F0FBF5!important;}"
    ".callout-context{border-left-color:#5F6B7A!important;background:#F8FAFC!important;}"
    ".callout-warning{border-left-color:#D85A30!important;background:#FFF5EE!important;}"
    ".callout-risk{border-left-color:#991B1B!important;background:#FFF7F7!important;}"
    "[data-testid='stMetric']{background:#FFFFFF;border:1px solid #DDE6F0;border-top-color:#2E75B6;}"
    "[data-testid='stMetricLabel']{color:#42526A;}"
    "[data-testid='stMetricValue']{color:#1F4E79;}"
    "div[data-testid='stDataFrame']{background:#FFFFFF;border:1px solid #D9E2EC;}"
    ".stPlotlyChart,[data-testid='stPlotlyChart']{background:#FFFFFF;border:1px solid #E8EDF4;}"
    + _CSS_BASE + "</style>"
)

_CSS_DARK = (
    "<style>"
    ":root{--ink:#DDE6F0;--muted:#8A99AB;--line:#2D3A4A;--navy:#7AB8E8;"
    "--blue:#63B3ED;--orange:#F6AD55;--green:#68D391;--red:#FC8181;}"
    "html,body,.stApp,[data-testid='stAppViewContainer'],"
    "[data-testid='stMain'],[data-testid='stMainBlockContainer']"
    "{background:#0F1117!important;color:#DDE6F0!important;}"
    ".block-container{background:#0F1117!important;}"
    "[data-testid='stHeader']{display:none!important;}"
    "[data-testid='stSidebar']{background:#161B27!important;border-right:1px solid #2D3A4A;}"
    "div[data-testid='stVerticalBlockBorderWrapper']:first-of-type>"
    "div[data-testid='stVerticalBlock']{"
    "background:#1C2333;border-radius:10px;padding:.25rem .5rem;}"
    "[data-testid='stSidebar'] *{color:#DDE6F0!important;}"
    "h1,h2,h3{color:#7AB8E8;}"
    ".hero-title{color:#7AB8E8;}"
    ".hero-sub,.sec-sub,.small-note{color:#8A99AB;}"
    ".tese-box{border:2px solid #7AB8E8;background:#1A2744;}"
    ".tese-box p{color:#7AB8E8;}"
    ".callout{background:#1C2333;border-color:#2D3A4A;border-left-color:#63B3ED;}"
    ".callout strong{color:#DDE6F0;}"
    ".callout-insight{border-left-color:#63B3ED!important;background:#1A2744!important;}"
    ".callout-action{border-left-color:#68D391!important;background:#162B1F!important;}"
    ".callout-context{border-left-color:#8A99AB!important;background:#1C2333!important;}"
    ".callout-warning{border-left-color:#F6AD55!important;background:#2B1E10!important;}"
    ".callout-risk{border-left-color:#FC8181!important;background:#2B1414!important;}"
    "[data-testid='stMetric']{background:#1C2333!important;border:1px solid #2D3A4A!important;border-top-color:#63B3ED!important;}"
    "[data-testid='stMetricLabel']{color:#8A99AB!important;}"
    "[data-testid='stMetricValue']{color:#7AB8E8!important;}"
    "div[data-testid='stDataFrame']{background:#1C2333!important;border:1px solid #2D3A4A!important;}"
    ".stPlotlyChart,[data-testid='stPlotlyChart']{background:#1C2333!important;border:1px solid #2D3A4A!important;}"
    "input,textarea,select{background:#1C2333!important;color:#DDE6F0!important;border-color:#2D3A4A!important;}"
    "[data-testid='stHeader']{background:#0F1117!important;border-bottom:1px solid #2D3A4A!important;}"
    "[data-testid='stToolbar']{background:#0F1117!important;}"
    "header{background:#0F1117!important;}"
    "[data-baseweb='select'] div,[data-baseweb='input'] div{"
    "background:#1C2333!important;color:#DDE6F0!important;border-color:#2D3A4A!important;}"
    "[data-baseweb='select'] span,[data-baseweb='input'] span{color:#DDE6F0!important;}"
    "[data-baseweb='popover'] ul{background:#1C2333!important;border-color:#2D3A4A!important;}"
    "[data-baseweb='popover'] li{background:#1C2333!important;color:#DDE6F0!important;}"
    "[data-baseweb='popover'] li:hover{background:#2D3A4A!important;}"
    "[data-testid='stSelectbox'] label,[data-testid='stToggle'] label{color:#DDE6F0!important;}"
    + _CSS_BASE + "</style>"
)

def _aplicar_css():
    dark = st.session_state.get("dark_mode", False)
    st.markdown(_CSS_DARK if dark else _CSS_LIGHT, unsafe_allow_html=True)

_aplicar_css()

# ── Carregamento de dados ──────────────────────────────────────────────────────
def _detectar_sep(caminho: Path) -> str:
    try:
        amostra = caminho.read_text(encoding="utf-8-sig", errors="ignore")[:4096]
        return csv.Sniffer().sniff(amostra, delimiters=",;|\t").delimiter
    except Exception:
        return ","


@st.cache_data(show_spinner=False)
def carregar_csv(nome_arquivo: str) -> pd.DataFrame:
    caminho = DATA_DIR / nome_arquivo
    if not caminho.exists():
        return pd.DataFrame()
    sep = _detectar_sep(caminho)
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            df = pd.read_csv(caminho, sep=sep, encoding=enc)
            return _preparar(df)
        except Exception:
            continue
    return pd.DataFrame()


def _preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().replace(
            {"": np.nan, "nan": np.nan, "None": np.nan}
        ).replace(TRADUCAO)
    _num = {
        "n_amostra","qtd_respostas_sim","qtd_tem_item",
        "pop_estimada_com_sintoma","pop_estimada_com_comorbidade",
        "pop_estimada_tem_item","populacao_estimada",
        "media_itens_protecao","correlacao","idade_media",
        "n_respostas_validas_internacao_b005","pop_respostas_validas_internacao_b005",
        "n_respostas_validas_entubacao_b006","pop_respostas_validas_entubacao_b006",
    }
    for col in df.columns:
        if col.startswith("pct_") or col in _num:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "uf" in df.columns:
        df["uf"] = pd.to_numeric(df["uf"], errors="coerce")
        df["sigla"]  = df["uf"].map(
            lambda c: UF_INFO.get(int(c), (str(c),))[0] if pd.notna(c) else None)
        df["estado"] = df["uf"].map(
            lambda c: UF_INFO.get(int(c), (None, str(c)))[1] if pd.notna(c) else None)
        df["regiao"] = df["uf"].map(
            lambda c: UF_INFO.get(int(c), (None, None, None))[2] if pd.notna(c) else None)
    if "v1013" in df.columns:
        df["ordem_mes"] = pd.to_numeric(df["v1013"], errors="coerce")
    elif "mes_nome" in df.columns:
        df["ordem_mes"] = df["mes_nome"].map(MESES_ORDEM)
    if "faixa_etaria" in df.columns:
        df["ordem_faixa"] = df["faixa_etaria"].map(FAIXA_ORDEM)
    if "faixa_renda" in df.columns:
        df["ordem_renda"] = df["faixa_renda"].map(RENDA_ORDEM)
    return df


@st.cache_data(show_spinner=False)
def _carregar_geojson():
    if GEOJSON_PATH.exists():
        return json.loads(GEOJSON_PATH.read_text())
    return None


@st.cache_data(show_spinner=False)
def carregar_todos() -> dict:
    return {k: carregar_csv(v) for k, v in ARQUIVOS.items()}


# ── Helpers ───────────────────────────────────────────────────────────────────
VALOR_NAO_APURADO = "Não apurado"


def fmt_pct(v, casas=1) -> str:
    if pd.isna(v): return VALOR_NAO_APURADO
    return f"{float(v):.{casas}f}%".replace(".", ",")

def fmt_num(v, casas=0) -> str:
    if pd.isna(v): return VALOR_NAO_APURADO
    n = float(v)
    if casas == 0: return f"{n:,.0f}".replace(",", ".")
    return f"{n:,.{casas}f}".replace(",","X").replace(".",",").replace("X",".")

def dado_indisponivel(titulo: str, motivo: str, colunas=None):
    detalhe = f" Colunas esperadas: {', '.join(colunas)}." if colunas else ""
    st.warning(
        f"{titulo}: indicador ocultado porque {motivo}.{detalhe} "
        "O painel só exibe dados agregados já validados da camada Ouro.",
        icon="⚠️",
    )

def tabela_indisponivel(nome_tabela: str):
    st.warning(
        f"Tabela agregada `{nome_tabela}` não disponível ou sem linhas válidas em `dados_dashboard/`. "
        "Esta página fica oculta porque o dashboard não recalcula a base bruta nem preenche lacunas por estimativa.",
        icon="⚠️",
    )

def nome_lab(col: str) -> str:
    return LABELS.get(col, col.replace("_", " "))

def ordenar_mes(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "ordem_mes" not in df.columns: return df
    return df.sort_values("ordem_mes")

def ordenar_faixa(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "ordem_faixa" not in df.columns: return df
    return df.sort_values("ordem_faixa")

def ultimo_mes(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "ordem_mes" not in df.columns: return df
    return df[df["ordem_mes"] == df["ordem_mes"].max()].copy()

def filtrar_mes(df: pd.DataFrame, mes: str) -> pd.DataFrame:
    if df.empty or mes == "Todos" or "mes_nome" not in df.columns: return df.copy()
    return df[df["mes_nome"] == mes].copy()

def recorte(df: pd.DataFrame, mes: str) -> pd.DataFrame:
    if df.empty or "mes_nome" not in df.columns: return df.copy()
    if mes != "Todos": return filtrar_mes(df, mes)
    return df.copy()  # "Todos" → todos os meses; agregar() fará a média ponderada

def coletar_meses(dados: dict) -> list:
    meses = []
    for df in dados.values():
        if not df.empty and "mes_nome" in df.columns:
            meses.extend(df["mes_nome"].dropna().unique().tolist())
    return sorted(
        {m for m in meses if m in MESES_ORDEM},
        key=lambda m: MESES_ORDEM[m],
    )

def med_pond(df: pd.DataFrame, col: str, peso="n_amostra") -> float:
    if df.empty or col not in df.columns: return np.nan
    dados = df[[col] + ([peso] if peso in df.columns else [])].dropna(subset=[col]).copy()
    if dados.empty: return np.nan
    v = pd.to_numeric(dados[col], errors="coerce")
    if peso in dados.columns:
        p = pd.to_numeric(dados[peso], errors="coerce").fillna(0)
        ok = v.notna() & (p > 0)
        if ok.any(): return np.average(v[ok], weights=p[ok])
    return v.mean()

def agregar(df: pd.DataFrame, grupo, colunas: list, peso="n_amostra") -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    if isinstance(grupo, str): grupo = [grupo]
    linhas = []
    for chaves, g in df.groupby(grupo, dropna=False):
        if not isinstance(chaves, tuple): chaves = (chaves,)
        linha = dict(zip(grupo, chaves))
        linha["n_total"] = g[peso].sum() if peso in g.columns else len(g)
        for col in colunas:
            if col in g.columns:
                linha[col] = med_pond(g, col, peso=peso)
        linhas.append(linha)
    return pd.DataFrame(linhas)

def agregar_count(df: pd.DataFrame, grupo: str,
                  qtd_col="qtd_respostas_sim", n_col="n_amostra") -> pd.DataFrame:
    if df.empty or qtd_col not in df.columns or n_col not in df.columns:
        return pd.DataFrame()
    agg = df.groupby(grupo).agg(qtd=(qtd_col,"sum"), n=(n_col,"sum")).reset_index()
    agg["pct"] = agg["qtd"] / agg["n"] * 100
    return agg

def is_dark() -> bool:
    return st.session_state.get("dark_mode", False)

def _layout_fig(fig, ytitle="Percentual"):
    dark = is_dark()
    bg      = "#1C2333" if dark else "#FFFFFF"
    ink     = "#DDE6F0" if dark else "#172033"
    grid    = "#2D3A4A" if dark else "#E5E7EB"
    tick    = "#8A99AB" if dark else "#334155"
    fig.update_layout(
        template="plotly_white", colorway=PALETA,
        paper_bgcolor=bg, plot_bgcolor=bg,
        font=dict(color=ink, size=12),
        title_x=0.01, title_font_size=16,
        legend_title_text="",
        margin=dict(l=16, r=16, t=56, b=34),
        xaxis_title="", yaxis_title=ytitle,
        hovermode="x unified",
        hoverlabel=dict(bgcolor=bg, font_color=ink, bordercolor=grid),
    )
    fig.update_xaxes(showgrid=False, automargin=True, tickfont=dict(color=tick))
    fig.update_yaxes(gridcolor=grid, zerolinecolor=grid, automargin=True)
    return fig

def _cor_col(col: str):
    if any(k in col for k in ["intern","entub","grave","dificul"]): return "#D85A30"
    if any(k in col for k in ["home_office","tem_item","protec"]): return "#1A7A4A"
    if any(k in col for k in ["auxilio","bolsa","seguro","benefi"]): return "#7C3AED"
    if any(k in col for k in ["sem_plano","ate_1_sm","informal","buscou"]): return "#0F766E"
    if any(k in col for k in ["com_sintoma","com_comorbidade","pct_com_sint","pct_com_comorb"]): return "#2E75B6"
    return None


def barras(df: pd.DataFrame, x: str, y: str, titulo: str,
           color=None, orientation="v", top=None, xtitle=None, ytitle=None):
    if df.empty or x not in df.columns or y not in df.columns:
        motivo = "a tabela do recorte atual não tem linhas suficientes" if df.empty else "faltam campos obrigatórios para montar o gráfico"
        dado_indisponivel(titulo, motivo, [x, y])
        return
    dados = df.dropna(subset=[x, y]).copy()
    dados[y] = pd.to_numeric(dados[y], errors="coerce")
    dados = dados.dropna(subset=[y])
    if top: dados = dados.sort_values(y, ascending=False).head(top)
    if dados.empty:
        dado_indisponivel(titulo, "todos os registros deste recorte ficaram sem valor numérico validado", [x, y])
        return
    fig = px.bar(
        dados,
        x=x if orientation == "v" else y,
        y=y if orientation == "v" else x,
        color=color if color and color in dados.columns else None,
        orientation=orientation, title=titulo, text=y,
    )
    if color and color in dados.columns:
        fig.update_layout(barmode="group")
    elif not color:
        auto_cor = _cor_col(y)
        if auto_cor:
            fig.update_traces(marker_color=auto_cor)
    tmpl = "%{text:.1f}%" if (y.startswith("pct_") or y == "pct") else "%{text:.1f}"
    fig.update_traces(texttemplate=tmpl, textposition="outside", cliponaxis=False)
    _layout_fig(fig, ytitle=ytitle or ("" if orientation == "h" else nome_lab(y)))
    if orientation == "h":
        fig.update_layout(xaxis_title=xtitle or nome_lab(y))
        fig.update_yaxes(categoryorder="total ascending")
    else:
        fig.update_layout(xaxis_title=xtitle or "")
    st.plotly_chart(fig, use_container_width=True)

def linhas(df: pd.DataFrame, x: str, y_cols: list, titulo: str):
    cols = [c for c in y_cols if c in df.columns]
    if df.empty or x not in df.columns or not cols:
        motivo = "a série temporal não tem linhas no recorte atual" if df.empty else "faltam campos obrigatórios para montar a série temporal"
        dado_indisponivel(titulo, motivo, [x] + y_cols)
        return
    dados = ordenar_mes(df)[[x] + cols].dropna(how="all", subset=cols)
    if dados.empty:
        dado_indisponivel(titulo, "nenhum mês tem valor validado para os indicadores selecionados", [x] + cols)
        return
    long = dados.melt(id_vars=x, value_vars=cols, var_name="indicador", value_name="valor")
    long["indicador"] = long["indicador"].map(nome_lab)
    fig = px.line(long, x=x, y="valor", color="indicador", markers=True, title=titulo)
    fig.update_traces(line_width=2.5, marker_size=7)
    _layout_fig(fig)
    st.plotly_chart(fig, use_container_width=True)

def chamada(tipo: str, texto: str):
    cls = {
        "insight": "callout-insight",
        "acao":    "callout-action",
        "context": "callout-context",
        "cuidado": "callout-warning",
        "risco":   "callout-risk",
    }
    tit = {
        "insight": "Insight",
        "acao":    "Ação para o hospital",
        "context": "Leitura de contexto",
        "cuidado": "Ponto de atenção",
        "risco":   "Implicação hospitalar",
    }
    css_cls = cls.get(tipo, "")
    titulo_caixa = tit.get(tipo, tipo)
    st.markdown(
        f"<div class='callout {css_cls}'><strong>{titulo_caixa}:</strong> {texto}</div>",
        unsafe_allow_html=True,
    )

def cabecalho(titulo: str, contexto: str):
    st.header(titulo)
    st.markdown(f"<div class='sec-sub'>{contexto}</div>", unsafe_allow_html=True)

def expander_tabela(titulo: str, df: pd.DataFrame):
    with st.expander(titulo, expanded=False):
        if df.empty:
            st.warning(
                "Tabela sem linhas para o recorte selecionado. Isso normalmente ocorre quando o filtro de mês "
                "não existe nessa tabela agregada ou quando a camada Ouro não validou registros para a combinação escolhida."
            )
        else: st.dataframe(
            df.drop(columns=["ordem_mes","ordem_faixa"], errors="ignore"),
            use_container_width=True, hide_index=True)

def _cor_metrica(label: str) -> str:
    l = label.lower()
    if any(k in l for k in ["intern","entub","posit","grave","risco","60+","60 anos"]):
        return "#D85A30"
    if any(k in l for k in ["plano","sus","atend","busca","acesso","teste","fez teste"]):
        return "#0F766E"
    if any(k in l for k in ["auxílio","bolsa","renda","informal","benefíci","social","vulnerab","crítico"]):
        return "#7C3AED"
    if any(k in l for k in ["estado","territó","região","norte","nordest","foco priorit"]):
        return "#1A7A4A"
    return "#2E75B6"


def metricas(cols: list):
    colunas = st.columns(len(cols))
    for col_st, item in zip(colunas, cols):
        label = item[0]
        valor = item[1]
        ajuda = item[2] if len(item) > 2 else None
        cor   = item[3] if len(item) > 3 else _cor_metrica(label)
        if valor == VALOR_NAO_APURADO:
            with col_st:
                detalhe = f" {ajuda}." if ajuda else ""
                st.warning(
                    f"{label}: métrica ocultada porque não houve valor validado no recorte atual.{detalhe}"
                )
            continue
        dark = is_dark()
        card_bg  = "#1C2333" if dark else "#FFFFFF"
        card_bdr = "#2D3A4A" if dark else "#DDE6F0"
        lbl_col  = "#8A99AB" if dark else "#42526A"
        val_col  = "#7AB8E8" if dark else "#1F4E79"
        hlp_col  = "#8A99AB" if dark else "#6B7280"
        ajuda_html = (
            f"<div style='font-size:.75rem;color:{hlp_col};margin-top:.15rem;"
            f"line-height:1.3;'>{ajuda}</div>" if ajuda else ""
        )
        with col_st:
            st.markdown(f"""
            <div style='background:{card_bg};border:1px solid {card_bdr};border-top:3.5px solid {cor};
                        border-radius:8px;padding:.85rem .9rem;
                        box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:.15rem;'>
              <div style='font-size:.74rem;color:{lbl_col};font-weight:600;
                          text-transform:uppercase;letter-spacing:.05em;'>{label}</div>
              <div style='font-size:1.55rem;font-weight:750;color:{val_col};
                          line-height:1.1;margin:.2rem 0 .05rem;'>{valor}</div>
              {ajuda_html}
            </div>
            """, unsafe_allow_html=True)

def aviso_recorte():
    if mes_global == "Todos":
        st.info(
            "Quando o filtro está em **Todos**, os indicadores mostram a média dos meses analisados.",
            icon="ℹ️"
        )

# ── Choropleth ────────────────────────────────────────────────────────────────
def brazil_choropleth(df_uf: pd.DataFrame, value_col: str, label: str, titulo: str):
    geojson = _carregar_geojson()
    if geojson is None or df_uf.empty or "sigla" not in df_uf.columns:
        return None
    try:
        df_plot = df_uf[df_uf["sigla"].notna()].copy()
        fig = px.choropleth(
            df_plot, geojson=geojson,
            locations="sigla", featureidkey="properties.sigla",
            color=value_col,
            hover_name="estado" if "estado" in df_plot.columns else "sigla",
            color_continuous_scale=[[0,"#C8DEFF"],[0.5,"#2E75B6"],[1,"#1F4E79"]],
            scope="south america", title=titulo,
            labels={value_col: label},
        )
        fig.update_geos(fitbounds="locations", visible=False)
        dark = is_dark()
        fig.update_layout(
            margin=dict(l=0,r=0,t=50,b=0),
            paper_bgcolor="#1C2333" if dark else "#FFFFFF",
            font=dict(color="#DDE6F0" if dark else "#172033", size=12),
            coloraxis_colorbar=dict(title=label, len=0.6, thickness=14),
            title_x=0.01, title_font_size=16,
        )
        return fig
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINAS
# ═══════════════════════════════════════════════════════════════════════════════

def _row_kpis(df_k: pd.DataFrame) -> pd.Series:
    if df_k.empty:
        return pd.Series(dtype=float)
    if mes_global == "Todos":
        sub = df_k[df_k["v1013"] == 0] if "v1013" in df_k.columns else pd.DataFrame()
        return sub.iloc[0] if not sub.empty else df_k.iloc[0]
    sub = df_k[df_k["mes_nome"] == mes_global] if "mes_nome" in df_k.columns else pd.DataFrame()
    return sub.iloc[0] if not sub.empty else df_k.iloc[0]


def pagina_apresentacao():
    dark    = is_dark()
    bg_card = "#1C2333" if dark else "#FFFFFF"
    bdr     = "#2D3A4A" if dark else "#DDE6F0"
    ink     = "#DDE6F0" if dark else "#172033"
    muted   = "#8A99AB" if dark else "#5F6B7A"
    navy    = "#7AB8E8" if dark else "#1F4E79"

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        f"<div class='hero-title' style='color:{navy};'>Tech Challenge — Fase 3</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:1.1rem;font-weight:500;color:{ink};margin:.2rem 0 .3rem;'>"
        f"Painel de apoio à decisão hospitalar com dados da PNAD-COVID 19</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='hero-sub' style='color:{muted};'>"
        f"FIAP · Pós-graduação em Data Analytics &nbsp;·&nbsp; 2024</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    col_eq, col_obj = st.columns([1, 2], gap="large")

    # ── Equipe ─────────────────────────────────────────────────────────────────
    with col_eq:
        st.markdown(
            f"<div style='font-size:.72rem;font-weight:700;color:{muted};"
            f"text-transform:uppercase;letter-spacing:.06em;margin-bottom:.6rem;'>"
            f"Equipe</div>",
            unsafe_allow_html=True,
        )
        membros = [
            "Izadora Rayana Bento Araujo",
            "Jônatas Williams Santos Silva",
            "Laura Rossati de Oliveira",
            "Lucas de Oliveira Schroeder",
            "Victor Thiago Farias Santos",
        ]
        for nome in membros:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:.5rem;"
                f"padding:.35rem 0;border-bottom:1px solid {bdr};'>"
                f"<div style='width:6px;height:6px;border-radius:50%;background:{navy};flex-shrink:0;'></div>"
                f"<span style='font-size:.88rem;color:{ink};'>{nome}</span></div>",
                unsafe_allow_html=True,
            )

    # ── Objetivo ───────────────────────────────────────────────────────────────
    with col_obj:
        st.markdown(
            f"<div style='font-size:.72rem;font-weight:700;color:{muted};"
            f"text-transform:uppercase;letter-spacing:.06em;margin-bottom:.6rem;'>"
            f"Contexto e objetivo</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-size:.92rem;color:{ink};line-height:1.65;'>"
            f"Um hospital contratou uma equipe de Data Analytics para entender o comportamento da população "
            f"durante a pandemia de COVID-19 e identificar sinais que ajudem no planejamento de um novo "
            f"surto respiratório.<br><br>"
            f"O painel transforma os dados da PNAD-COVID em indicadores de risco, acesso ao cuidado, "
            f"vulnerabilidade social e ações recomendadas para a gestão hospitalar."
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        # Três pilares
        pilares = [
            ("#D85A30", "Perfil clínico",       "Sintomas, comorbidades e faixas etárias com maior risco de internação."),
            ("#2E75B6", "Acesso ao cuidado",     "Busca por atendimento, testagem, plano de saúde e portas de entrada do sistema."),
            ("#1A7A4A", "Vulnerabilidade social", "Renda, trabalho, território e benefícios sociais como sinais de barreira de acesso."),
        ]
        for cor, titulo, desc in pilares:
            st.markdown(
                f"<div style='display:flex;gap:.75rem;align-items:flex-start;"
                f"padding:.55rem 0;border-bottom:1px solid {bdr};'>"
                f"<div style='width:3px;border-radius:2px;background:{cor};"
                f"min-height:2.4rem;flex-shrink:0;margin-top:.15rem;'></div>"
                f"<div><div style='font-size:.82rem;font-weight:700;color:{cor};'>{titulo}</div>"
                f"<div style='font-size:.82rem;color:{muted};line-height:1.5;'>{desc}</div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Metodologia resumida ───────────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:.72rem;font-weight:700;color:{muted};"
        f"text-transform:uppercase;letter-spacing:.06em;margin-bottom:.8rem;'>"
        f"Metodologia</div>",
        unsafe_allow_html=True,
    )
    m1, m2, m3, m4 = st.columns(4)
    for col_m, val, lbl in [
        (m1, "PNAD-COVID 19", "Fonte — IBGE"),
        (m2, "20 variáveis", "Selecionadas do questionário"),
        (m3, "3 meses", "Setembro, outubro e novembro de 2020"),
        (m4, "AWS + Glue + Athena", "Pipeline de dados em camada Ouro"),
    ]:
        with col_m:
            st.markdown(
                f"<div style='background:{bg_card};border:1px solid {bdr};"
                f"border-radius:8px;padding:.8rem .9rem;text-align:center;'>"
                f"<div style='font-size:1.05rem;font-weight:800;color:{navy};'>{val}</div>"
                f"<div style='font-size:.75rem;color:{muted};margin-top:.2rem;'>{lbl}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


def pagina_capa():
    st.markdown("<div class='hero-title'>Painel Hospitalar · PNAD COVID-19</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-sub'>Tech Challenge Fase 3 &nbsp;·&nbsp; Dados: setembro–novembro de 2020</div>",
        unsafe_allow_html=True,
    )

    st.markdown("""
    <div class='tese-box'>
    <p><strong>Tese central:</strong> A vulnerabilidade à COVID-19 aparece em duas frentes:
    <strong>risco clínico</strong>, ligado à idade e comorbidades, e <strong>risco de acesso</strong>,
    ligado a plano de saúde, renda e território. O hospital precisa atuar nas duas frentes:
    triagem clínica precoce e rotas rápidas para quem depende da rede pública.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "**Pergunta central:** Após analisar os dados da PNAD-COVID (set–nov/2020), "
        "quais decisões um hospital deve tomar para se preparar para um novo surto respiratório?"
    )
    st.divider()

    df_k = dados["kpis"]
    row = _row_kpis(df_k)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Registros analisados", fmt_num(row.get("n_amostra", np.nan)),
                        help="Total de respondentes válidos na PNAD-COVID")
    with c2: st.metric("Sem plano de saúde",   fmt_pct(row.get("pct_sem_plano")),
                        help="Dependência potencial do SUS")
    with c3: st.metric("Com alguma comorbidade", fmt_pct(row.get("pct_alguma_comorbidade")),
                        help="Diabetes, hipertensão, asma, coração, depressão ou câncer")
    with c4: st.metric("Idade média",           f"{fmt_num(row.get('idade_media', np.nan), 1)} anos")

    st.divider()

    st.markdown("#### Navegue pelas seções no menu lateral →")
    st.markdown("""
| Seção | Pergunta respondida |
|---|---|
| 1. Visão geral | Quem é a população? |
| 2–4. Perfil clínico | Sintomas, idade, comorbidades |
| 5–6. Acesso | Renda, plano, SUS vs privado |
| 7. Territórios | Onde estão os mais vulneráveis? |
| 8–11. Contexto social | Trabalho, proteção, escolaridade |
| 12. Correlações | Risco clínico ou também social? |
| 13–14. Gerencial | Alerta mensal + matriz de prioridade |
| 15. Plano de ação | O que o hospital deve fazer? |
""")

    st.divider()
    with st.expander("Equipe do projeto"):
        membros = [
            "Izadora Rayana Bento Araujo",
            "Jônatas Williams Santos Silva",
            "Laura Rossati de Oliveira",
            "Lucas de Oliveira Schroeder",
            "Victor Thiago Farias Santos",
        ]
        for nome in membros:
            st.markdown(f"- {nome}")


def pagina_visao_geral():
    cabecalho("Quem é a população analisada?",
              "Perfil geral dos 1,15 milhão de respondentes — base para todas as projeções do painel.")

    df_k = dados["kpis"]
    row = _row_kpis(df_k)

    metricas([
        ("Total de registros",  fmt_num(row.get("n_amostra")), "Respondentes válidos"),
        ("Idade média",         f"{fmt_num(row.get('idade_media'), 1)} anos", None),
        ("Feminino / Masculino",
         f"{fmt_pct(row.get('pct_feminino'))} / {fmt_pct(row.get('pct_masculino'))}", None),
        ("Sem plano de saúde",  fmt_pct(row.get("pct_sem_plano")), "Dependentes do SUS"),
    ])
    metricas([
        ("Renda até 1 SM",         fmt_pct(row.get("pct_ate_1_sm_entre_renda_informada")),
         "Entre renda informada"),
        ("Alguma comorbidade",     fmt_pct(row.get("pct_alguma_comorbidade")),
         "6 condições monitoradas"),
        ("Buscou atendimento",     fmt_pct(row.get("pct_buscou_atendimento")), None),
        ("Fez teste",              fmt_pct(row.get("pct_fez_teste")), None),
    ])
    metricas([
        ("Positividade entre resultados válidos",
         fmt_pct(row.get("pct_positivo_entre_resultados_validos")),
         "Entre quem teve resultado válido no teste"),
        ("Internação entre atendidos",
         fmt_pct(row.get("pct_internado_entre_atendidos")), None),
        ("Entubação entre internados",
         fmt_pct(row.get("pct_entubado_entre_internados")), None),
    ])

    chamada("insight",
            "A maioria das pessoas analisadas não tinha plano de saúde. "
            "Isso significa que, em um novo surto, muitos pacientes devem procurar primeiro a rede pública.")
    chamada("acao",
            "Preparar a porta de entrada com triagem rápida, orientação clara e encaminhamento eficiente para evitar filas, "
            "demora no atendimento e sobrecarga dos leitos.")


def pagina_sintomas():
    cabecalho("Quais sinais devem acender alerta cedo?",
              "Frequência dos sintomas reportados na PNAD-COVID — média dos meses disponíveis.")

    df = dados["sintomas"]
    if df.empty:
        tabela_indisponivel("descritiva_sintomas.csv"); return

    aviso_recorte()
    df_f = recorte(df, mes_global) if mes_global != "Todos" else df

    agg = agregar_count(df_f, "sintoma")
    if agg.empty:
        agg = agregar(df_f, "sintoma", ["pct_com_sintoma"])
        agg = agg.rename(columns={"pct_com_sintoma": "pct"}) if "pct_com_sintoma" in agg.columns else agg
    agg = agg.sort_values("pct", ascending=False)

    if not agg.empty:
        metricas([
            ("Sintoma mais comum", str(agg.iloc[0]["sintoma"]),
             f"{fmt_pct(agg.iloc[0]['pct'])} da população"),
            ("Dificuldade para respirar",
             fmt_pct(agg[agg["sintoma"].str.lower().str.contains("respirar", na=False)]["pct"].mean()),
             "Sinal grave — já é tardio"),
            ("Dor no peito",
             fmt_pct(agg[agg["sintoma"].str.lower().str.contains("peito|torácic", na=False)]["pct"].mean()),
             "Sinal grave — já é tardio"),
        ])

    barras(agg, "sintoma", "pct",
           "Frequência dos sintomas reportados (%)",
           orientation="h", xtitle="% da população com o sintoma")

    chamada("cuidado",
            "Falta de ar e dor no peito aparecem com menor frequência, mas são sinais de maior gravidade. "
            "Por isso, o hospital não deve esperar esses sintomas para começar a agir.")
    chamada("insight",
            "Os sintomas mais comuns são leves, como dor de cabeça, coriza, tosse e dor de garganta. "
            "O aumento desses sintomas pode ser o primeiro sinal de que a procura por atendimento vai crescer.")
    chamada("acao",
            "Criar uma triagem precoce que combine sintomas leves, idade e comorbidades. "
            "Assim, pacientes com maior risco podem ser orientados, testados ou encaminhados antes de evoluírem para internação.")


def pagina_idade_agravamento():
    cabecalho("Quem teve maior risco de internação?",
              "Internação entre atendidos e comorbidades por faixa etária — set–nov/2020.")

    df = dados["faixa_etaria"]
    if df.empty:
        tabela_indisponivel("descritiva_faixa_etaria.csv"); return

    aviso_recorte()
    df_f = recorte(df, mes_global) if mes_global != "Todos" else df
    grupo = agregar(df_f, "faixa_etaria",
                    ["pct_internado_entre_atendidos","pct_alguma_comorbidade","pct_buscou_atendimento"])
    grupo = ordenar_faixa(grupo)

    r_jovem = grupo[grupo["faixa_etaria"] == "18-29"]
    r_idoso = grupo[grupo["faixa_etaria"] == "60+"]
    metricas([
        ("Internação 18–29 anos", fmt_pct(r_jovem["pct_internado_entre_atendidos"].mean()),
         "Entre atendidos"),
        ("Internação 60+ anos",   fmt_pct(r_idoso["pct_internado_entre_atendidos"].mean()),
         "Entre atendidos"),
        ("Comorbidade 60+ anos",  fmt_pct(r_idoso["pct_alguma_comorbidade"].mean()),
         "Alguma das 6 condições"),
    ])

    col1, col2 = st.columns(2)
    with col1:
        barras(grupo, "faixa_etaria", "pct_internado_entre_atendidos",
               "Internação entre atendidos por faixa etária (%)",
               ytitle="% internação entre atendidos")
    with col2:
        barras(grupo, "faixa_etaria", "pct_alguma_comorbidade",
               "% com alguma comorbidade por faixa etária",
               ytitle="% com comorbidade")

    chamada("insight",
            "Pessoas com 60 anos ou mais não representam apenas um grupo vulnerável: elas concentram o maior risco "
            "de internação e a maior presença de comorbidades. Em um novo surto, esse público deve ser tratado "
            "como prioridade operacional.")
    chamada("acao",
            "Organizar um fluxo prioritário para pacientes 60+, combinando triagem rápida, monitoramento remoto "
            "e encaminhamento precoce. Isso ajuda a reduzir atrasos no atendimento e evita que casos de maior "
            "risco cheguem tarde ao hospital.")


def pagina_comorbidades():
    cabecalho("Quais doenças exigem atenção prioritária?",
              "Prevalência das comorbidades monitoradas na PNAD-COVID.")

    df = dados["comorbidades"]
    if df.empty:
        tabela_indisponivel("descritiva_comorbidades.csv"); return

    aviso_recorte()
    df_f = recorte(df, mes_global) if mes_global != "Todos" else df

    agg = agregar_count(df_f, "comorbidade")
    if agg.empty:
        agg = agregar(df_f, "comorbidade", ["pct_com_comorbidade"])
        agg = agg.rename(columns={"pct_com_comorbidade": "pct"}) if "pct_com_comorbidade" in agg.columns else agg
    agg = agg.sort_values("pct", ascending=False)

    if not agg.empty:
        comorb_hipert = agg[agg["comorbidade"].str.lower().str.contains("hipert", na=False)]["pct"].max()
        comorb_diab   = agg[agg["comorbidade"].str.lower().str.contains("diabe", na=False)]["pct"].max()
        metricas([
            ("1ª Hipertensão", fmt_pct(comorb_hipert), "Condição mais prevalente"),
            ("2ª Diabetes",    fmt_pct(comorb_diab),   "Segunda mais prevalente"),
            ("Foco prioritário", "Hipertensão e Diabetes",
             "As duas condições mais prevalentes — principal alvo de protocolos preventivos"),
        ])

    barras(agg, "comorbidade", "pct",
           "Prevalência das comorbidades (%)",
           orientation="h", xtitle="% da população com a condição")

    chamada("insight",
            "Hipertensão e diabetes são as condições mais comuns entre as comorbidades analisadas. "
            "Isso mostra que muitos pacientes de risco já podem ser identificados antes mesmo de "
            "procurarem o hospital durante um novo surto.")
    chamada("acao",
            "Usar os cadastros de pacientes hipertensos e diabéticos para criar acompanhamento preventivo "
            "em períodos de surto, com orientação, contato ativo e prioridade na triagem quando surgirem "
            "sintomas respiratórios.")


def pagina_renda_acesso():
    cabecalho("A renda influenciou o acesso ao cuidado?",
              "Busca por atendimento e internação entre atendidos por renda e plano de saúde.")

    df = dados["barreira"]
    if df.empty:
        tabela_indisponivel("analise_01_barreira_economica.csv"); return

    aviso_recorte()
    df_f = recorte(df, mes_global)
    if "plano_saude" in df_f.columns:
        df_f = df_f.dropna(subset=["plano_saude"])

    grupo_bar = [g for g in ["faixa_renda", "plano_saude"] if g in df_f.columns]
    df_bar = agregar(df_f, grupo_bar, ["pct_buscou_atendimento", "pct_internado_entre_atendidos"])
    if "ordem_renda" in df_f.columns:
        _ordem = df_f.groupby("faixa_renda")["ordem_renda"].first().to_dict()
        df_bar["ordem_renda"] = df_bar["faixa_renda"].map(_ordem)
        df_bar = df_bar.sort_values("ordem_renda")

    col1, col2 = st.columns(2)
    with col1:
        barras(df_bar, "faixa_renda", "pct_buscou_atendimento",
               "Busca por atendimento por renda e plano (%)",
               color="plano_saude" if "plano_saude" in df_bar.columns else None,
               ytitle="% buscou atendimento")
    with col2:
        barras(df_bar, "faixa_renda", "pct_internado_entre_atendidos",
               "Internação entre atendidos por renda e plano (%)",
               color="plano_saude" if "plano_saude" in df_bar.columns else None,
               ytitle="% internação entre atendidos")

    chamada("insight",
            "Em todas as faixas de renda, pessoas com plano de saúde buscaram mais atendimento do que pessoas "
            "sem plano. Isso indica que o acesso ao cuidado não depende só da gravidade dos sintomas, mas também "
            "da facilidade de chegar ao serviço de saúde.")
    chamada("cuidado",
            "A faixa \"Sem informação\" deve ser lida separadamente. Ela não representa baixa nem alta renda, "
            "mas pode indicar falta de informação cadastral ou pessoas fora da renda declarada.")
    chamada("acao",
            "Criar uma rota rápida para pacientes sem plano e com sintomas, com orientação clara, triagem ágil "
            "e encaminhamento adequado. O objetivo é reduzir atraso no atendimento e evitar que o paciente "
            "chegue em estado mais grave.")


def pagina_sus_privado():
    cabecalho("Onde a pressão hospitalar aparece primeiro?",
              "Internação entre atendidos por local de atendimento. "
              "Cada local é um recorte independente — valores não se somam.")

    df = dados["sus_privado"]
    if df.empty:
        tabela_indisponivel("analise_09_sus_privado.csv"); return

    aviso_recorte()
    df_f = recorte(df, mes_global)
    grupo_sus = [g for g in ["local_atendimento", "plano_saude"] if g in df_f.columns]
    df_sus = agregar(df_f, grupo_sus, ["pct_internado_entre_atendidos"])

    barras(df_sus, "local_atendimento", "pct_internado_entre_atendidos",
           "Internação entre atendidos por local de atendimento e plano (%)",
           color="plano_saude" if "plano_saude" in df_sus.columns else None,
           orientation="h", xtitle="% internação entre atendidos")

    chamada("cuidado",
            "Uma mesma pessoa pode ter procurado mais de um local de atendimento. Por isso, os percentuais "
            "devem ser lidos dentro de cada local e não devem ser somados como se formassem 100%.")
    chamada("insight",
            "O Hospital SUS aparece com maior percentual de internação entre os atendidos, principalmente entre "
            "pessoas sem plano. Isso indica que a porta pública tende a receber pacientes em condição mais grave "
            "ou com menor acesso prévio ao cuidado.")
    chamada("acao",
            "Integrar UBS, UPA e hospital em um fluxo claro de encaminhamento. Pacientes com sinais de risco "
            "devem ser identificados cedo e direcionados rapidamente, evitando demora no atendimento e "
            "sobrecarga na emergência.")


def pagina_territorios():
    # Hero header
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1F4E79 0%,#2E75B6 100%);
                border-radius:12px;padding:1.4rem 1.8rem;margin-bottom:1.4rem;'>
      <div style='font-size:1.45rem;font-weight:800;color:white;margin-bottom:.3rem;letter-spacing:-.01em;'>
        Onde antecipar capacidade hospitalar?
      </div>
      <div style='color:#B3D4F5;font-size:.93rem;'>
        Dependência do SUS &nbsp;·&nbsp; Baixa renda &nbsp;·&nbsp; Informalidade
        &nbsp;·&nbsp; por estado &nbsp;·&nbsp; PNAD-COVID set–nov/2020
      </div>
    </div>
    """, unsafe_allow_html=True)

    df = dados["mapa_desigualdade"]
    if df.empty:
        tabela_indisponivel("analise_05_mapa_desigualdade.csv"); return

    aviso_recorte()
    df_f = recorte(df, mes_global)

    colunas_agg = [c for c in [
        "pct_sem_plano","pct_ate_1_sm_entre_renda_informada",
        "pct_informal_entre_ocupados_com_info","media_itens_protecao",
    ] if c in df_f.columns]
    grupos_base = [g for g in ["sigla","estado","regiao"] if g in df_f.columns]
    if not grupos_base: grupos_base = ["sigla"]
    df_uf = agregar(df_f, grupos_base, colunas_agg)

    # Índice composto exploratório
    idx_cols = [c for c in ["pct_sem_plano","pct_ate_1_sm_entre_renda_informada",
                             "pct_informal_entre_ocupados_com_info"] if c in df_uf.columns]
    if len(idx_cols) >= 2:
        for c in idx_cols:
            mn, mx = df_uf[c].min(), df_uf[c].max()
            df_uf[f"_n_{c}"] = (df_uf[c] - mn) / (mx - mn) if mx > mn else 0.0
        df_uf["indice_vulnerabilidade"] = df_uf[[f"_n_{c}" for c in idx_cols]].mean(axis=1) * 100
        df_uf = df_uf.drop(columns=[f"_n_{c}" for c in idx_cols])

    # Classificação de prioridade
    ORDEM_PRI = {"Máxima":0,"Alta":1,"Moderada":2,"Baixa":3,"Sem dados":4}
    COR_PRI   = {"Máxima":"#B91C1C","Alta":"#D97706","Moderada":"#CA8A04","Baixa":"#16A34A","Sem dados":"#475569"}
    if "pct_sem_plano" in df_uf.columns:
        def _classi(v):
            if pd.isna(v): return "Sem dados"
            if v >= 85: return "Máxima"
            if v >= 75: return "Alta"
            if v >= 65: return "Moderada"
            return "Baixa"
        df_uf["prioridade"]      = df_uf["pct_sem_plano"].apply(_classi)
        df_uf["ordem_prioridade"] = df_uf["prioridade"].map(ORDEM_PRI)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    if "pct_sem_plano" in df_uf.columns and not df_uf["pct_sem_plano"].isna().all():
        idx_max    = df_uf["pct_sem_plano"].idxmax()
        uf_max     = df_uf.loc[idx_max]
        nn_mask    = df_uf["regiao"].isin(["Norte","Nordeste"]) if "regiao" in df_uf.columns \
                     else pd.Series([False]*len(df_uf), index=df_uf.index)
        media_nn   = df_uf.loc[nn_mask, "pct_sem_plano"].mean() if nn_mask.any() else np.nan
        media_br   = df_uf["pct_sem_plano"].mean()
        n_criticos = int((df_uf["pct_sem_plano"] >= 85).sum())
        metricas([
            ("Estado mais vulnerável",     str(uf_max.get("estado", uf_max.get("sigla","—"))),
             f"{fmt_pct(uf_max.get('pct_sem_plano'))} sem plano"),
            ("Norte/Nordeste — sem plano", fmt_pct(media_nn),   "Média das 2 regiões"),
            ("Brasil — sem plano",         fmt_pct(media_br),   "Média nacional"),
            ("Estados críticos (≥ 85%)",   fmt_num(n_criticos), "Prioridade máxima"),
        ])

    # ── Guia de prioridades ───────────────────────────────────────────────────
    st.markdown("""
    <div style='display:flex;gap:.6rem;margin:.9rem 0 1.2rem;flex-wrap:wrap;'>
      <div style='flex:1;min-width:140px;background:#FEE2E2;border-radius:8px;
                  padding:.6rem .85rem;border-left:4px solid #B91C1C;'>
        <div style='font-size:.72rem;font-weight:700;color:#991B1B;
                    text-transform:uppercase;letter-spacing:.05em;'>Maxima &#8805; 85%</div>
        <div style='font-size:.82rem;color:#172033;margin-top:.2rem;line-height:1.35;'>
          Antecipar insumos, leitos e teleorientação agora</div>
      </div>
      <div style='flex:1;min-width:140px;background:#FEF3C7;border-radius:8px;
                  padding:.6rem .85rem;border-left:4px solid #D97706;'>
        <div style='font-size:.72rem;font-weight:700;color:#92400E;
                    text-transform:uppercase;letter-spacing:.05em;'>Alta 75–84%</div>
        <div style='font-size:.82rem;color:#172033;margin-top:.2rem;line-height:1.35;'>
          Monitorar demanda e planejar expansão da rede</div>
      </div>
      <div style='flex:1;min-width:140px;background:#FEFCE8;border-radius:8px;
                  padding:.6rem .85rem;border-left:4px solid #CA8A04;'>
        <div style='font-size:.72rem;font-weight:700;color:#78350F;
                    text-transform:uppercase;letter-spacing:.05em;'>Moderada 65–74%</div>
        <div style='font-size:.82rem;color:#172033;margin-top:.2rem;line-height:1.35;'>
          Avaliar capacidade e definir gatilhos de alerta</div>
      </div>
      <div style='flex:1;min-width:140px;background:#ECFDF5;border-radius:8px;
                  padding:.6rem .85rem;border-left:4px solid #16A34A;'>
        <div style='font-size:.72rem;font-weight:700;color:#065F46;
                    text-transform:uppercase;letter-spacing:.05em;'>Baixa &lt; 65%</div>
        <div style='font-size:.82rem;color:#172033;margin-top:.2rem;line-height:1.35;'>
          Rede mista; acompanhar tendência privada</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Seletor + Mapa ────────────────────────────────────────────────────────
    opcoes: dict = {}
    if "pct_sem_plano" in df_uf.columns:
        opcoes["Dependência do SUS (% sem plano)"] = "pct_sem_plano"
    if "pct_ate_1_sm_entre_renda_informada" in df_uf.columns:
        opcoes["Baixa renda (% até 1 SM)"] = "pct_ate_1_sm_entre_renda_informada"
    if "pct_informal_entre_ocupados_com_info" in df_uf.columns:
        opcoes["Informalidade (% informal)"] = "pct_informal_entre_ocupados_com_info"
    if "indice_vulnerabilidade" in df_uf.columns:
        opcoes["Índice composto (exploratório)"] = "indice_vulnerabilidade"
    if not opcoes:
        st.error("Nenhuma coluna de vulnerabilidade disponível."); return

    col_sel, _ = st.columns([2, 3])
    with col_sel:
        ind_sel = st.selectbox("Indicador no mapa:", list(opcoes.keys()), key="mapa_ind_sel")
    value_col = opcoes[ind_sel]

    geojson = _carregar_geojson()

    if not geojson or "sigla" not in df_uf.columns:
        st.warning("Mapa ocultado: GeoJSON não disponível. O ranking abaixo mantém a leitura territorial.")

    else:
        import copy
        geojson_enriched = copy.deepcopy(geojson)
        df_plot = df_uf[df_uf["sigla"].notna()].copy()

        PROP_COLS = {
            "estado":"Estado","regiao":"Região",
            "pct_sem_plano":"% sem plano","pct_ate_1_sm_entre_renda_informada":"% até 1 SM",
            "pct_informal_entre_ocupados_com_info":"% informalidade",
            "indice_vulnerabilidade":"Índice composto","prioridade":"Prioridade",
        }
        for feat in geojson_enriched["features"]:
            sig = feat["properties"].get("sigla")
            row = df_plot[df_plot["sigla"] == sig]
            if not row.empty:
                r = row.iloc[0]
                for col_k in PROP_COLS:
                    if col_k in r.index:
                        v = r[col_k]
                        feat["properties"][col_k] = (
                            round(float(v), 1) if pd.notna(v) and col_k not in ("estado","regiao","prioridade")
                            else (str(v) if pd.notna(v) else "—")
                        )

        try:
            from branca.colormap import LinearColormap
            vmin = float(df_plot[value_col].min())
            vmax = float(df_plot[value_col].max())
            colormap = LinearColormap(
                colors=["#22C55E","#FDE68A","#F59E0B","#B91C1C"],
                vmin=vmin, vmax=vmax,
                caption=nome_lab(value_col),
            )
            def _fill(feature):
                sig = feature["properties"].get("sigla")
                row = df_plot[df_plot["sigla"] == sig]
                if row.empty or pd.isna(row.iloc[0].get(value_col)):
                    return "#cccccc"
                return colormap(float(row.iloc[0][value_col]))
        except Exception:
            def _fill(_): return "#2E75B6"
            colormap = None

        m = folium.Map(
            location=[-14.0, -52.0],
            zoom_start=4,
            tiles="CartoDB positron",
            prefer_canvas=True,
        )

        folium.GeoJson(
            geojson_enriched,
            style_function=lambda feat: {
                "fillColor":   _fill(feat),
                "color":       "white",
                "weight":      1.0,
                "fillOpacity": 0.87,
            },
            highlight_function=lambda _: {
                "weight":      2.5,
                "color":       "#1F4E79",
                "fillOpacity": 0.95,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["estado","regiao","pct_sem_plano","pct_ate_1_sm_entre_renda_informada",
                        "pct_informal_entre_ocupados_com_info","prioridade"],
                aliases=["Estado","Região","Sem plano","Até 1 SM","Informalidade","Prioridade"],
                localize=True,
                sticky=True,
                style=(
                    "background-color:white;color:#172033;font-family:sans-serif;"
                    "font-size:12px;padding:8px 12px;border-radius:6px;"
                    "border:1px solid #DDE6F0;box-shadow:0 2px 6px rgba(0,0,0,.12);"
                ),
            ),
            popup=folium.GeoJsonPopup(
                fields=list(PROP_COLS.keys()),
                aliases=list(PROP_COLS.values()),
                localize=True,
                max_width=260,
            ),
        ).add_to(m)

        if colormap:
            colormap.add_to(m)

        st_folium(m, use_container_width=True, height=540, returned_objects=[])

    st.divider()

    # ── Ranking | Perfil | Comparação regional ────────────────────────────────
    eixo_y = "estado" if "estado" in df_uf.columns else "sigla"
    col_rank, col_perfil, col_reg = st.columns([5, 4, 3])

    with col_rank:
        st.markdown(f"##### Top 10 — {nome_lab(value_col)}")
        top10 = df_uf.sort_values(value_col, ascending=False).head(10).reset_index(drop=True)
        max_val_r = float(top10[value_col].max()) if not top10.empty else 1
        cards_html = ""
        for i, row_r in top10.iterrows():
            nome_est = str(row_r.get(eixo_y, "—"))
            val_r    = float(row_r[value_col]) if pd.notna(row_r.get(value_col)) else 0
            pri_r    = str(row_r.get("prioridade", "—"))
            cor_r    = COR_PRI.get(pri_r, "#475569")
            w_bar    = val_r / max_val_r * 100 if max_val_r else 0
            rank_lbl = f"<span style='font-size:.78rem;color:#8A99AB;font-weight:700;'>{i+1}</span>"
            cards_html += f"""
            <div style='display:flex;align-items:center;gap:.55rem;padding:.4rem .5rem;
                        background:#FFFFFF;border:1px solid #E8EDF4;border-left:4px solid {cor_r};
                        border-radius:7px;margin-bottom:.35rem;'>
              <div style='width:22px;text-align:center;flex-shrink:0;'>{rank_lbl}</div>
              <div style='flex:1;min-width:0;'>
                <div style='display:flex;justify-content:space-between;align-items:baseline;'>
                  <span style='font-size:.82rem;font-weight:700;color:#172033;
                               white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
                               max-width:120px;display:inline-block;'>{nome_est}</span>
                  <span style='font-size:.82rem;font-weight:800;color:{cor_r};flex-shrink:0;margin-left:.4rem;'>{val_r:.1f}%</span>
                </div>
                <div style='background:#E8EDF4;border-radius:2px;height:4px;margin-top:3px;'>
                  <div style='background:{cor_r};width:{w_bar:.0f}%;height:4px;border-radius:2px;'></div>
                </div>
              </div>
              <div style='font-size:.68rem;font-weight:700;color:white;background:{cor_r};
                          padding:2px 6px;border-radius:4px;flex-shrink:0;white-space:nowrap;'>{pri_r}</div>
            </div>"""
        st.markdown(cards_html, unsafe_allow_html=True)

    with col_perfil:
        st.markdown("##### Perfil do estado")
        estados_lista = sorted(df_uf[eixo_y].dropna().tolist())
        if estados_lista:
            uf_sel  = st.selectbox("Selecionar estado:", estados_lista, key="mapa_uf_sel")
            rows_uf = df_uf[df_uf[eixo_y] == uf_sel]
            if not rows_uf.empty:
                r   = rows_uf.iloc[0]
                pri = str(r.get("prioridade","—"))
                cor = COR_PRI.get(pri,"#475569")

                # Build items with mini bars
                detail_items = []
                if "regiao" in r.index and pd.notna(r.get("regiao")):
                    detail_items.append(("Região", str(r["regiao"]), None, None))
                for col_k, label_k in [
                    ("pct_sem_plano","Sem plano"),
                    ("pct_ate_1_sm_entre_renda_informada","Até 1 SM"),
                    ("pct_informal_entre_ocupados_com_info","Informalidade"),
                    ("indice_vulnerabilidade","Índice composto"),
                ]:
                    if col_k in r.index and pd.notna(r.get(col_k)):
                        val_raw = float(r[col_k])
                        max_val = float(df_uf[col_k].max()) if col_k in df_uf.columns else 100
                        detail_items.append((label_k, fmt_pct(val_raw) if col_k != "indice_vulnerabilidade"
                                             else fmt_num(val_raw,1), val_raw, max_val))

                rows_html = ""
                for k, v, val_raw, max_val in detail_items:
                    bar_html = ""
                    if val_raw is not None and max_val:
                        pct_w = min(100, val_raw / max_val * 100)
                        bar_html = (f"<div style='background:#E8EDF4;border-radius:2px;height:4px;"
                                    f"margin-top:3px;'><div style='background:{cor};width:{pct_w:.0f}%;"
                                    f"height:4px;border-radius:2px;'></div></div>")
                    rows_html += (
                        f"<div style='margin:.38rem 0;'>"
                        f"<div style='display:flex;justify-content:space-between;'>"
                        f"<span style='color:#5F6B7A;font-size:.83rem;'>{k}</span>"
                        f"<span style='font-weight:700;font-size:.83rem;color:#172033;'>{v}</span>"
                        f"</div>{bar_html}</div>"
                    )
                st.markdown(f"""
                <div style='border:1px solid #DDE6F0;border-left:5px solid {cor};
                            border-radius:8px;padding:1rem 1.1rem;background:#FAFCFF;'>
                  <div style='font-size:1.05rem;font-weight:800;color:#1F4E79;'>{uf_sel}</div>
                  {rows_html}
                  <div style='margin-top:.85rem;padding:.4rem .5rem;background:{cor};color:white;
                              border-radius:5px;font-size:.82rem;text-align:center;font-weight:700;
                              letter-spacing:.04em;'>Prioridade {pri}</div>
                </div>""", unsafe_allow_html=True)

    with col_reg:
        st.markdown("##### Por região")
        if "regiao" in df_uf.columns and "pct_sem_plano" in df_uf.columns:
            reg_sum = (df_uf.groupby("regiao")["pct_sem_plano"]
                       .mean().reset_index()
                       .sort_values("pct_sem_plano", ascending=False))
            COR_REG = {"Norte":"#B91C1C","Nordeste":"#D97706",
                       "Centro-Oeste":"#7C3AED","Sudeste":"#2563EB","Sul":"#059669"}
            max_reg = float(reg_sum["pct_sem_plano"].max())
            for _, rr in reg_sum.iterrows():
                reg = str(rr["regiao"]); val = float(rr["pct_sem_plano"])
                cr  = COR_REG.get(reg,"#475569")
                w   = val / max_reg * 100 if max_reg else 0
                st.markdown(f"""
                <div style='margin:.4rem 0;padding:.55rem .8rem;background:#FFFFFF;
                            border:1px solid #E8EDF4;border-left:4px solid {cr};border-radius:7px;'>
                  <div style='display:flex;justify-content:space-between;margin-bottom:.3rem;'>
                    <span style='font-size:.83rem;font-weight:600;color:#172033;'>{reg}</span>
                    <span style='font-size:.85rem;font-weight:800;color:{cr};'>{val:.1f}%</span>
                  </div>
                  <div style='background:#E8EDF4;border-radius:3px;height:6px;'>
                    <div style='background:{cr};width:{w:.0f}%;height:6px;border-radius:3px;'></div>
                  </div>
                </div>""", unsafe_allow_html=True)

    # ── Tabela completa dos 27 estados ────────────────────────────────────────
    st.divider()
    with st.expander("Ver todos os 27 estados — tabela completa por prioridade", expanded=False):
        if "ordem_prioridade" in df_uf.columns:
            tabela = df_uf.sort_values("ordem_prioridade").copy()
        else:
            tabela = df_uf.copy()

        cols_tab = [c for c in [eixo_y,"regiao","pct_sem_plano",
                                 "pct_ate_1_sm_entre_renda_informada",
                                 "pct_informal_entre_ocupados_com_info",
                                 "indice_vulnerabilidade","prioridade"] if c in tabela.columns]
        tab_d = tabela[cols_tab].rename(columns={
            eixo_y:"Estado","regiao":"Região",
            "pct_sem_plano":"% sem plano",
            "pct_ate_1_sm_entre_renda_informada":"% até 1 SM",
            "pct_informal_entre_ocupados_com_info":"% informal",
            "indice_vulnerabilidade":"Índice",
            "prioridade":"Prioridade",
        })
        for col_p in ["% sem plano","% até 1 SM","% informal","Índice"]:
            if col_p in tab_d.columns:
                tab_d[col_p] = tab_d[col_p].apply(
                    lambda x: f"{x:.1f}%" if pd.notna(x) else "—")

        def _estilo_pri(v):
            return {
                "Máxima":  "background-color:#FEE2E2;color:#991B1B;font-weight:700",
                "Alta":    "background-color:#FEF3C7;color:#92400E;font-weight:600",
                "Moderada":"background-color:#FEFCE8;color:#78350F;font-weight:600",
                "Baixa":   "background-color:#ECFDF5;color:#065F46;font-weight:600",
            }.get(v,"")

        if "Prioridade" in tab_d.columns:
            st.dataframe(tab_d.style.map(_estilo_pri, subset=["Prioridade"]),
                         use_container_width=True, hide_index=True)
        else:
            st.dataframe(tab_d, use_container_width=True, hide_index=True)

    chamada("insight",
            "O mapa mostra que a vulnerabilidade se concentra principalmente no Norte e no Nordeste. "
            "Nessas regiões, a combinação de alta dependência do SUS e maior presença de baixa renda pode "
            "fazer a demanda chegar mais rápido à rede pública.")
    chamada("acao",
            "Priorizar planejamento regional nas UFs mais vulneráveis, com reforço de triagem, teleorientação, "
            "estoque de insumos e leitos de retaguarda. A preparação deve considerar o risco territorial, "
            "não apenas o tamanho da população.")


def pagina_trabalho():
    cabecalho("Quem teve menos capacidade de se proteger?",
              "Capacidade de isolamento por tipo de trabalho — proxy de exposição ao vírus.")

    df = dados["informalidade"]
    if df.empty:
        tabela_indisponivel("analise_02_informalidade_risco.csv"); return

    aviso_recorte()
    df_f = recorte(df, mes_global)

    if "formalidade_trabalho" in df_f.columns and "pct_home_office" in df_f.columns:
        grupo_form = agregar(df_f, "formalidade_trabalho", ["pct_home_office"])
        barras(grupo_form, "formalidade_trabalho", "pct_home_office",
               "% em home office por tipo de vínculo (%)",
               orientation="h", xtitle="% home office")

    grupo_cat_cols = [g for g in ["categoria_ocupacional", "formalidade_trabalho"] if g in df_f.columns]
    grupo_cat = agregar(df_f, grupo_cat_cols, ["pct_home_office"])
    barras(grupo_cat,
           "categoria_ocupacional" if "categoria_ocupacional" in grupo_cat.columns else "formalidade_trabalho",
           "pct_home_office",
           "Home office por categoria ocupacional (%)",
           color="formalidade_trabalho" if "formalidade_trabalho" in grupo_cat.columns else None,
           orientation="h", top=12, xtitle="% home office")

    chamada("cuidado",
            "O home office foi usado como sinal de possibilidade de isolamento, não como causa direta de "
            "internação. A diferença entre os grupos também pode envolver idade, ocupação, renda e acesso "
            "ao atendimento.")
    chamada("insight",
            "Trabalhadores informais e algumas categorias presenciais tiveram menor possibilidade de home "
            "office. Isso indica maior exposição durante um surto e maior dificuldade para procurar "
            "atendimento em horário comercial.")
    chamada("acao",
            "Criar alternativas de atendimento para trabalhadores presenciais, como horários estendidos, "
            "orientação fora do horário comercial e canais simples de triagem. Isso ajuda o paciente a "
            "buscar cuidado cedo, sem depender apenas do expediente tradicional.")


def pagina_protecao_domiciliar():
    cabecalho("A proteção domiciliar influencia o contexto do surto?",
              "Itens de proteção em casa: apresentado como contexto de prevenção comunitária.")

    aviso_recorte()
    df_m = dados["moradia"]
    if not df_m.empty:
        df_f = recorte(df_m, mes_global)
        if "nivel_protecao_domiciliar" in df_f.columns:
            grupo = agregar(df_f, "nivel_protecao_domiciliar",
                            ["media_itens_protecao","pct_pegou_emprestimo","pct_internado_entre_atendidos"])
            col1, col2 = st.columns(2)
            with col1:
                barras(grupo, "nivel_protecao_domiciliar", "media_itens_protecao",
                       "Itens de proteção por nível domiciliar", ytitle="Média de itens")
            with col2:
                barras(grupo, "nivel_protecao_domiciliar", "pct_pegou_emprestimo",
                       "% com endividamento por nível de proteção (%)")
    st.divider()
    df_i = dados["itens_protecao"]
    if not df_i.empty:
        df_fi = recorte(df_i, mes_global)
        if "item_protecao" in df_fi.columns and "pct_tem_item" in df_fi.columns:
            agg = agregar(df_fi, "item_protecao", ["pct_tem_item"])
            barras(agg.sort_values("pct_tem_item", ascending=False),
                   "item_protecao", "pct_tem_item",
                   "Posse de itens de proteção domiciliar (%)",
                   orientation="h", xtitle="% tem o item")
    chamada("cuidado",
            "Os dados não mostram uma relação forte entre número de itens de proteção em casa e internação. "
            "Por isso, essa tela deve ser lida como contexto de prevenção comunitária, não como critério "
            "direto para priorizar pacientes no hospital.")
    chamada("insight",
            "A maioria da população já tinha itens básicos de proteção, como sabão, máscara, desinfetante "
            "e álcool. A exceção mais clara foi o uso de luvas descartáveis, que apareceu com presença bem "
            "menor. Isso indica que a proteção domiciliar estava mais concentrada em medidas simples de "
            "higiene e máscara.")
    chamada("acao",
            "Usar essa informação para orientar campanhas preventivas fora do hospital. Em um novo surto, "
            "o foco deve ser reforçar medidas simples e acessíveis, como higiene das mãos, uso correto de "
            "máscara, limpeza do ambiente e orientação para isolamento domiciliar quando necessário.")


def pagina_protecao_social():
    cabecalho("Benefícios ajudam a identificar vulnerabilidade?",
              "Distribuição do auxílio emergencial e Bolsa Família por faixa de renda.")

    df = dados["protecao_social"]
    if df.empty:
        tabela_indisponivel("analise_04_protecao_social.csv"); return

    aviso_recorte()
    df_f = recorte(df, mes_global)
    if "ordem_renda" in df_f.columns:
        df_f = df_f.sort_values("ordem_renda")

    pct_ate1 = df_f[df_f["faixa_renda"] == "Até 1 SM"]["pct_recebeu_auxilio"].mean() \
        if "faixa_renda" in df_f.columns and "pct_recebeu_auxilio" in df_f.columns else np.nan
    pct_bf_ate1 = df_f[df_f["faixa_renda"] == "Até 1 SM"]["pct_recebeu_bolsa_familia"].mean() \
        if "faixa_renda" in df_f.columns and "pct_recebeu_bolsa_familia" in df_f.columns else np.nan
    pct_acima4 = df_f[df_f["faixa_renda"] == "Acima 4 SM"]["pct_recebeu_auxilio"].mean() \
        if "faixa_renda" in df_f.columns and "pct_recebeu_auxilio" in df_f.columns else np.nan
    metricas([
        ("Auxílio em até 1 SM",      fmt_pct(pct_ate1),    "Alcance entre os mais vulneráveis"),
        ("Bolsa Família em até 1 SM", fmt_pct(pct_bf_ate1), "Marcador de pobreza extrema"),
        ("Auxílio acima de 4 SM",     fmt_pct(pct_acima4),  "Alcance entre os de maior renda"),
    ])

    cols_ben = [c for c in [
        "pct_recebeu_auxilio","pct_recebeu_bolsa_familia","pct_recebeu_seguro_desemprego"
    ] if c in df_f.columns]
    if cols_ben and "faixa_renda" in df_f.columns:
        df_ben = agregar(df_f, "faixa_renda", cols_ben)
        if "ordem_renda" in df_f.columns:
            _om = df_f.groupby("faixa_renda")["ordem_renda"].first().to_dict()
            df_ben["ordem_renda"] = df_ben["faixa_renda"].map(_om)
            df_ben = df_ben.sort_values("ordem_renda")
        renda_order = list(df_ben["faixa_renda"].tolist()) if "ordem_renda" in df_ben.columns else None
        long = df_ben[["faixa_renda"] + cols_ben].dropna(how="all", subset=cols_ben).melt(
            id_vars="faixa_renda", value_vars=cols_ben, var_name="beneficio", value_name="pct"
        )
        long["beneficio"] = long["beneficio"].map(nome_lab)
        fig = px.bar(long.dropna(), x="faixa_renda", y="pct", color="beneficio",
                     barmode="group",
                     category_orders={"faixa_renda": renda_order} if renda_order else {},
                     title="Benefícios sociais por faixa de renda (%)", text="pct")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
        _layout_fig(fig)
        st.plotly_chart(fig, use_container_width=True)

    chamada("cuidado",
            "Benefício social não é um indicador clínico. Ele ajuda a identificar famílias que podem ter mais "
            "dificuldade para se isolar, comprar itens básicos, fazer teste ou procurar atendimento rapidamente.")
    chamada("insight",
            "O auxílio emergencial aparece com maior frequência nas faixas de menor renda, especialmente até "
            "1 salário mínimo. Isso mostra que esses grupos podem precisar de mais apoio e orientação durante "
            "um novo surto.")
    chamada("acao",
            "Integrar o atendimento de saúde com a assistência social. Em períodos de surto, pacientes em "
            "situação de vulnerabilidade devem receber orientação ativa, canais simples de contato e "
            "encaminhamento rápido quando apresentarem sintomas.")


def pagina_escolaridade_genero():
    cabecalho("Escolaridade, gênero e comunicação",
              "Perfil de escolaridade e gênero — ângulo de comunicação, não de risco clínico.")

    df = dados["escolaridade_genero"]
    if df.empty:
        tabela_indisponivel("analise_07_escolaridade_genero.csv"); return

    aviso_recorte()
    df_f = recorte(df, mes_global)
    grupo_esc = agregar(df_f, "escolaridade", ["pct_home_office", "pct_internado_entre_atendidos"])
    grupo_sex = agregar(df_f, "sexo",         ["pct_home_office", "pct_internado_entre_atendidos"])

    col1, col2 = st.columns(2)
    with col1:
        barras(grupo_esc, "escolaridade", "pct_home_office",
               "Home office por escolaridade — acesso a canais digitais (%)",
               orientation="h", xtitle="% em home office")
    with col2:
        barras(grupo_sex, "sexo", "pct_home_office",
               "Home office por sexo (%)",
               orientation="h", xtitle="% em home office")

    col3, col4 = st.columns(2)
    with col3:
        barras(grupo_esc, "escolaridade", "pct_internado_entre_atendidos",
               "Internação entre atendidos por escolaridade (%)",
               orientation="h", xtitle="% internação entre atendidos")
    with col4:
        barras(grupo_sex, "sexo", "pct_internado_entre_atendidos",
               "Internação entre atendidos por sexo (%)",
               orientation="h", xtitle="% internação entre atendidos")

    chamada("cuidado",
            "Escolaridade e gênero não devem ser usados como causa direta de gravidade. Esses recortes ajudam "
            "principalmente a entender como a comunicação do hospital deve chegar a cada público.")
    chamada("insight",
            "Pessoas com maior escolaridade aparecem com maior acesso ao home office, enquanto grupos com menor "
            "escolaridade tendem a ter menor acesso a canais digitais e maior dificuldade de isolamento. Isso "
            "indica que uma única estratégia de comunicação não alcança todos da mesma forma.")
    chamada("acao",
            "Adaptar a comunicação por público e canal: usar meios digitais para quem tem maior acesso online, "
            "mas reforçar rádio, agentes comunitários, UBS, mensagens simples e busca ativa para grupos com "
            "menor acesso. Em um novo surto, a orientação precisa chegar antes do agravamento.")


def pagina_correlacoes():
    cabecalho("O risco é só clínico ou também social?",
              "Relações entre fatores sociais e desfechos clínicos.")

    if mes_global != "Todos":
        st.info("Esta análise usa toda a série histórica (set–nov/2020). O filtro de mês não se aplica aqui.", icon="ℹ️")

    df = dados["correlacoes"].copy()
    if df.empty:
        tabela_indisponivel("correlacoes_economico_clinico.csv"); return

    df["correlacao_abs"] = df["correlacao"].abs()
    df["par"] = df["variavel_social"].astype(str) + " → " + df["desfecho_clinico"].astype(str)
    df = df.sort_values("correlacao_abs")

    metricas([
        ("Maior correlação", fmt_num(df["correlacao_abs"].max(), 4), "Relação muito fraca"),
        ("Pares avaliados", fmt_num(df.shape[0]), "Fatores sociais × desfechos clínicos"),
        ("Interpretação geral",
         "Relação muito fraca",
         "Fatores sociais ajudam no contexto, não substituem critério clínico"),
    ])

    fig = px.bar(df, x="correlacao_abs", y="par",
                 color="direcao" if "direcao" in df.columns else None,
                 orientation="h",
                 title="Força absoluta das correlações sociais × desfechos clínicos",
                 text="correlacao")
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside", cliponaxis=False)
    _layout_fig(fig, ytitle="")
    fig.update_layout(xaxis_title="Correlação absoluta", xaxis_range=[0, 0.07])
    st.plotly_chart(fig, use_container_width=True)

    chamada("cuidado",
            "Correlação não significa causa. Os resultados mostram relações muito fracas, então renda, plano "
            "de saúde, trabalho ou proteção domiciliar não devem ser usados sozinhos para prever internação "
            "ou entubação.")
    chamada("insight",
            "O risco de agravamento não é explicado por um único fator social isolado. Para o hospital, a "
            "leitura mais útil é combinar fatores clínicos, como idade, sintomas e comorbidades, com fatores "
            "de acesso, como plano de saúde, renda e território.")
    chamada("acao",
            "Separar a triagem em duas camadas: uma clínica, para identificar gravidade, e outra social, para "
            "identificar barreiras de acesso. Assim, o hospital prioriza quem tem maior risco médico sem "
            "ignorar quem pode chegar tarde ao cuidado.")


def pagina_alerta_mensal():
    cabecalho("Painel de alerta mensal",
              "Monitoramento mensal — testagem, positividade, internação e entubação · set–nov/2020.")

    if mes_global != "Todos":
        st.info("Esta página exibe sempre a série completa (set–nov/2020). O filtro de mês não se aplica aqui.", icon="ℹ️")

    df_ev = ordenar_mes(dados["evolucao"])
    df_k  = ordenar_mes(dados["kpis"])

    if df_ev.empty:
        tabela_indisponivel("analise_06_evolucao_mensal.csv"); return

    df_busca = (
        df_k[df_k["v1013"].isin([9,10,11])][["v1013","pct_buscou_atendimento"]].copy()
        if not df_k.empty and "v1013" in df_k.columns else pd.DataFrame()
    )
    df_plot = df_ev.merge(df_busca, on="v1013", how="left") if not df_busca.empty else df_ev

    dark    = is_dark()
    bg_card = "#1C2333" if dark else "#FFFFFF"
    bdr     = "#2D3A4A" if dark else "#DDE6F0"
    ink     = "#DDE6F0" if dark else "#172033"
    muted   = "#8A99AB" if dark else "#5F6B7A"
    bg_page = "#0F1117" if dark else "#F6F8FB"

    # ── Semáforo: thresholds por indicador ────────────────────────────────────
    # retorna (cor_hex, rótulo_status)
    def _semaforo(col, val):
        if pd.isna(val): return "#94A3B8", "—"
        thresholds = {
            "pct_internado_entre_atendidos":        [(8, "#22C55E","Normal"),(10,"#F59E0B","Atenção"),(999,"#EF4444","Alerta")],
            "pct_entubado_entre_internados":         [(20,"#22C55E","Normal"),(26,"#F59E0B","Atenção"),(999,"#EF4444","Alerta")],
            "pct_positivo_entre_resultados_validos": [(20,"#22C55E","Normal"),(28,"#F59E0B","Atenção"),(999,"#EF4444","Alerta")],
            "pct_fez_teste":                         [(10,"#F59E0B","Baixo"),(13,"#22C55E","Adequado"),(999,"#22C55E","Bom")],
            "pct_buscou_atendimento":               [(22,"#22C55E","Normal"),(28,"#F59E0B","Atenção"),(999,"#EF4444","Alerta")],
            "pct_dificuldade_respirar":             [(0.35,"#22C55E","Normal"),(0.5,"#F59E0B","Atenção"),(999,"#EF4444","Alerta")],
        }
        for limite, cor, label in thresholds.get(col, [(999,"#94A3B8","—")]):
            if val <= limite:
                return cor, label
        return "#94A3B8", "—"

    # ── Cartões mensais ───────────────────────────────────────────────────────
    INDICADORES = [
        ("pct_fez_teste",                         "Fez teste"),
        ("pct_positivo_entre_resultados_validos",  "Positividade"),
        ("pct_buscou_atendimento",                 "Buscou atendimento"),
        ("pct_internado_entre_atendidos",          "Internação"),
        ("pct_entubado_entre_internados",          "Entubação"),
        ("pct_dificuldade_respirar",               "Dif. respiratória"),
    ]

    meses_ord = df_plot.sort_values("ordem_mes")["mes_nome"].tolist() if "ordem_mes" in df_plot.columns else df_plot["mes_nome"].tolist()
    cols_mes = st.columns(len(meses_ord))

    for i, (col_st, mes) in enumerate(zip(cols_mes, meses_ord)):
        row_cur = df_plot[df_plot["mes_nome"] == mes].iloc[0] if not df_plot[df_plot["mes_nome"] == mes].empty else pd.Series(dtype=float)
        row_prev = df_plot[df_plot["mes_nome"] == meses_ord[i-1]].iloc[0] if i > 0 else None

        linhas_html = ""
        for col_k, label_k in INDICADORES:
            val  = row_cur.get(col_k)
            cor_sem, status = _semaforo(col_k, val if pd.notna(val) else None)
            val_txt = f"{val:.1f}%" if pd.notna(val) else "—"

            delta_html = ""
            if row_prev is not None:
                prev_val = row_prev.get(col_k)
                if pd.notna(val) and pd.notna(prev_val):
                    diff = val - float(prev_val)
                    seta = "▲" if diff > 0 else "▼"
                    cor_delta = "#EF4444" if (diff > 0 and col_k not in ("pct_fez_teste",)) else "#22C55E"
                    delta_html = (f"<span style='font-size:.7rem;color:{cor_delta};"
                                  f"font-weight:700;margin-left:.3rem;'>{seta}{abs(diff):.1f}pp</span>")

            linhas_html += (
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"padding:.3rem 0;border-bottom:1px solid {bdr};'>"
                f"<span style='font-size:.78rem;color:{muted};'>{label_k}</span>"
                f"<span style='display:flex;align-items:center;'>"
                f"<span style='font-size:.82rem;font-weight:700;color:{ink};'>{val_txt}</span>"
                f"{delta_html}"
                f"<span style='width:8px;height:8px;border-radius:50%;background:{cor_sem};"
                f"margin-left:.45rem;flex-shrink:0;'></span>"
                f"</span></div>"
            )

        header_bg = {"Setembro":"#1F4E79","Outubro":"#7C3AED","Novembro":"#065F46"}.get(mes, "#1F4E79")
        with col_st:
            st.markdown(f"""
            <div style='background:{bg_card};border:1px solid {bdr};border-radius:10px;overflow:hidden;'>
              <div style='background:{header_bg};padding:.6rem .85rem;'>
                <div style='font-size:.95rem;font-weight:800;color:#FFFFFF;'>{mes}</div>
                <div style='font-size:.72rem;color:rgba(255,255,255,.7);'>2020</div>
              </div>
              <div style='padding:.6rem .85rem;'>
                {linhas_html}
              </div>
            </div>""", unsafe_allow_html=True)

    # ── Legenda semáforo ──────────────────────────────────────────────────────
    st.markdown(
        f"<div style='margin:.6rem 0 1.2rem;display:flex;gap:1.2rem;'>"
        f"<span style='font-size:.75rem;color:{muted};'>"
        f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#22C55E;margin-right:.3rem;'></span>Normal</span>"
        f"<span style='font-size:.75rem;color:{muted};'>"
        f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#F59E0B;margin-right:.3rem;'></span>Atenção</span>"
        f"<span style='font-size:.75rem;color:{muted};'>"
        f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#EF4444;margin-right:.3rem;'></span>Alerta</span>"
        f"<span style='font-size:.75rem;color:{muted};margin-left:.5rem;'>· ▲▼ variação vs mês anterior em pontos percentuais</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Gráficos com zona de alerta ───────────────────────────────────────────
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        cols_g1 = [c for c in ["pct_fez_teste","pct_positivo_entre_resultados_validos","pct_buscou_atendimento"] if c in df_plot.columns]
        if cols_g1:
            d1 = ordenar_mes(df_plot)[["mes_nome"] + cols_g1].dropna(how="all", subset=cols_g1)
            long1 = d1.melt(id_vars="mes_nome", value_vars=cols_g1, var_name="ind", value_name="val")
            long1["ind"] = long1["ind"].map(nome_lab)
            fig1 = px.line(long1, x="mes_nome", y="val", color="ind", markers=True,
                           title="Acesso e testagem")
            fig1.update_traces(line_width=2.5, marker_size=8)
            fig1.add_hrect(y0=28, y1=50, fillcolor="#EF4444", opacity=0.08,
                           annotation_text="zona de alerta — testes positivos", annotation_position="top left",
                           annotation_font_size=10)
            _layout_fig(fig1, ytitle="%")
            st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        cols_g2 = [c for c in ["pct_internado_entre_atendidos","pct_entubado_entre_internados"] if c in df_ev.columns]
        if cols_g2:
            d2 = ordenar_mes(df_ev)[["mes_nome"] + cols_g2].dropna(how="all", subset=cols_g2)
            long2 = d2.melt(id_vars="mes_nome", value_vars=cols_g2, var_name="ind", value_name="val")
            long2["ind"] = long2["ind"].map(nome_lab)
            fig2 = px.line(long2, x="mes_nome", y="val", color="ind", markers=True,
                           title="Gravidade — internação e entubação")
            fig2.update_traces(line_width=2.5, marker_size=8)
            fig2.add_hrect(y0=10, y1=50, fillcolor="#EF4444", opacity=0.08,
                           annotation_text="zona de alerta — internação", annotation_position="top left",
                           annotation_font_size=10)
            _layout_fig(fig2, ytitle="%")
            st.plotly_chart(fig2, use_container_width=True)

    # ── Gatilhos de ação ──────────────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:.72rem;font-weight:700;color:{muted};"
        f"text-transform:uppercase;letter-spacing:.06em;margin:.6rem 0 .6rem;'>"
        f"Gatilhos de ação recomendados</div>", unsafe_allow_html=True)

    gatilhos = [
        ("#EF4444", "Internação > 10%",          "Acionar protocolo de expansão de leitos e reforço de plantão imediatamente."),
        ("#F59E0B", "Testes positivos > 28%",    "Ampliar testagem e revisar fluxo de triagem — surto em aceleração."),
        ("#F59E0B", "Procura por atendimento ↑", "Monitorar diariamente — demanda precede internação em 2–3 semanas."),
        ("#EF4444", "Entubação > 26%",           "Verificar disponibilidade de UTI e insumos críticos com urgência."),
    ]
    g_cols = st.columns(len(gatilhos))
    for col_g, (cor, titulo, desc) in zip(g_cols, gatilhos):
        with col_g:
            st.markdown(
                f"<div style='background:{bg_card};border:1px solid {bdr};"
                f"border-top:3px solid {cor};border-radius:8px;padding:.7rem .8rem;height:100%;'>"
                f"<div style='font-size:.8rem;font-weight:700;color:{cor};margin-bottom:.3rem;'>{titulo}</div>"
                f"<div style='font-size:.78rem;color:{muted};line-height:1.45;'>{desc}</div>"
                f"</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    chamada("cuidado",
            "Os indicadores mensais não servem para prever o futuro sozinhos, mas ajudam a perceber mudança "
            "de tendência. A procura por atendimento, os casos confirmados e as internações devem ser "
            "acompanhados juntos.")
    chamada("insight",
            "O aumento da procura por atendimento costuma aparecer antes da pressão nos leitos. Por isso, "
            "acompanhar esses sinais mês a mês ajuda o hospital a agir antes que o crescimento dos casos "
            "vire sobrecarga na emergência e na UTI.")
    chamada("acao",
            "Acompanhar semanalmente a procura por atendimento, o aumento de casos confirmados, as internações "
            "e os casos graves. Quando esses indicadores começarem a subir, o hospital deve reforçar equipe, "
            "triagem, insumos e leitos antes da sobrecarga.")


def pagina_risco_combinado():
    cabecalho("Quem deve ter prioridade na triagem?",
              "Faixa etária, comorbidade e internação combinadas para orientar a priorização.")

    if mes_global != "Todos":
        st.info("Esta análise usa toda a série histórica agregada. O filtro de mês não se aplica aqui.", icon="ℹ️")

    df = dados["faixa_etaria"]
    if df.empty:
        tabela_indisponivel("descritiva_faixa_etaria.csv"); return

    grupo = agregar(df, "faixa_etaria",
                    ["pct_internado_entre_atendidos","pct_alguma_comorbidade","pct_buscou_atendimento"])
    grupo = ordenar_faixa(grupo)

    def _nivel(row):
        fe = row.get("faixa_etaria", "")
        comorb = row.get("pct_alguma_comorbidade") or 0
        if fe == "60+" and comorb > 40:
            return "🔴 Máxima"
        if fe == "60+" or (fe == "50-59" and comorb > 25):
            return "🟠 Alta"
        if fe in ("40-49","50-59"):
            return "🟡 Moderada"
        return "🟢 Baixa"

    grupo["Prioridade"]          = grupo.apply(_nivel, axis=1)
    grupo["% internação"]        = grupo["pct_internado_entre_atendidos"].apply(fmt_pct)
    grupo["% comorbidade"]       = grupo["pct_alguma_comorbidade"].apply(fmt_pct)
    grupo["% busca atendimento"] = grupo["pct_buscou_atendimento"].apply(fmt_pct)
    grupo = grupo.rename(columns={"faixa_etaria":"Faixa etária"})

    st.dataframe(
        grupo[["Faixa etária","% comorbidade","% internação","% busca atendimento","Prioridade"]],
        use_container_width=True, hide_index=True,
    )

    fig = px.bar(
        grupo.dropna(subset=["pct_internado_entre_atendidos","pct_alguma_comorbidade"]),
        x="Faixa etária",
        y=["pct_internado_entre_atendidos","pct_alguma_comorbidade"],
        barmode="group",
        title="Internação e comorbidade por faixa etária — régua de priorização",
        labels={"value":"Percentual (%)","variable":"Indicador"},
    )
    fig.for_each_trace(lambda t: t.update(name=nome_lab(t.name)))
    _layout_fig(fig, ytitle="Percentual (%)")
    st.plotly_chart(fig, use_container_width=True)

    chamada("cuidado",
            "A prioridade não deve ser definida só pela idade ou só pela comorbidade. O risco aumenta quando "
            "esses fatores aparecem juntos: idade avançada, presença de doenças pré-existentes e maior chance "
            "de internação.")
    chamada("insight",
            "O grupo 60+ concentra o maior percentual de comorbidades e também a maior taxa de internação "
            "entre atendidos. Isso mostra que esse público precisa ser identificado antes da chegada ao "
            "hospital, não apenas no momento da emergência.")
    chamada("acao",
            "Criar uma régua simples de prioridade para a triagem: pacientes mais velhos e com comorbidades "
            "devem ter fluxo rápido de avaliação, orientação e encaminhamento. Isso ajuda a reduzir demora "
            "no atendimento e torna a resposta do hospital mais organizada em um novo surto.")


def pagina_plano_acao():
    cabecalho("O que o hospital deve fazer?",
              "Matriz decisória — sinal observado, risco hospitalar, ação, área e urgência.")

    if mes_global != "Todos":
        st.info("Este plano é baseado na análise completa da série. O filtro de mês não se aplica aqui.", icon="ℹ️")

    # Matriz decisória principal
    matriz = pd.DataFrame([
        ["Idoso 60+ com sintomas",
         "Maior chance de agravamento e necessidade de leito",
         "Encaminhar para fluxo prioritário 60+",
         "Triagem / Internação",
         "Imediata"],
        ["Aumento na procura por atendimento",
         "Pressão crescente na porta de entrada",
         "Reforçar triagem, equipe e fluxo de atendimento",
         "Pronto-atendimento",
         "Alta"],
        ["Paciente sem plano e sintomático",
         "Pode chegar mais tarde ao cuidado",
         "Criar rota rápida com triagem social e clínica",
         "Recepção + Assistência social",
         "Alta"],
        ["Hipertenso ou diabético com sintomas",
         "Maior risco de complicação",
         "Priorizar atendimento e acompanhar evolução",
         "Clínica médica / ESF",
         "Alta"],
        ["Aumento de casos confirmados nos testes",
         "Possível crescimento de internações nas próximas semanas",
         "Revisar fluxo de triagem e preparar expansão de leitos",
         "Gestão hospitalar",
         "Alta"],
        ["Estado vulnerável com surto ativo",
         "Maior pressão sobre a rede pública local",
         "Antecipar insumos, teleorientação e leitos de retaguarda",
         "Planejamento regional",
         "Média"],
        ["Trabalhador presencial sintomático",
         "Maior exposição e dificuldade de buscar atendimento",
         "Oferecer canal de atendimento em horário flexível",
         "Comunicação + Pronto-atendimento",
         "Média"],
        ["Queda na testagem com sintomas estáveis",
         "Risco de casos não identificados",
         "Ampliar acesso à testagem e monitorar demanda",
         "Vigilância em saúde",
         "Média"],
    ], columns=["Sinal observado","Risco hospitalar","Ação","Área responsável","Urgência"])

    URG_BADGE = {
        "Imediata": ("background:#FEE2E2;color:#991B1B", "Imediata"),
        "Alta":     ("background:#FEF3C7;color:#92400E", "Alta"),
        "Média":    ("background:#ECFDF5;color:#065F46", "Média"),
    }
    th = ("style='padding:.55rem .75rem;text-align:left;font-size:.78rem;font-weight:600;"
          "color:#5F6B7A;text-transform:uppercase;letter-spacing:.04em;"
          "border-bottom:2px solid #DDE6F0;background:#F6F8FB;'")
    td_base = "style='padding:.6rem .75rem;font-size:.83rem;color:#172033;border-bottom:1px solid #EDF1F7;vertical-align:top;'"
    rows_html = ""
    for _, r in matriz.iterrows():
        badge_css, badge_lbl = URG_BADGE.get(r["Urgência"], ("background:#E5E7EB;color:#374151", r["Urgência"]))
        rows_html += (
            f"<tr>"
            f"<td {td_base} style='padding:.6rem .75rem;font-size:.83rem;color:#172033;"
            f"border-bottom:1px solid #EDF1F7;vertical-align:top;font-weight:600;width:18%;'>{r['Sinal observado']}</td>"
            f"<td {td_base} style='padding:.6rem .75rem;font-size:.83rem;color:#172033;"
            f"border-bottom:1px solid #EDF1F7;vertical-align:top;width:22%;'>{r['Risco hospitalar']}</td>"
            f"<td {td_base} style='padding:.6rem .75rem;font-size:.83rem;color:#172033;"
            f"border-bottom:1px solid #EDF1F7;vertical-align:top;width:28%;'>{r['Ação']}</td>"
            f"<td {td_base} style='padding:.6rem .75rem;font-size:.83rem;color:#172033;"
            f"border-bottom:1px solid #EDF1F7;vertical-align:top;width:20%;'>{r['Área responsável']}</td>"
            f"<td style='padding:.6rem .75rem;vertical-align:top;border-bottom:1px solid #EDF1F7;width:12%;'>"
            f"<span style='{badge_css};padding:3px 10px;border-radius:5px;font-size:.78rem;"
            f"font-weight:700;white-space:nowrap;'>{badge_lbl}</span></td>"
            f"</tr>"
        )
    st.markdown(f"""
    <div style='overflow-x:auto;'>
    <table style='width:100%;border-collapse:collapse;border:1px solid #DDE6F0;border-radius:8px;overflow:hidden;'>
      <thead><tr>
        <th {th}>Sinal observado</th>
        <th {th}>Risco hospitalar</th>
        <th {th}>Ação</th>
        <th {th}>Área responsável</th>
        <th {th}>Urgência</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table></div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Decisões detalhadas")

    decisoes = [
        ("1. Triagem precoce por combinação",          "#1F4E79",
         "Pacientes com sintomas leves, idade avançada e comorbidades devem entrar em fluxo prioritário. "
         "O hospital não deve esperar falta de ar para agir."),
        ("2. Linha de cuidado para 60+",               "#2E75B6",
         "Pessoas com 60 anos ou mais têm maior risco de internação. O hospital deve usar telemonitoramento, "
         "orientação familiar, testagem antecipada e encaminhamento rápido."),
        ("3. Busca ativa de hipertensos e diabéticos", "#1A7A4A",
         "Hipertensão e diabetes são as comorbidades mais frequentes. O hospital pode usar cadastros "
         "existentes para orientar e priorizar esses pacientes durante surtos."),
        ("4. Rota rápida para quem não tem plano",     "#7C3AED",
         "Pacientes sem plano podem ter mais dificuldade de chegar cedo ao atendimento. A triagem social "
         "deve ajudar a identificar esse grupo e acelerar o encaminhamento."),
        ("5. Integração UBS → UPA → Hospital",         "#D85A30",
         "A porta pública concentra maior gravidade. UBS, UPA e hospital precisam atuar com fluxo claro "
         "para evitar atraso e sobrecarga na emergência. Quando o encaminhamento falha, o paciente chega "
         "mais tarde e pressiona a emergência."),
        ("6. Antecipação regional em áreas vulneráveis","#B45309",
         "Estados com maior dependência do SUS precisam de planejamento antecipado: insumos, "
         "teleorientação, equipe e leitos antes do pico de demanda."),
        ("7. Parceria entre saúde e assistência social","#0F766E",
         "Benefícios sociais ajudam a identificar famílias vulneráveis. Em um novo surto, esses cadastros "
         "podem apoiar orientação ativa e encaminhamento rápido."),
        ("8. Painel de alerta com gatilhos definidos", "#475569",
         "O hospital deve acompanhar procura por atendimento, casos confirmados, internações e casos graves. "
         "Quando esses sinais começarem a subir, equipe, leitos e insumos devem ser reforçados antes da "
         "sobrecarga."),
    ]

    for titulo, cor, descricao in decisoes:
        st.markdown(f"""
        <div style='border-left:5px solid {cor}; padding:.75rem 1rem; margin:.4rem 0;
                    background:#FAFCFF; border-radius:6px;'>
            <strong style='color:{cor}'>{titulo}</strong><br>
            <span style='color:#172033; font-size:.93rem;'>{descricao}</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    with st.expander("Notas metodológicas", expanded=False):
        notas = pd.DataFrame([
            ["Internação entre atendidos",
             "Proporção de internações entre quem buscou atendimento — não taxa populacional geral."],
            ["Locais de atendimento",
             "Respostas múltiplas possíveis; não somam 100% nem devem ser agregados."],
            ["Correlações sociais",
             "Todas fracas (|r| < 0,04) — descrevem contexto de acesso, não causalidade clínica."],
            ["Proteção domiciliar",
             "Sem relação clara com internação nos dados; apresentada como contexto."],
            ["Percentual de testes positivos",
             "Calculado entre resultados válidos, não sobre toda a população testada."],
            ["Índice composto de vulnerabilidade",
             "Exploratório — média normalizada de sem plano, baixa renda e informalidade. Não causal."],
        ], columns=["Critério","Nota metodológica"])
        st.dataframe(notas, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR E ROTEAMENTO
# ═══════════════════════════════════════════════════════════════════════════════

dados = carregar_todos()
meses = coletar_meses(dados)

PAGINAS = {
    "Apresentação":                                  pagina_apresentacao,
    "Capa executiva":                                pagina_capa,
    "1. Quem é a população analisada?":              pagina_visao_geral,
    "2. Quais sinais acendem alerta cedo?":          pagina_sintomas,
    "3. Quem teve maior risco de internação?":       pagina_idade_agravamento,
    "4. Quais doenças exigem atenção?":              pagina_comorbidades,
    "5. A renda influenciou o acesso?":              pagina_renda_acesso,
    "6. Onde a pressão aparece primeiro?":           pagina_sus_privado,
    "7. Onde estão os territórios vulneráveis?":     pagina_territorios,
    "8. Quem teve menos capacidade de se proteger?": pagina_trabalho,
    "9. Proteção domiciliar (contexto)":             pagina_protecao_domiciliar,
    "10. Benefícios identificam vulnerabilidade?":   pagina_protecao_social,
    "11. Escolaridade, gênero e comunicação":        pagina_escolaridade_genero,
    "12. O risco é clínico ou também social?":       pagina_correlacoes,
    "13. Painel de alerta mensal":                   pagina_alerta_mensal,
    "14. Quem deve ter prioridade na triagem?":      pagina_risco_combinado,
    "15. Plano de ação":                             pagina_plano_acao,
}

if "pagina_anterior" not in st.session_state:
    st.session_state.pagina_anterior = None
if "mes_selector" not in st.session_state:
    st.session_state.mes_selector = "Todos"

st.sidebar.markdown("## PNAD COVID-19")
st.sidebar.caption("Painel hospitalar · Fase 3")
st.sidebar.divider()

pagina_sel_sidebar = st.sidebar.radio(
    "Navegação",
    list(PAGINAS.keys()),
    key="pagina_sel_sidebar",
)

# Detectar mudança de página para resetar mês
_cur_page = st.session_state.get("pagina_sel_sidebar", list(PAGINAS.keys())[0])
if st.session_state.get("pagina_anterior") != _cur_page:
    st.session_state["mes_selector"] = "Todos"
    st.session_state["pagina_anterior"] = _cur_page

st.sidebar.divider()
mes_global = st.sidebar.selectbox(
    "Mês de análise", ["Todos"] + meses,
    key="mes_selector",
    help="Filtra dados mensais. 'Todos' mostra a média dos meses.",
)
st.sidebar.toggle("Modo escuro", key="dark_mode", value=False)
st.sidebar.caption("No celular, use o menu nativo do Streamlit para abrir e fechar a navegação.")

_aplicar_css()

PAGINAS[pagina_sel_sidebar]()
