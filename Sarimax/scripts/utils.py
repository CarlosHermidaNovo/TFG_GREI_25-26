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
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import grangercausalitytests
from joblib import Parallel, delayed
from tqdm import tqdm
import itertools, statsmodels.api as sm
import pandas as pd
import warnings
import importlib
from scripts import train_predict
import ast
from tqdm_joblib import tqdm_joblib
from scipy.stats import norm
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from statsmodels.tsa.api import VAR
import os


def stationarity_tests(serie):
    kpss_result = kpss(serie)
    adf_result = adfuller(serie)

    print(f"----- KPSS Test -----")
    print("KPSS Statistic:", kpss_result[0])
    print("p-value:", kpss_result[1])
    
    if(kpss_result[1] < 0.05):
        print("The series IS NOT stationary")

    else:
        print("The series IS stationary")

    print(f"\n----- ADF Test -----")
    print("ADF Statistic:", adf_result[0])
    print("p-value:", adf_result[1])
    
    if(adf_result[1] < 0.05):
        print("The series IS stationary")

    else:
        print("The series IS NOT stationary")

def plot_acf_pacf(series, lag_max=50, alpha=0.05):
    """
    Plot the Autocorrelation Function (ACF) and Partial Autocorrelation Function (PACF) 
    for a given time series.

    Parameters
    ----------
    series : array-like or pd.Series
        The time series to analyze.
    lag_max : int, default=50
        Maximum number of lags to compute.
    alpha : float, default=0.05
        Significance level for confidence intervals.
    """
    # --- ACF ---
    acf_vals, confint = acf(series, nlags=lag_max, alpha=alpha)
    conf_low = confint[:, 0] - acf_vals
    conf_high = confint[:, 1] - acf_vals
    low_line = conf_low[-1]
    high_line = conf_high[-1]

    # --- PACF ---
    pacf_vals, confintp = pacf(series, nlags=lag_max, method="yw", alpha=alpha)
    conf_low_p = confintp[:, 0] - pacf_vals
    conf_high_p = confintp[:, 1] - pacf_vals
    low_line_p = conf_low_p[-1]
    high_line_p = conf_high_p[-1]

    # --- Plot ---
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # ACF
    axes[0].vlines(range(len(acf_vals)), [0], acf_vals, color="#D60000")
    axes[0].axhline(0, color="#424242")
    axes[0].axhline(high_line, color="#0208AD", linestyle="--", linewidth=1)
    axes[0].axhline(low_line, color="#0208AD", linestyle="--", linewidth=1)
    axes[0].set_ylim(-1.2, 1.2)
    axes[0].set_title("Autocorrelation (ACF)", fontweight="bold", color="#424242")
    axes[0].set_xticks(range(0, lag_max+1, 1))

    # PACF
    axes[1].vlines(range(len(pacf_vals)), [0], pacf_vals, color="#D60000")
    axes[1].axhline(0, color="#424242")
    axes[1].axhline(high_line_p, color="#0208AD", linestyle="--", linewidth=1)
    axes[1].axhline(low_line_p, color="#0208AD", linestyle="--", linewidth=1)
    axes[1].set_ylim(-1.2, 1.2)
    axes[1].set_title("Partial Autocorrelation (PACF)", fontweight="bold", color="#424242")
    axes[1].set_xticks(range(0, lag_max+1, 1))

    # Style
    fig.patch.set_facecolor("#fafafa")
    for ax in axes:
        ax.set_facecolor("#fafafa")
        ax.tick_params(axis='x', colors="#424242")
        ax.tick_params(axis='y', colors="#424242")
        ax.grid(True, color="#d1cfcf", alpha=0.4)

    plt.tight_layout()
    plt.show()

def smape(y_true, y_pred):
    return 100 * np.mean(2 * np.abs(y_pred - y_true) / (np.abs(y_true) + np.abs(y_pred)))
    
