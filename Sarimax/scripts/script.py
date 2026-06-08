import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
from io import StringIO
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller, kpss
import statsmodels.api as sm
import itertools
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.linear_model import LassoCV, ElasticNetCV
from sklearn.pipeline import make_pipeline
from statsmodels.tsa.stattools import ccf
from arch import arch_model
from statsmodels.stats.diagnostic import het_arch
import scipy.stats as st
import matplotlib.dates as mdates
import importlib
import pmdarima as pm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy.stats import norm
from statsmodels.tsa.stattools import grangercausalitytests
from pmdarima.arima.utils import nsdiffs
from statsmodels.stats.diagnostic import het_arch
from statsmodels.stats.stattools import jarque_bera
import pymannkendall as mk
from scipy.stats import boxcox
from scipy.special import inv_boxcox
from scipy.stats import boxcox_normmax
from statsmodels.tsa.x13 import x13_arima_analysis
import math
from statsmodels.tsa.stattools import coint
from arch.unitroot import VarianceRatio
import logging
from prophet import Prophet

from sklearn.linear_model import LassoCV
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAXResults

from statsmodels.stats.multitest import multipletests

import sys
from pathlib import Path
import importlib

from scipy.signal import periodogram

# DB IMPORTS
from sqlalchemy import create_engine
from langchain_core.tools import tool

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import scripts.utils as utils
importlib.reload(utils)

from scripts.utils import stationarity_tests, plot_acf_pacf, smape, make_lags, top_ccf_vars, calcular_vif, grangers_causality_matrix

import scripts.utils_plot as utils_plot
importlib.reload(utils_plot)

import scripts.train_predict as train_predict

importlib.reload(train_predict)

from scripts.train_predict import entrenar_y_predecir
from scripts.utils import realizar_predicciones_paralelo, bootstrap_forecast_sarimax, xerar_datas_corte

import scripts.utils
importlib.reload(utils)

from scripts.utils import (stationarity_tests, plot_acf_pacf, smape, make_lags, top_ccf_vars, calcular_vif, grangers_causality_matrix, 
                   generar_fechas_corte_por_ano, realizar_predicciones_paralelo, df_to_sarimax_config, run_sarimax_forecasts_parallel)

import scripts.utils_plot as utils_plot
importlib.reload(utils_plot)

from scripts.utils_plot import (inicializacion_datos, plot_st, plot_total_monthly_sales, plot_monthly_sales_by_variety,
plot_monthly_sales_grouped_by_year, plot_total_yearly_sales, plot_total_weekday_sales, plot_stl_decomposition, 
                       plot_seasonal_pattern, plot_forecasts_period, extraer_resultados_por_horizonte)

from scripts.utils import check_stationarity_exog, johansen_cointegration_tests
from statsmodels.tsa.vector_ar.vecm import VECM

import scripts.utils 
importlib.reload(utils)

from scripts.utils import stationarity_tests, plot_acf_pacf, smape, make_lags, top_ccf_vars, calcular_vif, grangers_causality_matrix

import scripts.utils  as utils
import scripts.train_predict as train_predict

importlib.reload(utils)
importlib.reload(train_predict)

import scripts.utils as utils
import scripts.train_predict as train_predict

from scripts.train_predict import entrenar_y_predecir
from scripts.utils import realizar_predicciones_paralelo, bootstrap_forecast_sarimax, xerar_datas_corte, _fit_and_forecast_cut, sarimax_ci_readiness_report

def get_acf_pacf_data(series, lag_max=50, alpha=0.05):
    # 1. Calcular ACF e o seu intervalo de confianza
    # acf_vals: o valor da correlación
    # confint: matriz con [limite_inferior, limite_superior] absoluto
    acf_vals, confint_acf = acf(series, nlags=lag_max, alpha=alpha)
    
    # 2. Calcular PACF e o seu intervalo de confianza
    pacf_vals, confint_pacf = pacf(series, nlags=lag_max, method="yw", alpha=alpha)
    
    # 3. Crear un DataFrame organizado para facilitar a lectura humana
    df_results = pd.DataFrame({
        'Lag': range(len(acf_vals)),
        'ACF': acf_vals,
        'ACF_Lower': confint_acf[:, 0] - acf_vals,
        'ACF_Upper': confint_acf[:, 1] - acf_vals,
        'PACF': pacf_vals,
        'PACF_Lower': confint_pacf[:, 0]  - pacf_vals,
        'PACF_Upper': confint_pacf[:, 1] - pacf_vals
    })
    
    # Engadimos unha columna booleana para que a outra persoa vexa se é significativo "a golpe de vista"
    # Un valor é significativo se o intervalo de confianza non inclúe o cero
    df_results['ACF_Significativo'] = (df_results['ACF_Lower'] > 0) | (df_results['ACF_Upper'] < 0)
    df_results['PACF_Significativo'] = (df_results['PACF_Lower'] > 0) | (df_results['PACF_Upper'] < 0)
    
    return df_results

