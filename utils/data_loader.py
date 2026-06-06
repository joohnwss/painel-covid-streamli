import csv
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent.parent
SEARCH_DIRS = ["dados_dashboard", "data", "dados", "dataset"]

TABELAS = {
    "kpis":               "descritiva_kpis",
    "perfil_populacao":   "descritiva_perfil_populacao",
    "sintomas":           "descritiva_sintomas",
    "faixa_etaria":       "descritiva_faixa_etaria",
    "comorbidades":       "descritiva_comorbidades",
    "itens_protecao":     "descritiva_itens_protecao",
    "barreira":           "analise_01_barreira_economica",
    "informalidade":      "analise_02_informalidade_risco",
    "perfil_grave":       "analise_03_perfil_grave",
    "protecao_social":    "analise_04_protecao_social",
    "mapa_desigualdade":  "analise_05_mapa_desigualdade",
    "evolucao":           "analise_06_evolucao_mensal",
    "escolaridade_genero":"analise_07_escolaridade_genero",
    "moradia":            "analise_08_moradia_endividamento",
    "sus_privado":        "analise_09_sus_privado",
    "correlacoes":        "correlacoes_economico_clinico",
}


def _detectar_sep(path: Path) -> str:
    try:
        sample = path.read_text(encoding="utf-8-sig", errors="ignore")[:4096]
        return csv.Sniffer().sniff(sample, delimiters=",;|\t").delimiter
    except Exception:
        return ","


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().replace(
            {"": np.nan, "nan": np.nan, "None": np.nan}
        )
    numeric_hints = {
        "n_amostra", "qtd_respostas_sim", "qtd_tem_item",
        "pop_estimada_com_sintoma", "pop_estimada_com_comorbidade",
        "pop_estimada_tem_item", "populacao_estimada",
        "media_itens_protecao", "correlacao", "idade_media",
    }
    for col in df.columns:
        if col.startswith("pct_") or col in numeric_hints:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_table(nome: str) -> pd.DataFrame:
    filename = TABELAS.get(nome, nome)
    for folder in SEARCH_DIRS:
        for ext in (".csv", ".parquet"):
            path = BASE_DIR / folder / (filename + ext)
            if path.exists():
                try:
                    if ext == ".parquet":
                        return _normalizar(pd.read_parquet(path))
                    sep = _detectar_sep(path)
                    for enc in ("utf-8-sig", "utf-8", "latin1"):
                        try:
                            df = pd.read_csv(path, sep=sep, encoding=enc)
                            return _normalizar(df)
                        except Exception:
                            continue
                except Exception:
                    continue
    return pd.DataFrame()
