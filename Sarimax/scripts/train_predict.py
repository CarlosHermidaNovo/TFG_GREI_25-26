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

def generar_fechas_futuras(fecha_corte: pd.Timestamp, pasos: int, tipo: str) -> pd.DatetimeIndex:
    tipo = tipo.upper()
    if tipo not in ["D", "W", "M", "Y", "W-FRI", "B", "MS"]:
        raise ValueError(f"Tipo '{tipo}' non recoñecido. Usa 'D', 'W', 'M' ou 'Y'.")

    # Definir frecuencia equivalente
    freq_map = {"D": "D", "W-FRI": "W-FRI", "MS": "MS", "Y": "YS", "B":"B"}  # MS = month start, YS = year start
    freq = freq_map[tipo]

    # Calcular primeira data futura
    if tipo == "D":
        start = fecha_corte + pd.Timedelta(1, "D")
    elif tipo == "B":  # Business day
        start = fecha_corte + pd.offsets.BusinessDay(1)
    elif tipo == "W-FRI":
        start = fecha_corte + pd.offsets.Week(4, weekday=4)
    elif tipo == "MS":
        start = (fecha_corte + pd.offsets.MonthBegin(1)).normalize()
    elif tipo == "Y":
        start = (fecha_corte + pd.offsets.YearBegin(1)).normalize()

    return pd.date_range(start=start, periods=pasos, freq=freq)

def entrenar_y_predecir(
    y,
    x,
    fecha_corte,
    tipo,
    pasos,
    s=12,
    pdq_range=(range(0, 2), range(0, 2), range(0, 3)),   # (p,d,q)
    PDQ_range=(range(0, 2), range(0, 2), range(0, 2)),   # (P,D,Q)
    min_train_len=1,
    maxiter=500
):
    warnings.filterwarnings("ignore", message="Maximum Likelihood optimization failed to converge. Check mle_retvals")
    warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="statsmodels")
    try:

        Y_train = y.loc[:fecha_corte] if y is not None else None
        Y_test_index = generar_fechas_futuras(fecha_corte, pasos, tipo)
        Y_test = pd.Series(index=Y_test_index, dtype=float)
        X_train = x.loc[:fecha_corte] if x is not None else None
        # X_test = x.loc[fecha_corte:].head(pasos) if x is not None else None

        if len(Y_test) < pasos or len(Y_train) < min_train_len:
            return None

        p_range, d_range, q_range = pdq_range
        P_range, D_range, Q_range = PDQ_range
        s_values = s

        combinaciones = [
            (p_, d_, q_, P_, D_, Q_, s_)
            for p_, d_, q_, P_, D_, Q_, s_ in itertools.product(
                p_range, d_range, q_range, P_range, D_range, Q_range, s_values
            )
            if not (q_ != 0 and Q_ != 0 and q_ == s_ * Q_)
            if not (s_ == 0 and (P_ != 0 or D_ != 0 or Q_ != 0))
        ]
        total_comb = len(combinaciones)
        mejor_aicc = float('inf')
        mejores_parametros = None
        
        with tqdm(total=total_comb, desc=f"{fecha_corte.strftime('%Y-%m-%d')} ({pasos} - {tipo})", position=1, leave=False) as pbar:
            for (p_, d_, q_, P_, D_, Q_, s_) in combinaciones:
                try:
                    model = sm.tsa.statespace.SARIMAX(
                        Y_train,
                        exog=X_train,
                        order=(p_, d_, q_),
                        seasonal_order=(P_, D_, Q_, s_),
                        enforce_stationarity=False,
                        enforce_invertibility=False
                    )
                    result = model.fit(disp=False, maxiter=500)
                    aicc = result.aicc
                    if aicc < mejor_aicc:
                        mejor_aicc = aicc
                        mejores_parametros = (p_, d_, q_, P_, D_, Q_, s_)
                except Exception as e:
                    print(f"Erro para (p,d,q,P,D,Q)=({p_},{d_},{q_},{P_},{D_},{Q_}): {type(e).__name__} -> {e}")
                    pass
                finally:
                    pbar.update(1)

        if mejores_parametros is None:
            return None

        '''model = sm.tsa.statespace.SARIMAX(
            Y_train,
            exog=X_train,
            order=mejores_parametros[:3],
            seasonal_order=mejores_parametros[3:],
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        result = model.fit(disp=False, maxiter=maxiter)'''

        return {
            'fecha_corte': fecha_corte.strftime('%Y-%m-%d'),
            'tipo_forecast': tipo,
            'horizonte': pasos,
            'parametros': mejores_parametros,
            'AICc': mejor_aicc,
        }

    except Exception as e:
        print(f"Erro en {fecha_corte} ({tipo}): {e}")
        return None