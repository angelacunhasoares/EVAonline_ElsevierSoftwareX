import numpy as np
import pandas as pd
import plotly.express as px
from dash import html, dcc
import dash_bootstrap_components as dbc
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from src.results_tables import display_results_table
from loguru import logger
from utils.get_translations import get_translations


def display_daily_data(df: pd.DataFrame, lang: str = "pt") -> html.Div:
    """
    Exibe os dados climáticos diários em uma tabela formatada.

    Parâmetros:
    - df: DataFrame com os dados (espera colunas 'date', 'T2M_MAX', 'T2M_MIN', 'RH2M', 'WS2M', 'ALLSKY_SFC_SW_DWN', 'PRECTOTCORR', 'ETo').
    - lang: Idioma para traduções ('pt' ou 'en').

    Retorna:
    - html.Div contendo a tabela formatada.
    """
    try:
        return display_results_table(df, lang=lang)
    except Exception as e:
        logger.error(f"Erro ao exibir dados diários: {str(e)}")
        return html.Div(f"{get_translations(lang)['error']}: {str(e)}")


def display_descriptive_stats(df: pd.DataFrame, lang: str = "pt") -> html.Div:
    """
    Exibe estatísticas descritivas para as variáveis numéricas.

    Parâmetros:
    - df: DataFrame com os dados.
    - lang: Idioma para traduções ('pt' ou 'en').

    Retorna:
    - html.Div contendo a tabela de estatísticas.
    """
    try:
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou None fornecido para display_descriptive_stats")
            return html.Div(get_translations(lang)["no_data"])

        t = get_translations(lang)
        expected_columns = ["T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "ETo"]
        numeric_cols = [col for col in expected_columns if col in df.columns]
        if not numeric_cols:
            logger.error("Nenhuma coluna numérica válida encontrada")
            raise ValueError("Nenhuma coluna numérica válida encontrada")

        stats_data = {
            t["mean"]: df[numeric_cols].mean().round(2),
            t["max"]: df[numeric_cols].max().round(2),
            t["min"]: df[numeric_cols].min().round(2),
            t["median"]: df[numeric_cols].median().round(2),
            t["std_dev"]: df[numeric_cols].std().round(2),
            t["percentile_25"]: df[numeric_cols].quantile(0.25).round(2),
            t["percentile_75"]: df[numeric_cols].quantile(0.75).round(2),
            t["coef_variation"]: ((df[numeric_cols].std() / df[numeric_cols].mean()) * 100).round(2),
            t["skewness"]: df[numeric_cols].apply(lambda x: stats.skew(x.dropna())).round(2),
            t["kurtosis"]: df[numeric_cols].apply(lambda x: stats.kurtosis(x.dropna())).round(2),
        }
        stats_df = pd.DataFrame(stats_data).T
        stats_df.insert(0, t["statistic"], stats_df.index)

        # Renomear colunas com traduções
        translated_columns = {col: t.get(col.lower(), col) for col in stats_df.columns[1:]}
        stats_df = stats_df.rename(columns=translated_columns)

        table = dbc.Table.from_dataframe(
            stats_df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="table table-sm"
        )
        logger.info("Tabela de estatísticas descritivas gerada com sucesso")
        return html.Div([html.H5(t["descriptive_stats"]), table])

    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas descritivas: {str(e)}")
        return html.Div(f"{t['error']}: {str(e)}")


def display_normality_test(df: pd.DataFrame, lang: str = "pt") -> html.Div:
    """
    Exibe o teste de normalidade Shapiro-Wilk.

    Parâmetros:
    - df: DataFrame com os dados.
    - lang: Idioma para traduções ('pt' ou 'en').

    Retorna:
    - html.Div com a tabela e nota explicativa.
    """
    try:
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou None fornecido para display_normality_test")
            return html.Div(get_translations(lang)["no_data"])

        t = get_translations(lang)
        expected_columns = ["T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "ETo"]
        numeric_cols = [col for col in expected_columns if col in df.columns]
        if not numeric_cols:
            logger.error("Nenhuma coluna numérica válida encontrada")
            raise ValueError("Nenhuma coluna numérica válida encontrada")

        normality_tests = {}
        for col in numeric_cols:
            stat, p_value = stats.shapiro(df[col].dropna())
            normality_tests[t.get(col.lower(), col)] = {
                t["statistic"]: stat.round(2),
                t["p_value"]: p_value.round(4),
            }
        normality_df = pd.DataFrame(normality_tests).T
        normality_df.insert(0, t["variable"], normality_df.index)

        table = dbc.Table.from_dataframe(
            normality_df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="table table-sm"
        )
        logger.info("Tabela de teste de normalidade gerada com sucesso")
        return html.Div([
            html.H5(t["normality_test"]),
            table,
            html.P(t["normality_note"])
        ])

    except Exception as e:
        logger.error(f"Erro ao gerar teste de normalidade: {str(e)}")
        return html.Div(f"{t['error']}: {str(e)}")


def display_correlation_matrix(df: pd.DataFrame, lang: str = "pt") -> html.Div:
    """
    Exibe a matriz de correlação entre as variáveis.

    Parâmetros:
    - df: DataFrame com os dados.
    - lang: Idioma para traduções ('pt' ou 'en').

    Retorna:
    - html.Div com a tabela de correlação.
    """
    try:
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou None fornecido para display_correlation_matrix")
            return html.Div(get_translations(lang)["no_data"])

        t = get_translations(lang)
        expected_columns = ["T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "ETo"]
        numeric_cols = [col for col in expected_columns if col in df.columns]
        if not numeric_cols:
            logger.error("Nenhuma coluna numérica válida encontrada")
            raise ValueError("Nenhuma coluna numérica válida encontrada")

        corr_df = df[numeric_cols].corr().round(2)
        corr_df = corr_df.rename(columns=lambda x: t.get(x.lower(), x), index=lambda x: t.get(x.lower(), x))

        table = dbc.Table.from_dataframe(
            corr_df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="table table-sm"
        )
        logger.info("Matriz de correlação gerada com sucesso")
        return html.Div([html.H5(t["correlation_matrix"]), table])

    except Exception as e:
        logger.error(f"Erro ao gerar matriz de correlação: {str(e)}")
        return html.Div(f"{t['error']}: {str(e)}")


def display_eto_summary(df: pd.DataFrame, lang: str = "pt") -> html.Div:
    """
    Exibe soma total de ETo, déficit hídrico diário, estatísticas e gráficos.

    Parâmetros:
    - df: DataFrame com os dados (espera colunas 'date', 'PRECTOTCORR', 'ETo').
    - lang: Idioma para traduções ('pt' ou 'en').

    Retorna:
    - html.Div com tabelas, estatísticas e gráficos.
    """
    try:
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou None fornecido para display_eto_summary")
            return html.Div(get_translations(lang)["no_data"])

        t = get_translations(lang)
        expected_columns = ["date", "PRECTOTCORR", "ETo"]
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Colunas ausentes no DataFrame: {missing_columns}")
            raise ValueError(f"Colunas ausentes no DataFrame: {missing_columns}")

        df_display = df[["date", "PRECTOTCORR", "ETo"]].copy()
        df_display["date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")
        df_display = df_display.round(2)
        df_display[t["water_deficit"]] = (df_display["PRECTOTCORR"] - df_display["ETo"]).round(2)

        et0_sum = df_display["ETo"].sum().round(2)
        deficit_mean = df_display[t["water_deficit"]].mean().round(2)
        deficit_total = df_display[t["water_deficit"]].sum().round(2)
        days_with_deficit = len(df_display[df_display[t["water_deficit"]] < 0])
        days_with_excess = len(df_display[df_display[t["water_deficit"]] > 0])

        table = dbc.Table.from_dataframe(
            df_display.rename(columns={"date": t["date"], "PRECTOTCORR": t["precipitation"], "ETo": t["eto"]}),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="table table-sm"
        )

        # Gráficos de déficit e balanço hídrico
        df_display["Deficiência"] = df_display[t["water_deficit"]].apply(lambda x: min(0, x) if x < 0 else 0)
        df_display["Excedente"] = df_display[t["water_deficit"]].apply(lambda x: max(0, x) if x > 0 else 0)
        df_display[t["cumulative_balance"]] = df_display[t["water_deficit"]].cumsum()
        df_display["Deficiência Acumulada"] = df_display[t["cumulative_balance"]].apply(lambda x: min(0, x) if x < 0 else 0)
        df_display["Excedente Acumulado"] = df_display[t["cumulative_balance"]].apply(lambda x: max(0, x) if x > 0 else 0)

        fig_deficit = px.area(
            df_display,
            x="date",
            y=["Deficiência", "Excedente"],
            title=t["water_deficit"],
            labels={"value": t["water_deficit"], "variable": t["component"]},
            color_discrete_map={"Deficiência": "red", "Excedente": "#005B99"},
        )
        fig_deficit.update_traces(
            hovertemplate=f"{t['date']}: %{{x}}<br>{t['value']}: %{{y}} mm/dia<br>{t['component']}: %{{customdata}}"
        )
        fig_deficit.update_layout(
            yaxis_title=t["water_deficit"],
            legend_title=t["legend"],
            template="plotly_white",
            margin=dict(b=100)
        )

        fig_balance = px.area(
            df_display,
            x="date",
            y=["Deficiência Acumulada", "Excedente Acumulado"],
            title=t["cumulative_balance"],
            labels={"value": t["cumulative_balance"], "variable": t["component"]},
            color_discrete_map={"Deficiência Acumulada": "red", "Excedente Acumulado": "#005B99"},
        )
        fig_balance.update_traces(
            hovertemplate=f"{t['date']}: %{{x}}<br>{t['value']}: %{{y}} mm/dia<br>{t['component']}: %{{customdata}}"
        )
        fig_balance.update_layout(
            yaxis_title=t["cumulative_balance"],
            legend_title=t["legend"],
            template="plotly_white",
            margin=dict(b=100)
        )

        logger.info("Resumo de ETo e gráficos gerados com sucesso")
        return html.Div([
            html.H5(t["eto_summary"]),
            html.P(f"{t['total_eto']}: {et0_sum} mm/dia"),
            html.H6(t["water_deficit"]),
            table,
            html.P(f"{t['mean_deficit']}: {deficit_mean} mm/dia"),
            html.P(f"{t['total_deficit']}: {deficit_total} mm/dia"),
            html.P(f"{t['deficit_negative']}: {days_with_deficit} {t['days']}"),
            html.P(f"{t['deficit_positive']}: {days_with_excess} {t['days']}"),
            dcc.Checklist(
                id="deficit-chart-checklist",
                options=[{"label": t["show_deficit_chart"], "value": "show_deficit"}],
                value=[],
                style={"margin": "10px"}
            ),
            html.Div(id="deficit-chart-output"),
            dcc.Checklist(
                id="balance-chart-checklist",
                options=[{"label": t["show_balance_chart"], "value": "show_balance"}],
                value=[],
                style={"margin": "10px"}
            ),
            html.Div(id="balance-chart-output"),
            dcc.Graph(id="deficit-chart", figure=fig_deficit, style={"display": "none"}),
            dcc.Graph(id="balance-chart", figure=fig_balance, style={"display": "none"}),
            html.P(t["deficit_note"])
        ])

    except Exception as e:
        logger.error(f"Erro ao gerar resumo de ETo: {str(e)}")
        return html.Div(f"{t['error']}: {str(e)}")


def display_trend_analysis(df: pd.DataFrame, lang: str = "pt") -> html.Div:
    """
    Exibe a tendência temporal da ETo.

    Parâmetros:
    - df: DataFrame com os dados (espera colunas 'date', 'ETo').
    - lang: Idioma para traduções ('pt' ou 'en').

    Retorna:
    - html.Div com a tendência.
    """
    try:
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou None fornecido para display_trend_analysis")
            return html.Div(get_translations(lang)["no_data"])

        t = get_translations(lang)
        if "date" not in df.columns or "ETo" not in df.columns:
            logger.error("Colunas 'date' ou 'ETo' ausentes no DataFrame")
            raise ValueError("Colunas 'date' ou 'ETo' ausentes no DataFrame")

        dates_numeric = pd.to_numeric(pd.to_datetime(df["date"]).map(lambda x: x.toordinal()))
        slope, intercept = np.polyfit(dates_numeric, df["ETo"], 1)
        logger.info("Análise de tendência gerada com sucesso")
        return html.Div([
            html.H5(t["trend_analysis"]),
            html.P(f"{t['eto_trend']}: {slope.round(4)} mm/dia {t['per_day']}")
        ])

    except Exception as e:
        logger.error(f"Erro ao gerar análise de tendência: {str(e)}")
        return html.Div(f"{t['error']}: {str(e)}")


def display_seasonality_test(df: pd.DataFrame, lang: str = "pt") -> html.Div:
    """
    Exibe o teste de estacionalidade (ADF) para ETo.

    Parâmetros:
    - df: DataFrame com os dados (espera coluna 'ETo').
    - lang: Idioma para traduções ('pt' ou 'en').

    Retorna:
    - html.Div com o resultado do teste.
    """
    try:
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou None fornecido para display_seasonality_test")
            return html.Div(get_translations(lang)["no_data"])

        t = get_translations(lang)
        if "ETo" not in df.columns:
            logger.error("Coluna 'ETo' ausente no DataFrame")
            raise ValueError("Coluna 'ETo' ausente no DataFrame")

        result = adfuller(df["ETo"].dropna())
        p_value = float(result[1])
        logger.info(f"Teste de estacionalidade (ADF) gerado com sucesso: p-valor = {p_value:.4f}")
        return html.Div([
            html.H5(t["seasonality_test"]),
            html.P(f"{t['adf_test']}: p-valor = {p_value:.4f}")
        ])

    except Exception as e:
        logger.error(f"Erro ao gerar teste de estacionalidade: {str(e)}")
        return html.Div(f"{t['error']}: {str(e)}")


def display_cumulative_distribution(df: pd.DataFrame, lang: str = "pt") -> html.Div:
    """
    Exibe a distribuição acumulada de ETo e precipitação.

    Parâmetros:
    - df: DataFrame com os dados (espera colunas 'date', 'PRECTOTCORR', 'ETo').
    - lang: Idioma para traduções ('pt' ou 'en').

    Retorna:
    - html.Div com a tabela de distribuição acumulada.
    """
    try:
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou None fornecido para display_cumulative_distribution")
            return html.Div(get_translations(lang)["no_data"])

        t = get_translations(lang)
        expected_columns = ["date", "PRECTOTCORR", "ETo"]
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Colunas ausentes no DataFrame: {missing_columns}")
            raise ValueError(f"Colunas ausentes no DataFrame: {missing_columns}")

        df_display = df[["date", "PRECTOTCORR", "ETo"]].copy()
        df_display["date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")
        df_display[t["cumulative_eto"]] = df_display["ETo"].cumsum().round(2)
        df_display[t["cumulative_precipitation"]] = df_display["PRECTOTCORR"].cumsum().round(2)

        table = dbc.Table.from_dataframe(
            df_display.rename(columns={"date": t["date"], "PRECTOTCORR": t["precipitation"], "ETo": t["eto"]}),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="table table-sm"
        )
        logger.info("Tabela de distribuição acumulada gerada com sucesso")
        return html.Div([html.H5(t["cumulative_distribution"]), table])

    except Exception as e:
        logger.error(f"Erro ao gerar distribuição acumulada: {str(e)}")
        return html.Div(f"{t['error']}: {str(e)}")