import pandas as pd
from dash import html
import dash_bootstrap_components as dbc
from loguru import logger
from utils.get_translations import get_translations


def display_results_table(df: pd.DataFrame, lang: str = "pt") -> html.Div:
    """
    Prepara e retorna uma tabela formatada de resultados de ET₀ para exibição no Dash.

    Parâmetros:
    - df: DataFrame com os resultados do cálculo de ET₀.
    - lang: Idioma para tradução das colunas ('pt' ou 'en').

    Retorna:
    - html.Div contendo a tabela formatada com dbc.Table.
    """
    try:
        # Validar DataFrame
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou None fornecido para display_results_table")
            return html.Div("Nenhum dado disponível para exibição")

        # Criar uma cópia do DataFrame
        df_display = df.copy()

        # Colunas esperadas
        expected_columns = [
            "date",
            "T2M_MAX",
            "T2M_MIN",
            "RH2M",
            "WS2M",
            "ALLSKY_SFC_SW_DWN",
            "PRECTOTCORR",
            "ETo"
        ]

        # Verificar colunas
        missing_columns = [col for col in expected_columns if col not in df_display.columns]
        if missing_columns:
            logger.error(f"Colunas ausentes no DataFrame: {missing_columns}")
            raise ValueError(f"Colunas ausentes no DataFrame: {missing_columns}")

        # Selecionar colunas relevantes
        df_display = df_display[expected_columns]

        # Obter traduções
        t = get_translations(lang)
        column_names = {
            "date": t["date"],
            "T2M_MAX": t["temp_max"],
            "T2M_MIN": t["temp_min"],
            "RH2M": t["humidity"],
            "WS2M": t["wind_speed"],
            "ALLSKY_SFC_SW_DWN": t["radiation"],
            "PRECTOTCORR": t["precipitation"],
            "ETo": t["eto"]
        }

        # Renomear colunas
        df_display = df_display.rename(columns=column_names)

        # Formatar a coluna de data
        df_display["date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")

        # Arredondar valores numéricos
        numeric_cols = df_display.columns[1:]  # Exclui "date"
        df_display[numeric_cols] = df_display[numeric_cols].round(2)

        # Criar tabela com Dash Bootstrap
        table = dbc.Table.from_dataframe(
            df_display,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="table table-sm"
        )

        logger.info("Tabela de resultados formatada com sucesso")
        return html.Div([table])

    except Exception as e:
        logger.error(f"Erro ao formatar tabela de resultados: {str(e)}")
        return html.Div(f"Erro ao exibir tabela: {str(e)}")