def make_lags(df, cols, n_lags, horizon=1, freq='D'):
    """
    Generate lagged versions of selected columns from a DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        Original DataFrame containing the time series data.
    cols : list of str
        List of column names in `df` to generate lags for.
    n_lags : int
        Number of lagged periods to create for each selected column.

    Returns
    -------
    df_lagged : pandas.DataFrame
        DataFrame containing the lagged features, with column names in the
        format "<column>_lag<k>" for lag k.

    Examples
    --------
    >>> df = pd.DataFrame({'y': [1, 2, 3, 4]})
    >>> make_lags(df, cols=['y'], n_lags=2)
    y_lag1  y_lag2
    0     NaN     NaN
    1     1.0     NaN
    2     2.0     1.0
    3     3.0     2.0
    """
    #f"date_lag{lag}": df.index.shift(-lag, freq='MS')
    lagged_series = []

    for col in cols:
        for lag in range(horizon, horizon + n_lags):
            df_tmp = pd.DataFrame({
            f"{col}_lag{lag}": df[col].shift(lag)
            })
            lagged_series.append(df_tmp)

    df_lagged = pd.concat(lagged_series, axis=1)
    return df_lagged
    
def top_ccf_vars(exs, target, n_lags=12, top_n=25):
    """
    Identify the top exogenous variables most correlated with a target 
    time series using the cross-correlation function (CCF).

    Parameters
    ----------
    exs : pandas.DataFrame
        DataFrame containing candidate exogenous variables (as columns) 
        to evaluate against the target series.
    target : pandas.Series
        Target time series to compute cross-correlations against.
    n_lags : int, optional (default=12)
        Number of lags to consider when computing the cross-correlation 
        function.
    top_n : int, optional (default=25)
        Number of top variables to return based on absolute CCF values.

    Returns
    -------
    df_result : pandas.DataFrame
        Table with the top variables most correlated with the target series. 
        Columns include:
        - 'variable': name of the exogenous variable,
        - 'max_abs_ccf': maximum absolute cross-correlation value 
        within the first `n_lags`,
        - 'best_lag': lag at which the maximum absolute cross-correlation occurs.

    Notes
    -----
    - This function ignores variables named "target" if present in `exs`.
    - Any rows with missing data in either the exogenous or target series 
    are dropped before computing CCF.
    - Only lags from 0 to `n_lags - 1` are considered.

    Examples
    --------
    >>> exs = pd.DataFrame({'x1': [1, 2, 3, 4], 'x2': [4, 3, 2, 1]})
    >>> target = pd.Series([1, 2, 3, 4])
    >>> top_ccf_vars(exs, target, n_lags=2, top_n=1)
    variable  max_abs_ccf  best_lag
    0       x1          1.0         0
    """
    
    results = []

    for col in exs.columns:
        if col == "target":
            continue
        try:
            x = exs[col].dropna()
            y = target.loc[x.index].dropna()
            common_index = x.index.intersection(y.index)
            x = x.loc[common_index]
            y = y.loc[common_index]

            if len(x) < n_lags:
                continue

            vals = ccf(x.values, y.values)
            max_corr = np.max(np.abs(vals[:n_lags]))
            best_lag = np.argmax(np.abs(vals[:n_lags]))
            results.append({
                "variable": col,
                "max_abs_ccf": max_corr,
                "best_lag": best_lag
            })
        except Exception as e:
            print(f"Error -> {col}: {e}")
            continue

    df_result = pd.DataFrame(results).sort_values("max_abs_ccf", ascending=False)
    return df_result.head(top_n)