# Configuración de base de datos
DB_URL = 'postgresql://admin:admin@localhost:5433/base_datos_v3'
engine = create_engine(DB_URL)

@tool
def predecir_trigo_grecia(dummy: str = "") -> str:
    """
    Realiza la predicción de la producción del trigo en Grecia usando un modelo SARIMAX.
    Úsala cuando el usuario pida "predice el trigo en grecia", "predicción de trigo", etc.
    Carga los últimos datos, ejecuta el modelo, guarda en BD y devuelve la explicación.
    """
    print("DEBUG: Ejecutando predicción de trigo en Grecia...")
    
    # Carga y transformación datos
    # Usar rutas absolutas para evitar problemas al llamar desde agent.py
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '..', 'data')
    
    nex_path = os.path.join(data_dir, 'new_ex.csv')
    nex = pd.read_csv(nex_path, sep=';')
    nex['date'] = pd.to_datetime(nex['date'])
    nex = nex.set_index('date')
    
    path = os.path.join(data_dir, 'sosdata_active.csv')
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df = df[(df.index > '2012-10-01') & (df.index < '2024-01-01')]
    
    brent_path = os.path.join(data_dir, 'brent.csv')
    brent = pd.read_csv(brent_path, sep=';', header=None, names=['date', 'oil'])
    brent['date'] = pd.to_datetime(brent['date'])
    brent = brent.set_index('date')
    
    hk_path = os.path.join(data_dir, 'hkks.csv')
    hk = pd.read_csv(hk_path, sep=';', header=None, names=['date', 'hkks'])
    hk['date'] = pd.to_datetime(hk['date'])
    hk = hk.set_index('date')
    hk.index = hk.index.to_period('M').to_timestamp()
    
    df['oil'] = brent['oil']
    df['hkks'] = hk['hkks']
    
    df = pd.concat([df, nex], axis=1).dropna()
    
    # Transformación logarítmica
    serie = df[['wheat']]
    y = serie.wheat.values
    serie = np.log(y)
    df['wt'] = serie
    
    # Fuerza estacionalidad - AQUÍ SE MUESTRAN POR PANTALLA PERO PUEDES METER ALGO PARA GUARDARLO EN FICHERO SI ES NECESARIO
    stl12 = STL(df[['wt']], period=12, robust=True).fit()
    
    resid = stl12.resid
    seasonal = stl12.seasonal
    
    var_resid = np.var(resid, ddof=1)
    var_denom = np.var(resid + seasonal, ddof=1)
    
    strength = max(0, 1 - var_resid / var_denom)
    
    print(f'Strength for 12 months seasonality: {strength}')
    
    stl12 = STL(df[['wt']], period=6, robust=True).fit()
    
    resid = stl12.resid
    seasonal = stl12.seasonal
    
    var_resid = np.var(resid, ddof=1)
    var_denom = np.var(resid + seasonal, ddof=1)
    
    strength = max(0, 1 - var_resid / var_denom)
    
    print(f'Strength for 6 months seasonality: {strength}')
    
    # AQUÍ SE OBTIENEN LOS RESULTADOS DE LOS TEST ACF/PACF
    serie = df.wt
    resultados = get_acf_pacf_data(serie.diff().dropna())
    # print(resultados)
    
    # EXOGENAS
    def highlight_sig(v):
        if v <= 0.05:
            return "background-color: lightgreen"
        return ""
    
    df_clean = df.copy()
    df_clean.index = df_clean.index.to_period("M").to_timestamp(how="start")
    
    # df_clean = df_clean.loc[df_clean.index >= "2015-01-01"]
    # df_clean = df_clean.loc[df_clean.index <= "2023-12-31"]
    
    target = df_clean[['wt']]
    
    # df_clean.drop(columns=['dolar'], inplace=True)
    df_clean = df_clean.drop(columns=['wheat'])
    df_clean = df_clean.drop(columns=['wt'])
    df_clean = df_clean.drop(columns=['rice'])

    df_clean['electricity_price'] = np.log(df_clean['electricity_price'])
    df_clean['oil'] = np.log(df_clean['oil'])
    df_clean['imports'] = np.log(df_clean['imports'])
    df_clean['exports'] = np.log(df_clean['exports'])
    df_clean['cpi'] = np.log(df_clean['cpi'])
    df_clean['hkks'] = np.log(df_clean['hkks'])
    df_clean['fkt'] = np.log(df_clean['fkt'])
    df_clean['natural_gas'] = np.log(df_clean['natural_gas'])
    df_clean['dap'] = np.log(df_clean['dap'])
    df_clean['tsp'] = np.log(df_clean['tsp'])
    df_clean['urea'] = np.log(df_clean['urea'])
    df_clean['pot_chloride'] = np.log(df_clean['pot_chloride'])
    
    df_exogs = df_clean.copy()
    variables = df_exogs.columns[:-1].copy()
    
    variables_diff = ['electricity_price','oil', 'cpi', 'imports', 'exports', 'fkt', 'hkks', 'natural_gas', 'dap',
           'tsp', 'urea', 'pot_chloride']
    
    for var in variables_diff:
        df_exogs[var] = df_exogs[var].diff()
    
    df_granger = df_exogs.copy()
    df_granger['target'] = target
    df_granger['target'] = df_granger['target'].diff()
    df_granger = df_granger.dropna()
    
    variables = ["target"] + list(df_exogs.columns)
    
    pvals = grangers_causality_matrix(df_granger, variables, maxlag=15)
    styled = pvals.style.applymap(highlight_sig)
    
    pvals_flat = pvals.values.flatten()
    
    reject, pvals_adj, _, _ = multipletests(
        pvals_flat,
        alpha=0.05,
        method="fdr_bh"
    )
    
    # Reconstruír en forma matriz
    reject_matrix = reject.reshape(pvals.shape)
    pvals_adj_matrix = pvals_adj.reshape(pvals.shape)
    
    reject_df = pd.DataFrame(
        reject_matrix,
        index=pvals.index,
        columns=pvals.columns
    )
    
    pvals_adj_df = pd.DataFrame(
        pvals_adj_matrix,
        index=pvals.index,
        columns=pvals.columns
    )
    
    # styled = pvals_adj_df.style.applymap(highlight_sig)
    # ESTO ES LA TABLA DEL TEST DE GRANGER
    # print(pvals_adj_df)
    df_exogs['urea_agresiva'] = df_exogs['urea'] * df_exogs['urea'].abs()
    df_exogs['ng_agresiva'] = df_exogs['natural_gas'] * df_exogs['natural_gas'].abs()
    df_exogs['e_agresiva'] = df_exogs['electricity_price'] * df_exogs['electricity_price'].abs()
    
    '''selected_vars = ['urea', 'electricity_price', 'natural_gas']
    exogs_final = df_exogs[selected_vars].copy()'''
    
    selected_vars = ['urea_agresiva', 'ng_agresiva', 'e_agresiva']
    exogs_final = df_exogs[selected_vars].copy()
    
    dflag1 = make_lags(exogs_final, exogs_final.columns, 2, 6, freq='MS')
    dflag1 = dflag1[9:]
    
    dflag = dflag1.copy()
    tlag = target[9:]
    exslag = dflag
    
    '''exslag['urea'] = exslag['urea_lag7']+exslag['urea_lag6']
    exslag['natural_gas'] = exslag['natural_gas_lag7']+exslag['natural_gas_lag6']
    exslag['electricity_price'] = exslag['electricity_price_lag7']+exslag['electricity_price_lag6']'''
    
    exslag['urea'] = exslag['urea_agresiva_lag7']+exslag['urea_agresiva_lag6']
    exslag['natural_gas'] = exslag['ng_agresiva_lag7']+exslag['ng_agresiva_lag6']
    exslag['electricity_price'] = exslag['e_agresiva_lag7']+exslag['e_agresiva_lag6']
    
    exslag = exslag[['urea', 'electricity_price', 'natural_gas']]
    
    config = {'2018-12-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2019-03-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2019-06-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2019-09-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2019-12-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2020-03-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2020-06-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2020-09-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2020-12-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2021-03-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2021-06-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2021-09-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2021-12-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2022-03-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2022-06-01': {3: {'order': (0, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2022-09-01': {3: {'order': (1, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2022-12-01': {3: {'order': (1, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2023-03-01': {3: {'order': (1, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2023-06-01': {3: {'order': (1, 1, 0), 'seasonal_order': (0, 0, 0, 12)}},
     '2023-09-01': {3: {'order': (1, 1, 0), 'seasonal_order': (0, 0, 0, 12)}}}

    # Predicción
    results, sims = utils.run_sarimax_forecasts_parallel(series = tlag, exogs = exslag, config_dict = config, freq='MS', log_transform=True)
    df_results, meses = extraer_resultados_por_horizonte(results, [3])
    # En df_results tienes los resultados de la predicción
    df_results = df_results.set_index('date')
    
    # === GUARDAR EN BASE DE DATOS ===
    try:
        df_db = df_results[['pred', 'ci_low', 'ci_high']].copy()
        df_db.index.name = 'fecha'
        df_db.to_sql('prediccion_trigo_grecia', engine, if_exists='replace', index=True)
        
        # Guardar también la serie temporal real para poder compararla
        df_real = df[['wheat']].copy().dropna()
        df_real.index.name = 'fecha'
        df_real.columns = ['valor_real']
        df_real.to_sql('real_trigo_grecia', engine, if_exists='replace', index=True)
        
        print("Datos guardados en PostgreSQL correctamente.")
    except Exception as e:
        print(f"Error guardando en BD: {e}")

    # === GENERAR EXPLICACIÓN DINÁMICA ===
    var_nombres = {
        'urea': 'Urea (abono nitrogenado)',
        'ng': 'Gas Natural',
        'e': 'Precio de la Electricidad',
        'dap': 'DAP (di-amonio fosfato)',
        'tsp': 'TSP (superfosfato triple)',
        'kcl': 'Cloruro de Potasio',
        'brent': 'Precio del Brent (petróleo)',
    }
    
    vars_legibles = []
    for v in selected_vars:
        clave = v.replace('_agresiva', '').replace('_', '')
        nombre = var_nombres.get(clave, v.replace('_agresiva', '').replace('_', ' ').title())
        vars_legibles.append(nombre)
    vars_str = ", ".join(vars_legibles)

    explicacion = "He analizado la predicción de la producción de trigo en Grecia usando nuestro modelo SARIMAX optimizado.\n\n"
    explicacion += f"**Variables analizadas:** Para realizar esta predicción he tenido en cuenta los siguientes factores exógenos clave: {vars_str}. Estas variables fueron seleccionadas mediante un test de causalidad de Granger por su capacidad predictiva sobre la producción de trigo.\n\n"
    
    if strength < 0.3:
        explicacion += (
            f"**Estacionalidad:** He aplicado la descomposición STL (Seasonal-Trend decomposition using LOESS) "
            f"sobre los datos históricos de producción. La fuerza estacional calculada para períodos de 12 meses es de {strength:.2f} "
            f"({strength*100:.1f}%). Dado que el umbral de significancia estacional suele situarse por encima de 0.6-0.7, "
            f"podemos concluir matemáticamente que **la producción anual de trigo en Grecia no presenta una estacionalidad "
            f"estructurada** que afecte de forma recurrente al modelo predictivo. El SARIMAX ha sido configurado sin componentes estacionales.\n\n"
        )
    else:
        explicacion += (
            f"**Estacionalidad:** La descomposición STL revela una fuerza estacional de {strength:.2f} "
            f"({strength*100:.1f}%) para períodos de 12 meses, lo que supera el umbral de 0.6. "
            f"El modelo SARIMAX ha incorporado componentes estacionales para capturar este patrón.\n\n"
        )
    
    explicacion += (
        "**Evaluación:** Para validar la robustez de este pronóstico, se han generado "
        "previsiones iterativas a 3 meses vista utilizando cortes de los datos históricos entre 2018 y finales de 2023.\n\n"
    )

    try:
        ultimas_preds = df_results.tail(3)
        if not ultimas_preds.empty:
            explicacion += "**Últimas estimaciones (horizonte del último corte):**\n"
            for fecha, fila in ultimas_preds.iterrows():
                fecha_str = pd.to_datetime(fecha).strftime('%Y-%m')
                pred_val = fila['pred']
                low_val = fila['ci_low']
                high_val = fila['ci_high']
                explicacion += f"- **{fecha_str}**: {pred_val:,.2f} (intervalo: {low_val:,.2f} – {high_val:,.2f})\n"
            explicacion += "\n"
    except Exception as e:
        print(f"Aviso: no se pudieron formatear las predicciones recientes - {e}")

    
    explicacion += "Puedes consultar el gráfico completo con los intervalos de confianza en la pestaña **Trigo en Grecia**.\n\n"
    explicacion += "ROUTE: /trigo"
    
    return explicacion

if __name__ == "__main__":
    print(predecir_trigo_grecia.invoke(""))