def calcular_vif(exogs, lim=10):
    """
    Perform iterative Variance Inflation Factor (VIF) filtering to detect and 
    remove multicollinearity among exogenous variables.

    Parameters
    ----------
    exogs : pandas.DataFrame
        DataFrame containing the exogenous variables to evaluate.
    lim : float, optional (default=10)
        Threshold above which a variable is considered to exhibit high 
        multicollinearity and is removed.

    Returns
    -------
    vif_final : pandas.DataFrame
        DataFrame showing the VIF values of the remaining variables 
        (including the constant), sorted in descending order.
    exog_vars : list of str
        List of remaining variable names after removing those with 
        high multicollinearity.

    Notes
    -----
    - The function adds a constant term to compute the VIFs, but the constant 
      itself is excluded from the elimination process.
    - Variables are removed one at a time based on the highest VIF until 
      all VIFs fall below the specified `lim`.
    - The `variance_inflation_factor` is computed using `statsmodels`.

    Examples
    --------
    >>> import pandas as pd
    >>> from statsmodels.stats.outliers_influence import variance_inflation_factor
    >>> import statsmodels.api as sm
    >>> df = pd.DataFrame({
    ...     'x1': [1, 2, 3, 4, 5],
    ...     'x2': [2, 4, 6, 8, 10],  # Perfectly collinear with x1
    ...     'x3': [5, 4, 3, 2, 1]
    ... })
    >>> calcular_vif(df, lim=5)
    Deleting 'x2' (VIF=inf)
    (   Variable       VIF
     0     const  41.666667
     1       x3   5.000000
     2       x1   5.000000,
     ['x1', 'x3'])
    """
    
    exog_vars = list(exogs.columns)
    exogs_clean = exogs.dropna()
    continuar = True

    while continuar and len(exog_vars) > 1:
        X = sm.add_constant(exogs_clean[exog_vars])
        vif = pd.DataFrame({
            "Variable": X.columns,
            "VIF": [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
        })
        
        vif_exog = vif[vif["Variable"] != "const"]
        
        vif_exog = vif_exog.sort_values("VIF", ascending=False).reset_index(drop=True)
        
        max_vif = vif_exog.loc[0, "VIF"]
        max_var = vif_exog.loc[0, "Variable"]

        if max_vif > lim:
            print(f"Deleting '{max_var}' (VIF={max_vif:.2f})")
            exog_vars.remove(max_var)
        else:
            continuar = False

    # Cálculo final
    X = sm.add_constant(exogs_clean[exog_vars])
    vif_final = pd.DataFrame({
        "Variable": X.columns,
        "VIF": [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    }).sort_values("VIF", ascending=False).reset_index(drop=True)

    return vif_final, exog_vars

def grangers_causality_matrix(data, variables, maxlag=3, test='ssr_chi2test'):
    """
    Computes the Granger causality p-values between a target variable 
    (first element of `variables`) and all other variables in the DataFrame.

    For each predictor variable:
    - The function selects only the target and the predictor.
    - Because different variables may start at different dates, NaNs appear 
      at the beginning of some columns. To handle this, the function performs 
      pairwise filtering by dropping all rows where either series has NaN.
      This ensures that the Granger test is run only on the period where 
      both variables have valid observations.
    - If the remaining sample is too short for the specified `maxlag`, the 
      function fills the row with NaN and skips the test.
    - Otherwise, it runs the Granger causality test for lags 1..maxlag and 
      stores the corresponding p-values.

    Returns
    -------
    DataFrame
        Rows = predictor variables
        Columns = lags
        Values = p-values of the chosen Granger test.
    """
    df_result = pd.DataFrame(index=variables[1:], columns=range(1, maxlag+1))
    target = variables[0]

    for col in variables[1:]:
        # 1. Seleccionar só target e col
        df_pair = data[[target, col]].dropna()

        # 2. Se non hai puntos suficientes → encher con NaN
        if len(df_pair) < maxlag + 5:   # Regra práctica mínima
            df_result.loc[col, :] = np.nan
            continue

        # 3. Executar Granger nese tramo válido
        test_result = grangercausalitytests(df_pair, maxlag=maxlag, verbose=False)

        # 4. Gardar p-valores
        for lag in range(1, maxlag+1):
            p_value = test_result[lag][0][test][1]
            df_result.loc[col, lag] = p_value

    return df_result

def generar_fechas_corte_por_ano(serie, anos, n_semanas=3, seed=None):
    """
    Xera datas de corte (inicio de semana) para anos concretos e
    engade a semana seguinte á última data dispoñible.

    Args:
        serie (pd.Series | pd.DataFrame): serie temporal co índice de datas.
        anos (list[int]): lista de anos (ex. [2021, 2024]).
        n_semanas (int): número de semanas aleatorias por ano.
        seed (int | None): semente para reproducibilidade.

    Returns:
        list[pd.Timestamp]: lista ordenada de datas de corte.
    """
    if seed is not None:
        np.random.seed(seed)

    fechas_corte = []

    for ano in anos:
        # límite superior: non pasar da última data dispoñible
        inicio = pd.Timestamp(f"{ano}-01-01")
        fin = min(pd.Timestamp(f"{ano}-12-31"), serie.index.max())

        # se o rango é válido
        if inicio < fin:
            semanas = pd.date_range(inicio, fin, freq="W-MON")  # luns de cada semana
            if len(semanas) > 0:
                semanas_elexidas = np.random.choice(semanas, size=min(n_semanas, len(semanas)), replace=False)
                fechas_corte.extend(semanas_elexidas)

    # ordenar e devolver
    return sorted(pd.to_datetime(fechas_corte))

def generar_fechas_futuras(fecha_corte: pd.Timestamp, pasos: int, tipo: str) -> pd.DatetimeIndex:
    """
    Xera un rango de datas futuras segundo o tipo de forecast.

    Args:
        fecha_corte (pd.Timestamp): data de corte.
        pasos (int): número de períodos futuros.
        tipo (str): tipo de forecast ('D' diario, 'W' semanal, 'M' mensual, 'Y' anual).

    Returns:
        pd.DatetimeIndex: rango de datas futuras.
    """
    tipo = tipo.upper()
    if tipo not in ["D", "W", "M", "Y"]:
        raise ValueError(f"Tipo '{tipo}' non recoñecido. Usa 'D', 'W', 'M' ou 'Y'.")

    # Definir frecuencia equivalente
    freq_map = {"D": "D", "W": "W-SUN", "M": "MS", "Y": "YS"}
    freq = freq_map[tipo]

    # Calcular primeira data futura
    if tipo == "D":
        start = fecha_corte + pd.Timedelta(1, "D")
    elif tipo == "W":
        start = fecha_corte + pd.DateOffset(weeks=1)
    elif tipo == "M":
        start = (fecha_corte + pd.offsets.MonthBegin(1)).normalize()
    elif tipo == "Y":
        start = (fecha_corte + pd.offsets.YearBegin(1)).normalize()

    return pd.date_range(start=start, periods=pasos, freq=freq)

def df_to_sarimax_config(df):
    """
    Convert a DataFrame with columns
    ['fecha_corte', 'horizonte', 'parametros']
    into a nested dictionary config for run_sarimax_forecasts().
    """
    config = {}

    for _, row in df.iterrows():
        cut_date = str(row["fecha_corte"])
        horizon = int(row["horizonte"])

        # interpret tuple safely
        params = ast.literal_eval(row["parametros"])
        if len(params) == 7:
            order = tuple(params[:3])
            seasonal_order = tuple(params[3:])
        elif len(params) == 4:
            order = tuple(params)
            seasonal_order = (0, 0, 0, 0)
        else:
            raise ValueError(f"Unexpected parameter length for {params}")

        if cut_date not in config:
            config[cut_date] = {}
        config[cut_date][horizon] = {
            "order": order,
            "seasonal_order": seasonal_order
        }

    return config

def realizar_predicciones_paralelo(
    y,
    x,
    fechas_corte,
    forecast_types,
    s=12,
    pdq_range=(range(0, 3), range(0, 2), range(0, 3)),
    PDQ_range=(range(0, 2), range(0, 2), range(0, 2)),
    min_train_len=36,
    maxiter=500,
    n_jobs=-1, 
    file='results.csv'
):
    fechas_corte = fechas_corte
    forecast_types = forecast_types
    tasks = []

    '''for corte in fechas_corte:
        fechacorte = pd.to_datetime(corte)
        for tipo, pasos in forecast_types.items():
            if tipo == 'anual':
                fechas_pred = [fechacorte]
            elif tipo == 'trimestral':
                fechas_pred = [fechacorte + pd.DateOffset(months=i * 3) for i in range(4)]
            else:
                fechas_pred = [fechacorte + pd.DateOffset(months=i) for i in range(12)]
            for f in fechas_pred:
                tasks.append((f, tipo, pasos))'''
    
    for corte in fechas_corte:
        fechacorte = pd.to_datetime(corte)
        for tipo, config in forecast_types.items():
            pasos = config.get("steps", 1)
            tasks.append((fechacorte, config.get("freq", 'D'), pasos))

    print(f"Iniciando {len(tasks)} axustes en paralelo con {n_jobs if n_jobs>0 else 'todos os'} núcleos")

    with tqdm(total=len(tasks), desc="Progreso global", unit="modelo") as pbar:
        results = Parallel(n_jobs=n_jobs, backend='loky')(
            delayed(train_predict.entrenar_y_predecir)(y, x, fecha, tipo, pasos, s, pdq_range=pdq_range,
                PDQ_range=PDQ_range,
                min_train_len=min_train_len,
                maxiter=maxiter)
                
            for fecha, tipo, pasos in tasks
        )
        pbar.update(len(tasks))

    resultados_validos = [r for r in results if r is not None]
    df_resultados = pd.DataFrame(resultados_validos)
    df_resultados.to_csv(file, index=False)

    print(f"\Results saved in 'resultados_sarimax_exog_paralelo.csv'")

    return df_resultados

def _fit_and_forecast_cut(
    cut_date,
    series_proc,
    exogs,
    horizon_dict,
    freq,
    use_garch,
    log_transform,
    expand_len, 
    models_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
):
    """Sub-función interna que se executa en paralelo por cada cut_date."""
    cut_date = pd.Timestamp(cut_date)
    if freq == 'W-FRI':
        full_test = series_proc.loc[cut_date +pd.offsets.Week(4, weekday=4):].asfreq(freq)
    else:
        full_test = series_proc.loc[cut_date + pd.Timedelta("1D"):].asfreq(freq)
    results_cut = {}

    for h, params in horizon_dict.items():
        k = 0
        target_len = expand_len if expand_len and expand_len > h else h

        preds, ci_lows, ci_highs, all_idx = [], [], [], []
        train = series_proc.loc[:cut_date].asfreq(freq)
        remaining = target_len

        simus = []

        while remaining > 0:
            lower = None
            upper = None
            sims = None
            step = min(h, remaining)

            last_date = train.index[-1]
            idx_future = pd.date_range(
                start=last_date + pd.tseries.frequencies.to_offset(freq),
                periods=step,
                freq=freq
            )

            if exogs is not None:
                exog_train = exogs.reindex(train.index).asfreq(freq)
            else:
                exog_train = None

            if exogs is not None:
                exog_fore = exogs.loc[exogs.index.intersection(idx_future)]
                if len(exog_fore) < len(idx_future):
                    exog_fore = exogs.reindex(idx_future)
            else:
                exog_fore = None


            model = sm.tsa.statespace.SARIMAX(
                train,
                order=params.get("order", (1, 0, 0)),
                seasonal_order=params.get("seasonal_order", (0, 0, 0, 0)),
                exog=exog_train,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            res = model.fit(disp=False, method='powell', maxiter=1000)

            model_path = os.path.join(
                models_dir,
                f"sarimax_cut={cut_date.date()}_h={h}_k={k}.pkl"
            )

            res.save(model_path)

            k += 1

            '''with open(f"../logs/summary_{cut_date}.txt", "w") as f:
                f.write(res.summary().as_text())
                f.write(exog_fore.to_string())
                f.write(exogs.to_string())
                f.write(res.params.to_string())
'''
            
            forecast = res.get_forecast(steps=step, exog=exog_fore)
            pred_mean = forecast.predicted_mean
            resid = res.filter_results.standardized_forecasts_error[0]

            # COMPROBACIÓN DE NORMALIDAD
            jb_stat, jb_p, skew, kurt = jarque_bera(resid)
            ok_jb = jb_p > 0.05

            if ok_jb:
                ci = forecast.conf_int(alpha=0.05)
                lower = ci.iloc[:, 0]
                upper = ci.iloc[:, 1]

                if log_transform:
                    lower = np.exp(lower)
                    upper = np.exp(upper)

            else:
                lower, upper, sims = bootstrap_forecast_sarimax(res, log_transform=log_transform, exog=exog_fore)

            
            if log_transform:
                var_h = forecast.var_pred_mean  
                pred_mean = np.exp(pred_mean) * (1 + var_h/2)

            # --- GARCH opcional ---
            if use_garch:
                garch_model = arch_model(resid, vol="GARCH", p=1, q=1, dist="t")
                garch_res = garch_model.fit(disp="off")
                garch_fore = garch_res.forecast(horizon=step)
                sigma2 = garch_fore.variance.iloc[-1].values
                sigma = np.sqrt(sigma2)
            else:
                sigma2 = forecast.var_pred_mean.values
                sigma = np.sqrt(sigma2)
                garch_res = None

            idx_fore = full_test.index[len(all_idx):len(all_idx) + step]

            last_date = train.index[-1]
            idx_results = pd.date_range(start=last_date + pd.tseries.frequencies.to_offset(freq),
                                    periods=step, freq=freq)

            preds.extend(pred_mean)
            ci_lows.extend(lower)
            ci_highs.extend(upper)
            all_idx.extend(idx_results)

            if sims is not None:
                simus.extend(sims)

            # --- Engadir datos reais deses pasos ---
            remaining -= step
            
            if (remaining > 0) and (len(idx_fore) > 0):
                train = pd.concat([train, full_test.loc[idx_fore]])

            else: 
                break
            

        results_cut[h] = {
            "pred": pd.Series(preds, index=all_idx),
            "ci_low": pd.Series(ci_lows, index=all_idx),
            "ci_high": pd.Series(ci_highs, index=all_idx),
            "res": res,
            "horizon": h,
            "cut_date": cut_date
        }

    return cut_date, results_cut, simus


def run_sarimax_forecasts_parallel(
    series: pd.Series,
    exogs,
    config_dict: dict,
    use_garch: bool = False,
    log_transform: bool = False,
    freq: str = "D",
    expand_len: int | None = None,
    n_jobs: int = -1
):
    #series_proc = np.log(series) if log_transform else series.copy()
    series_proc = series.copy()

    # --- tqdm para joblib ---
    with tqdm_joblib(tqdm(total=len(config_dict), desc="Forecast progress")):
        results_list = Parallel(n_jobs=n_jobs, backend="loky")(
            delayed(_fit_and_forecast_cut)(
                cut_date,
                series_proc,
                exogs,
                horizon_dict,
                freq,
                use_garch,
                log_transform,
                expand_len
            )
            for cut_date, horizon_dict in config_dict.items()
        )

    results = {cut_date: res for cut_date, res, sim in results_list}
    simulaciones = {cut_date: sim for cut_date, res, sim in results_list}
    return results, simulaciones

def bootstrap_forecast_sarimax(res, steps=3, B=1000, log_transform=False, exog=None):

    rng = np.random.default_rng(42)
    sims = np.empty((B, steps), dtype=float)

    resid = res.resid

    for b in range(B):
        shocks = rng.choice(resid, size=steps, replace=True)

        sim = res.simulate(
            nsimulations=steps,
            measurement_shocks=shocks,
            anchor='end', 
            exog=exog
        )

        sims[b, :] = np.asarray(sim).ravel()

    if log_transform:
        sims = np.exp(sims)
    # Intervalos en log
    lower_log = np.percentile(sims, 2.5, axis=0)
    upper_log = np.percentile(sims, 97.5, axis=0)

    # Back-transform directamente (bootstrap)
    lower = lower_log
    upper = upper_log

    return lower, upper, sims

def xerar_datas_corte(inicio, fin, freq, step=1, posicion="end"):

    inicio = pd.Timestamp(inicio)
    fin = pd.Timestamp(fin)

    offset_map = {
        ("D", "start"): pd.offsets.Day(),
        ("D", "end"): pd.offsets.Day(),

        ("W", "start"): pd.offsets.Week(weekday=0),     
        ("W", "end"): pd.offsets.Week(weekday=6),

        ("M", "start"): pd.offsets.MonthBegin(),
        ("M", "end"): pd.offsets.MonthEnd(),

        ("Q", "start"): pd.offsets.QuarterBegin(startingMonth=1),
        ("Q", "end"): pd.offsets.QuarterEnd(startingMonth=1),

        ("Y", "start"): pd.offsets.YearBegin(),
        ("Y", "end"): pd.offsets.YearEnd(),
    }

    if (freq, posicion) not in offset_map:
        raise ValueError("Combinación freq/posicion non soportada.")

    base_offset = offset_map[(freq, posicion)]
    full_offset = base_offset * step

    datas = []

    actual = inicio

    while actual <= fin:
        datas.append(actual.strftime("%Y-%m-%d"))
        actual += full_offset

    return datas[:-1]

def check_stationarity_exog(df, exog_cols, alpha=0.05):
    estacionarias = []
    non_estacionarias = []

    for col in exog_cols:
        serie = df[col].dropna()
        pvalue = adfuller(serie)[1]

        if pvalue < alpha:
            estacionarias.append(col)
        else:
            non_estacionarias.append(col)

    print("=== Endogenous stationarity ===")
    if estacionarias:
        print("Stationary (I(0)):", estacionarias)
    else:
        print("None exogenous is stationary")

    if non_estacionarias:
        print("No-stationary (I(1)):", non_estacionarias)

    return estacionarias, non_estacionarias

def johansen_cointegration_tests(df, target_col, i1_exogs, det_order=0, maxlags=12, alpha=0.05):
    
    cointegrated = []
    not_cointegrated = []
    
    print("=== Johansen cointegration test ===")
    
    for exog in i1_exogs:
        print(f"\nChecking cointegration: {target_col} - {exog}")
        
        pair_df = df[[target_col, exog]].dropna()
        
        if len(pair_df) < 30:
            not_cointegrated.append(exog)
            continue
        
        try:
            order_res = VAR(pair_df).select_order(maxlags)
            p = order_res.aic
        except Exception as e:
            not_cointegrated.append(exog)
            continue
        
        if p is None or p < 1:
            p = 2
        
        k_ar_diff = p - 1
        
        print(f"Optimal lag VAR (AIC): p = {p}")
        
        try:
            jres = coint_johansen(pair_df, det_order=det_order, k_ar_diff=k_ar_diff)
        except Exception as e:
            not_cointegrated.append(exog)
            continue
        
        trace_stat = jres.lr1[0]  
        trace_crit = jres.cvt[0, 1]
        
        print(f"Trace statistic (r=0): {trace_stat:.3f}")
        print(f"Critical value 95%:   {trace_crit:.3f}")
        
        if trace_stat > trace_crit:
            print(f"Cointegration between {target_col} e {exog} (rank ≥ 1)")
            cointegrated.append(exog)
        else:
            not_cointegrated.append(exog)
    
    print("\n=== RESUMO FINAL ===")
    print("Cointegrated:", cointegrated if cointegrated else "None")
    print("No-cointegrated:", not_cointegrated if not_cointegrated else "None")
    
    return cointegrated, not_cointegrated

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats

from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.stattools import jarque_bera
from statsmodels.graphics.tsaplots import plot_acf

def sarimax_ci_readiness_report(res, lags_lb=(10, 20), lags_acf=40, alpha=0.05):
    # resid = res.resid.dropna()
    resid = res.filter_results.standardized_forecasts_error[0]

    print("\n=== 1) Autocorrelation of residuals (Ljung–Box) ===")
    lb = acorr_ljungbox(resid, lags=list(lags_lb), return_df=True)
    print(lb)
    ok_lb = (lb["lb_pvalue"] > alpha).all()

    print("\n=== 2) Conditional heteroskedasticity (ARCH-LM) ===")
    arch_stat, arch_p, _, _ = het_arch(resid)
    print(f"ARCH-LM p-value: {arch_p:.6f}")
    ok_arch = arch_p > alpha

    print("\n=== 3) Normality (Jarque–Bera + Q-Q) ===")
    jb_stat, jb_p, skew, kurt = jarque_bera(resid)
    print(f"JB p-value: {jb_p:.6f} | skew={skew:.3f} | kurtosis={kurt:.3f}")
    ok_jb = jb_p > alpha

    # Plots (visual diagnosis)
    print("\n=== Plots ===")
    res.plot_diagnostics(figsize=(12, 8))
    plt.tight_layout()
    plt.show()

    print("\n=== ACF/PACF of residuals ===")
    plt.figure(figsize=(8, 3))
    plot_acf_pacf(resid, lags_acf)
    
    print("\n=== ACF\PACF of squared residuals (volatility clustering) ===")
    plot_acf_pacf(resid**2, lags_acf)

    # Decision logic (practical)
    print("\n=== Decision (for using SARIMAX CIs) ===")
    if ok_lb and ok_arch:
        print("✅ Core assumptions for CI are OK (no autocorrelation + no ARCH).")
        if ok_jb:
            print("✅ Normality is also OK → CIs are well-justified under Gaussian approx.")
        else:
            print("⚠️ Normality rejected → CIs are approximate (tails may be off).")
    else:
        print("❌ Core assumptions fail → CIs may be unreliable.")
        if not ok_lb:
            print("   - Residual autocorrelation detected: model mean not fully captured.")
        if not ok_arch:
            print("   - ARCH effects detected: time-varying variance not modeled.")

    return {
        "lb": lb,
        "arch_p": arch_p,
        "jb_p": jb_p,
        "ok_lb": ok_lb,
        "ok_arch": ok_arch,
        "ok_jb": ok_jb
    }
