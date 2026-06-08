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
import dtale
import glob
import matplotlib.cm as cm

import pandas as pd

# --- Auxiliar para títulos ---
def _titulo(resultados: dict) -> str:
    if resultados.get("name"):
        return resultados["name"]
    elif resultados.get("subfamilia"):
        return resultados["subfamilia"]
    else:
        return "All products"


def inicializacion_datos(
    it: pd.DataFrame,
    transactions: pd.DataFrame,
    subfamilia: str | None = None,
    name: str | None = None,
    transaction: str | None = None,
    empresa: str | None = None,
):

    pk = it[it["DataAreaId"] == empresa].copy()

    if subfamilia is not None:
        pk = pk[pk["SubfamilyGrouping"].str.contains(subfamilia, case=False, na=False)]

    if name is not None:
        pk = pk[pk["Name"].str.contains(name, case=False, na=False)]

    fid = pk["ItemId"].unique()

    id_to_name = dict(zip(it["ItemId"], it["Name"]))

    final_df = transactions[(transactions.DataAreaId == empresa) & (transactions.ItemId.isin(fid))]
    final_df = final_df.copy()
    final_df["DatePhysical"] = pd.to_datetime(final_df["DatePhysical"], errors="coerce")

    compras = final_df[(final_df["ReferenceCategory"] == 3)].copy()
    ventas = final_df[(final_df["ReferenceCategory"] == 0)].copy()
    ventas["QTY"] = -ventas["QTY"]
    merma = final_df[
        (final_df["ReferenceCategory"] != 0)
        & (final_df["ReferenceCategory"] != 3)
    ].copy()

    # --- Agregación diaria ---
    compras_diarias = compras.groupby("DatePhysical", as_index=False)["QTY"].sum()
    ventas_diarias = ventas.groupby("DatePhysical", as_index=False)["QTY"].sum()
    merma_diarias = merma.groupby("DatePhysical", as_index=False)["QTY"].sum()

    # --- Agregación por produto ---
    ventas_indv = {
        loc: g.groupby("DatePhysical", as_index=False)["QTY"].sum()
        for loc, g in ventas.groupby("ItemId")
    }
    compras_indv = {
        loc: g.groupby("DatePhysical", as_index=False)["QTY"].sum()
        for loc, g in compras.groupby("ItemId")
    }
    mermas_indv = {
        loc: g.groupby("DatePhysical", as_index=False)["QTY"].sum()
        for loc, g in merma.groupby("ItemId")
    }

    # --- Agregación mensual ---
    ventas_mensuais = ventas.copy()
    ventas_mensuais["Mes"] = ventas_mensuais["DatePhysical"].dt.to_period("M").dt.to_timestamp()
    ventas_mensuais = (
        ventas_mensuais.groupby(["Mes", "ItemId"])["QTY"].sum().reset_index()
    )

    compras_mensuais = compras.copy()
    compras_mensuais["Mes"] = compras_mensuais["DatePhysical"].dt.to_period("M").dt.to_timestamp()
    compras_mensuais = (
        compras_mensuais.groupby(["Mes", "ItemId"])["QTY"].sum().reset_index()
    )

    mermas_mensuais = merma.copy()
    mermas_mensuais["Mes"] = mermas_mensuais["DatePhysical"].dt.to_period("M").dt.to_timestamp()
    mermas_mensuais = (
        mermas_mensuais.groupby(["Mes", "ItemId"])["QTY"].sum().reset_index()
    )

    # --- Valor descritivo da subfamilia (se hai) ---
    if name is not None and not pk.empty:
        # Se o usuario filtrou por 'name', devolvemos o nome real do produto
        name_final = pk["Name"].iloc[0]
        subfamilia_final = pk["SubfamilyGrouping"].iloc[0] if "SubfamilyGrouping" in pk.columns else None

    elif subfamilia is not None and not pk.empty:
        # Se o usuario filtrou por 'subfamilia', devolvemos a subfamilia real e non forzamos nome
        subfamilia_final = pk["SubfamilyGrouping"].iloc[0]
        name_final = None

    else:
        # Se non se filtrou por nada, ambos a None
        subfamilia_final = None
        name_final = None

    return {
        "final_df": final_df,
        "compras_diarias": compras_diarias,
        "ventas_diarias": ventas_diarias,
        "merma_diarias": merma_diarias,
        "ventas_mensuais": ventas_mensuais,
        "compras_mensuais": compras_mensuais,
        "mermas_mensuais": mermas_mensuais,
        "ventas_indv": ventas_indv,
        "compras_indv": compras_indv,
        "merma_indv": mermas_indv,
        "id_to_name": id_to_name,
        "subfamilia": subfamilia_final,
        "name": name_final,
        "transaction": transaction,
    }

def plot_st(resultados: dict, color="deepskyblue", show=True):
    """
    Xera as gráficas de vendas diarias e mensuais de pataca Kennebec.

    Args:
        resultados (dict): saída da función preparar_datos_transaccionais().
        color (str): cor principal das liñas.
        show (bool): se True, mostra a gráfica inmediatamente.

    Returns:
        tuple: (fig, ax) para modificar ou gardar posteriormente.
    """
    if resultados["transaction"] == 'sales':
        ventas_diarias = resultados["ventas_diarias"]
        ventas_mensuais = resultados["ventas_mensuais"]
    elif resultados["transaction"] == 'purchases':
        ventas_diarias = resultados["compras_diarias"]
        ventas_mensuais = resultados["compras_mensuais"]
    elif resultados["transaction"] == 'shrinkage':
        ventas_diarias = resultados["merma_diarias"]
        ventas_mensuais = resultados["mermas_mensuais"]

    fig, ax = plt.subplots(1, 2, figsize=(15, 5))
    fig.patch.set_facecolor("#fafafa")

    # --- Gráfico diario ---
    ax[0].set_facecolor("#fafafa")
    ax[0].plot(
        ventas_diarias.DatePhysical,
        ventas_diarias.QTY,
        color=color,
        linewidth=1.2,
        label="Ventas totais"
    )

    ax[0].set_title(f"{_titulo(resultados)} daily sales", fontsize=12, weight='bold')
    ax[0].set_xlabel("Year", fontweight="bold")
    ax[0].set_ylabel("QTY", fontweight="bold")
    ax[0].grid(True, color="#d1cfcf", alpha=0.4)

    anos = sorted(ventas_diarias.DatePhysical.dt.year.unique())
    tick_pos = [pd.Timestamp(year=int(y), month=1, day=1) for y in anos]
    ax[0].set_xticks(tick_pos)
    ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax[0].tick_params(colors="#424242")
    for spine in ax[0].spines.values():
        spine.set_visible(False)

    # --- Gráfico mensual ---
    ax[1].set_facecolor("#fafafa")
    ax[1].plot(
        ventas_mensuais.Mes,
        ventas_mensuais.QTY,
        color=color,
        linewidth=1.2,
        label="Ventas totais"
    )

    ax[1].set_title(f"{_titulo(resultados)} monthly {resultados['transaction']}", fontsize=12, weight='bold')
    ax[1].set_xlabel("Year", fontweight="bold")
    ax[1].set_ylabel("QTY", fontweight="bold")
    ax[1].grid(True, color="#d1cfcf", alpha=0.4)

    anos_mensuais = sorted(ventas_mensuais.Mes.dt.year.unique())
    tick_pos_mensuais = [pd.Timestamp(year=int(y), month=1, day=1) for y in anos_mensuais]
    ax[1].set_xticks(tick_pos_mensuais)
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax[1].tick_params(colors="#424242")
    for spine in ax[1].spines.values():
        spine.set_visible(False)

    plt.tight_layout()

    if show:
        plt.show()

def plot_total_monthly_sales(resultados: dict, color="deepskyblue", show=True):
    """
    Xera unha gráfica de barras coas vendas totais agregadas por mes
    (suma de todos os anos dispoñibles no conxunto de datos).

    Args:
        resultados (dict): saída da función `inicializacion_datos()`.
        color (str): cor principal das barras.
        show (bool): se True, mostra a gráfica inmediatamente.

    Returns:
        tuple: (fig, ax) para modificar ou gardar posteriormente.
    """
    if resultados["transaction"] == 'sales':
        ventas_mensuais = resultados["ventas_mensuais"]
    elif resultados["transaction"] == 'purchases':
        ventas_mensuais = resultados["compras_mensuais"]
    elif resultados["transaction"] == 'shrinkage':
        ventas_mensuais = resultados["mermas_mensuais"]

    # --- Agregación por mes ---
    ventas_por_mes = (
        ventas_mensuais
        .groupby(ventas_mensuais["Mes"].dt.month)["QTY"]
        .sum()
        .reindex(range(1, 13), fill_value=0)
    )

    n_meses = len(ventas_por_mes)

    # --- Gráfico ---
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    ax.bar(ventas_por_mes.index, ventas_por_mes.values, color=color, width=0.7)

    ax.set_title(f"{_titulo(resultados)} total monthly {resultados['transaction']}", fontsize=13, weight='bold')
    ax.set_xlabel("Month", fontweight="bold")
    ax.set_ylabel("QTY", fontweight="bold")

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        rotation=0
    )

    ax.tick_params(axis='x', colors="#424242")
    ax.tick_params(axis='y', colors="#424242")

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(axis='y', color="#d1cfcf", alpha=0.4)

    plt.tight_layout()

    if show:
        plt.show()

def plot_monthly_sales_by_variety(resultados: dict, gap: float = 1.0, show=True):
    """
    Xera un gráfico de barras apiladas coas vendas mensuais por variedade,
    """
    if resultados["transaction"] == 'sales':
        ventas_mensuais = resultados["ventas_mensuais"].copy()
    elif resultados["transaction"] == 'purchases':
        ventas_mensuais = resultados["compras_mensuais"].copy()
    elif resultados["transaction"] == 'shrinkage':
        ventas_mensuais = resultados["mermas_mensuais"].copy()
    id_to_name = resultados["id_to_name"]

    # --- Crear rango completo de meses ---
    all_months = pd.date_range(
        start=ventas_mensuais["Mes"].min(),
        end=ventas_mensuais["Mes"].max(),
        freq="MS"
    )

    # --- Pivot ---
    pivot = (
        ventas_mensuais
        .pivot(index="Mes", columns="ItemId", values="QTY")
        .fillna(0)
        .reindex(all_months, fill_value=0)
    )

    col_labels = [id_to_name.get(col, col) for col in pivot.columns]

    # --- Crear eixo X con espazo entre anos ---
    anos = sorted(pivot.index.year.unique())
    x_positions = []
    current_pos = 0

    for year in anos:
        n_months = (pivot.index.year == year).sum()
        x_positions.extend(np.arange(current_pos, current_pos + n_months))
        current_pos += n_months + gap  # engade espazo entre grupos

    pivot["x"] = x_positions

    # --- Gráfico ---
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    bottom = np.zeros(len(pivot))
    cmap = plt.get_cmap("Paired")
    colors = [cmap(i) for i in np.linspace(0.2, 0.9, len(pivot.columns)-1)]

    for i, col in enumerate(pivot.columns[:-1]):  # excluímos a columna 'x'
        ax.bar(
            pivot["x"],
            pivot[col],
            bottom=bottom,
            width=0.8,
            color=colors[i % len(colors)],
            label=col_labels[i]
        )
        bottom += pivot[col]

    # --- Etiquetas por ano ---
    centros = []
    for year in anos:
        subset = pivot[pivot.index.year == year]
        centros.append(subset["x"].mean())
    ax.set_xticks(centros)
    ax.set_xticklabels(anos)

    # --- Estilo ---
    ax.set_title(f"{_titulo(resultados)} monthly {resultados['transaction']} by variety", fontsize=13, weight='bold')
    ax.set_xlabel("Year", fontweight="bold")
    ax.set_ylabel("QTY", fontweight="bold")
    ax.tick_params(axis='x', colors="#424242", rotation=0)
    ax.tick_params(axis='y', colors="#424242")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(axis='y', color="#d1cfcf", alpha=0.4)

    # --- Lenda ---
    ax.legend(col_labels, title="Variety", bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()

    if show:
        plt.show()

    return fig, ax


def plot_monthly_sales_grouped_by_year(resultados: dict, gap: float = 1.0, show=True):
    """
    Xera unha gráfica de barras coas vendas mensuais agrupadas por ano,
    deixando un espazo visible entre anos e coloreando cada mes cunha paleta.

    Args:
        resultados (dict): saída da función `inicializacion_datos()`.
        gap (float): tamaño do espazo visual entre grupos de anos.
        show (bool): se True, mostra a gráfica inmediatamente.

    Returns:
        tuple: (fig, ax) para modificar ou gardar posteriormente.
    """
    if resultados["transaction"] == 'sales':
        ventas_mensuais = resultados["ventas_mensuais"].copy()
    elif resultados["transaction"] == 'purchases':
        ventas_mensuais = resultados["compras_mensuais"].copy()
    elif resultados["transaction"] == 'shrinkage':
        ventas_mensuais = resultados["mermas_mensuais"].copy()

    # --- Engadimos columnas auxiliares ---
    ventas_mensuais["ano"] = ventas_mensuais["Mes"].dt.year
    ventas_mensuais["num_mes"] = ventas_mensuais["Mes"].dt.month
    ventas_mensuais["nome_mes"] = ventas_mensuais["Mes"].dt.strftime("%b")

    ventas_mensuais = ventas_mensuais.groupby("Mes", as_index=False)["QTY"].sum()

    all_months = pd.date_range(
        start=ventas_mensuais["Mes"].min(),
        end=ventas_mensuais["Mes"].max(),
        freq="MS"
    )

    ventas_mensuais = (
        ventas_mensuais.set_index("Mes")
        .reindex(all_months)
        .reset_index()
        .rename(columns={"index": "Mes"})
    )

    ventas_mensuais["QTY"] = ventas_mensuais["QTY"].fillna(0)
    ventas_mensuais["ano"] = ventas_mensuais["Mes"].dt.year
    ventas_mensuais["num_mes"] = ventas_mensuais["Mes"].dt.month
    ventas_mensuais["nome_mes"] = ventas_mensuais["Mes"].dt.strftime("%b")

    # --- Crear eixo X con espazo entre anos ---
    unique_years = ventas_mensuais["ano"].unique()
    x_positions = []
    current_pos = 0

    for year in unique_years:
        n_months = len(ventas_mensuais[ventas_mensuais["ano"] == year])
        x_positions.extend(np.arange(current_pos, current_pos + n_months))
        current_pos += n_months + gap  # engade espazo entre grupos

    ventas_mensuais["x"] = x_positions

    # --- Definimos cores por mes ---
    palette = cm.tab20.colors[:12]
    colors = [palette[m - 1] for m in ventas_mensuais["num_mes"]]

    # --- Crear figura ---
    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    # --- Gráfico ---
    ax.bar(ventas_mensuais["x"], ventas_mensuais["QTY"], color=colors, width=1)

    # --- Eixes e formato ---
    ax.set_title(f"{_titulo(resultados)} monthly {resultados['transaction']} by year", fontsize=13, weight='bold')
    ax.set_xlabel("Year", fontweight="bold")
    ax.set_ylabel("QTY", fontweight="bold")

    # Marcas de ano centradas no grupo correspondente
    centros = []
    labels = []
    for year in unique_years:
        subset = ventas_mensuais[ventas_mensuais["ano"] == year]
        centros.append(subset["x"].mean())
        labels.append(str(year))
    ax.set_xticks(centros)
    ax.set_xticklabels(labels)

    # Estética
    ax.tick_params(axis='x', colors="#424242")
    ax.tick_params(axis='y', colors="#424242")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(axis='y', color="#d1cfcf", alpha=0.4)

    # --- Lenda dos meses ---
    handles = [plt.Rectangle((0, 0), 1, 1, color=palette[i]) for i in range(12)]
    labels_meses = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]
    ax.legend(handles, labels_meses, title="Month", bbox_to_anchor=(1.02, 1), loc='upper left')

    plt.tight_layout()

    if show:
        plt.show()

def plot_total_yearly_sales(resultados: dict, color="deepskyblue", show=True):
    """
    Xera unha gráfica de barras coas vendas totais agregadas por ano.

    Args:
        resultados (dict): saída da función `inicializacion_datos()`.
        color (str): cor principal das barras.
        show (bool): se True, mostra a gráfica inmediatamente.

    Returns:
        tuple: (fig, ax)
    """

    if resultados["transaction"] == 'sales':
        ventas_diarias = resultados["ventas_diarias"].copy()
    elif resultados["transaction"] == 'purchases':
        ventas_diarias = resultados["compras_diarias"].copy()
    elif resultados["transaction"] == 'shrinkage':
        ventas_diarias = resultados["merma_diarias"].copy()
        
    ventas_diarias["ano"] = ventas_diarias["DatePhysical"].dt.year

    # --- Agregación por ano ---
    ventas_por_ano = (
        ventas_diarias
        .groupby("ano")["QTY"]
        .sum()
        .sort_index()
    )

    # --- Gráfico ---
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    ax.bar(ventas_por_ano.index, ventas_por_ano.values, color=color, width=0.6)

    ax.set_title(f"{_titulo(resultados)} total yearly {resultados['transaction']}", fontsize=13, weight='bold')
    ax.set_xlabel("Year", fontweight="bold")
    ax.set_ylabel("QTY", fontweight="bold")
    ax.set_xticks(ventas_por_ano.index)


    ax.tick_params(axis='x', colors="#424242")
    ax.tick_params(axis='y', colors="#424242")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(axis='y', color="#d1cfcf", alpha=0.4)

    plt.tight_layout()
    if show:
        plt.show()

def plot_total_weekday_sales(resultados: dict, show=True):
    """
    Xera unha gráfica de barras coas vendas medias por día da semana.

    Args:
        resultados (dict): saída da función `inicializacion_datos()`.
        show (bool): se True, mostra a gráfica inmediatamente.

    Returns:
        tuple: (fig, ax)
    """
    if resultados["transaction"] == 'sales':
        ventas_diarias = resultados["ventas_diarias"].copy()
    elif resultados["transaction"] == 'purchases':
        ventas_diarias = resultados["compras_diarias"].copy()
    elif resultados["transaction"] == 'shrinkage':
        ventas_diarias = resultados["merma_diarias"].copy()
    ventas_diarias["dia_semana"] = ventas_diarias["DatePhysical"].dt.day_name()

    # Orde natural dos días
    dias_ord = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # --- Agregación por día da semana ---
    ventas_por_dia = (
        ventas_diarias
        .groupby("dia_semana")["QTY"]
        .mean()  # ou .sum() se prefires volume total
        .reindex(dias_ord)
    )

    # --- Gráfico ---
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    ax.bar(dias_ord, ventas_por_dia.values, color='deepskyblue', width=0.7)

    ax.set_title(f"{_titulo(resultados)} average daily {resultados['transaction']} by weekday", fontsize=13, weight='bold')
    ax.set_xlabel("Day of the week", fontweight="bold")
    ax.set_ylabel("Average QTY", fontweight="bold")

    ax.tick_params(axis='x', colors="#424242", rotation=0)
    ax.tick_params(axis='y', colors="#424242")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(axis='y', color="#d1cfcf", alpha=0.4)

    plt.tight_layout()
    if show:
        plt.show()

def plot_stl_decomposition(resultados: dict, periods=(7, 365), show=True):
    """
    Xera un grid de dúas columnas con descomposicións STL para varios períodos (semanal, anual...).
    Cada columna corresponde a un período estacional distinto.

    Args:
        resultados (dict): saída da función `inicializacion_datos()`.
        periods (tuple): períodos estacionais a analizar (por defecto semanal e anual).
        show (bool): se True, mostra a gráfica inmediatamente.

    Returns:
        tuple: (fig, axes)
    """

    # --- Serie diaria ---
    if resultados["transaction"] == 'sales':
        ventas_diarias = resultados["ventas_diarias"].copy()
    elif resultados["transaction"] == 'purchases':
        ventas_diarias = resultados["compras_diarias"].copy()
    elif resultados["transaction"] == 'shrinkage':
        ventas_diarias = resultados["merma_diarias"].copy()
    serie = ventas_diarias.set_index("DatePhysical")["QTY"].asfreq("D").fillna(0)

    # --- Preparar figuras ---
    n_periods = len(periods)
    n_rows = 4  # cada STL ten 4 compoñentes
    fig, axes = plt.subplots(n_rows, n_periods, figsize=(6*n_periods, 10), sharex=False)
    fig.patch.set_facecolor("#fafafa")

    if n_periods == 1:
        axes = np.array(axes).reshape(-1, 1)  # garantir estrutura 2D

    # --- Etiquetas ---
    comp_labels = ["Observed", "Trend", "Seasonal", "Residual"]

    for c, period in enumerate(periods):
        stl = STL(serie, period=period, robust=True)
        res = stl.fit()

        comps = [serie, res.trend, res.seasonal, res.resid]
        titulo = f"{_titulo(resultados)} STL decomposition (period={period})"

        for r, (comp, label) in enumerate(zip(comps, comp_labels)):
            ax = axes[r, c]
            ax.set_facecolor("#fafafa")
            ax.plot(comp, color="deepskyblue", linewidth=1.2)

            if r == 0:
                ax.set_title(titulo, fontsize=8, weight='bold', pad=10)
            if r == n_rows - 1:
                ax.set_xlabel("Date", fontweight="bold")

            ax.set_ylabel(label, fontweight="bold")
            ax.tick_params(colors="#424242", labelrotation=0)
            ax.grid(True, color="#d1cfcf", alpha=0.4)

            for spine in ax.spines.values():
                spine.set_visible(False)

    plt.tight_layout(h_pad=2.0, w_pad=2.0)

    if show:
        plt.show()

def plot_seasonal_pattern(
    resultados: dict,
    tipo: str = "ventas",
    period: str = "week",
    color_palette: str = "tab10",
    smooth: bool = False,
    title: str | None = None,
    show = True
):
    """
    Emula o comportamento de gg_season() de R, integrado co output de `inicializacion_datos()`.

    Args:
        resultados (dict): Saída da función `inicializacion_datos()`.
        tipo (str): 'ventas', 'compras' ou 'merma'.
        period (str): 'week', 'month' ou 'year' (define o ciclo estacional).
        color_palette (str): Paleta de cores de seaborn.
        smooth (bool): Se True, aplica suavizado por media móbil.
        title (str): Título opcional.
    """

    # --- Selección do dataframe ---
    tipo = tipo.lower()
    if tipo not in ["ventas", "compras", "merma"]:
        raise ValueError("tipo debe ser 'ventas', 'compras' ou 'merma'.")

    df = resultados[f"{tipo}_diarias"].copy()
    if df.empty:
        print(f"[Aviso] Non hai datos dispoñibles para '{tipo}_diarias'")
        return

    date_col = "DatePhysical"
    value_col = "QTY"
    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data = data.dropna(subset=[date_col, value_col])

    if period == "week":
        data["year"] = data[date_col].dt.year
        data["week"] = data[date_col].dt.isocalendar().week.astype(int)
        data["dayofweek"] = data[date_col].dt.day_name()
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        x_col, hue = "dayofweek", "week"
        group_cols = ["year", "week", "dayofweek"]

    elif period == "month":
        data["year"] = data[date_col].dt.year
        data["month"] = data[date_col].dt.month
        data["day"] = data[date_col].dt.day
        x_col, hue = "day", "month"
        order = None
        group_cols = ["year", "month", "day"]

    elif period == "year":
        data["year"] = data[date_col].dt.year
        data["month_name"] = data[date_col].dt.strftime("%b")
        x_col, hue = "year", "month_name"  # cambiamos o orden para claridade
        order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        group_cols = ["year", "month_name"]

    else:
        raise ValueError("period debe ser 'week', 'month' ou 'year'.")

    # --- agregación (agora conservamos hue sempre) ---
    grouped = data.groupby(group_cols, as_index=False)[value_col].sum()


    # --- suavizado opcional ---
    if smooth:
        grouped[value_col] = grouped.groupby(hue)[value_col].transform(lambda x: x.rolling(3, min_periods=1, center=True).mean())

    # --- título automático ---
    if title is None:
        base = resultados.get("name") or resultados.get("subfamilia") or "Todos os produtos"
        title = f"{base} – Seasonal pattern ({period})"

    # --- gráfico ---
    plt.figure(figsize=(10, 5))
    for key, grupo in grouped.groupby(hue):
        plt.plot(grupo[x_col], grupo[value_col], label=key, alpha=0.7)
    plt.title(title, fontsize=13, weight="bold")
    plt.xlabel(period.capitalize(), fontweight="bold")
    plt.ylabel(value_col, fontweight="bold")
    if order:
        plt.xticks(ticks=range(len(order)), labels=order)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    if show:
        plt.show()

def plot_forecasts_period(
    serie,
    df_forecasts,
    year = None,
    month = None,
    day = None,
    start_date=None,
    end_date=None,
    color_obs="deepskyblue",
    color_pred="red",
    title=None,
    ax=None,
    show=True
):
    """
    Debuxa a serie observada e as predicións do modelo (con intervalos de confianza)
    para un período específico (ano, mes e/ou día). Pode integrarse nun grid se se pasa un eixe 'ax'.

    Args:
        serie (pd.Series)
        df_forecasts (pd.DataFrame)
        year, month, day (int): Filtros opcionais
        ax (matplotlib.axes.Axes): Eixe opcional para debuxar nun grid
        show (bool): Se True, mostra a figura (só útil se non se usa grid)
    """
    if start_date is not None:
        start_date = pd.to_datetime(start_date)
    if end_date is not None:
        end_date = pd.to_datetime(end_date)

    def _make_mask(idx, year, month, day):
        mask = pd.Series(True, index=idx)

        # ---- YEAR ----
        if isinstance(year, int):
            mask &= idx.year == year
        elif isinstance(year, (tuple, list)) and len(year) == 2:
            mask &= (idx.year >= year[0]) & (idx.year <= year[1])

        # ---- MONTH ----
        if isinstance(month, int):
            mask &= idx.month == month
        elif isinstance(month, (tuple, list)) and len(month) == 2:
            mask &= (idx.month >= month[0]) & (idx.month <= month[1])

        # ---- DAY ----
        if isinstance(day, int):
            mask &= idx.day == day
        elif isinstance(day, (tuple, list)) and len(day) == 2:
            mask &= (idx.day >= day[0]) & (idx.day <= day[1])

        return mask

    # --- Filtrado da serie ---
    mask_serie = _make_mask(serie.index, year, month, day)
    mask_pred = _make_mask(df_forecasts.index, year, month, day)

    if start_date is not None:
        mask_serie &= serie.index >= start_date
        mask_pred  &= df_forecasts.index >= start_date
    if end_date is not None:
        mask_serie &= serie.index <= end_date
        mask_pred  &= df_forecasts.index <= end_date


    serie_sel = serie.loc[mask_serie]    
    df_sel = df_forecasts.loc[mask_pred]

    # --- Crear figura/ax ---
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 6))

    # Serie observada
    ax.plot(
        serie_sel.index,
        serie_sel,
        color=color_obs,
        alpha=0.6,
        label="Observed",
        marker="o",
        markersize=3
    )

    # Predicións por data de corte
    for cut_date, df_sub in df_sel.groupby("cut_date"):

        # --- UNIÓN ENTRE SERIE E PRIMEIRO PRED ---
        first_pred_date = df_sub.index.min()

        # buscar o último dato observado antes do forecast
        prev_obs = serie.loc[serie.index < first_pred_date]

        if len(prev_obs) > 0:
            last_obs_date = prev_obs.index.max()
            last_obs_value = prev_obs.loc[last_obs_date]

            ax.plot(
                [last_obs_date, first_pred_date],
                [last_obs_value.wt, df_sub.loc[first_pred_date].pred],
                color=color_pred,
                linestyle="--",
                alpha=0.7
            )

        # --- LIÑA DE PREDICIÓN ---
        ax.plot(
            df_sub.index,
            df_sub["pred"],
            label=f"Forecast (cut={cut_date.date()})",
            color=color_pred,
            marker="o",
            markersize=3
        )

        # --- INTERVALOS ---
        ax.fill_between(
            df_sub.index,
            df_sub["ci_low"],
            df_sub["ci_high"],
            alpha=0.2,
            color=color_pred
        )

    # --- Título e estilo ---
    if title is None:
        label = "-".join(str(x) for x in [year, month, day] if x is not None)
        title = f"{label}"
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.tick_params(axis="x", rotation=45)
    
    # Evitar lenda repetida se é nun grid
    if ax is None:
        ax.legend()

    if show and ax is None:
        plt.tight_layout()
        plt.show()

    return ax

def extraer_resultados_por_horizonte(results: dict, horizon: int | list[int], return_months: bool = True):
    """
    Extrae todas as predicións dun ou varios horizontes concretos
    e devolve tamén os pares únicos (ano, mes) presentes en 'date'.

    Args:
        results (dict): saída completa de run_sarimax_forecasts_parallel.
        horizon (int | list[int]): horizonte(s) desexado(s), p.ex. 7 ou [1, 7, 30].
        return_months (bool): se True, devolve tamén os pares únicos (ano, mes).

    Returns:
        tuple:
            - df_resultados (pd.DataFrame)
            - pares_mes (pd.DataFrame | None)
    """
    if isinstance(horizon, int):
        horizon = [horizon]

    records = []

    for cut_date, horizon_dict in results.items():
        for h, vals in horizon_dict.items():
            if vals["horizon"] in horizon:
                df_temp = pd.DataFrame({
                    "date": vals["pred"].index,
                    "pred": vals["pred"].values,
                    "ci_low": vals["ci_low"].values,
                    "ci_high": vals["ci_high"].values,
                })
                df_temp["cut_date"] = vals["cut_date"]
                df_temp["horizon"] = vals["horizon"]
                records.append(df_temp)

    if not records:
        empty = pd.DataFrame(columns=["cut_date", "horizon", "date", "pred", "ci_low", "ci_high"])
        return (empty, pd.DataFrame(columns=["ano", "mes"])) if return_months else empty

    df = pd.concat(records, ignore_index=True)
    df = df.sort_values(["cut_date", "date"]).reset_index(drop=True)

    if return_months:
        pares_mes = (
            df["date"]
            .dropna()
            .map(lambda d: (d.year, d.month))
            .drop_duplicates()
            .map(lambda p: {"ano": p[0], "mes": p[1]})
        )
        pares_mes = pd.DataFrame(list(pares_mes))
        return df, pares_mes.sort_values(["ano", "mes"]).reset_index(drop=True)

    return df

def plot_wheat_series(df, 
                      value_col="wheat",
                      title="Wheat",
                      ylabel="Price (€/Metric ton)",
                      color="blue",
                      max_year_ticks=100,
                      fill=False,
                      rolling_window=None,
                      show_rolling_var=False):
    
    x = df.index
    y = df[value_col]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    # Serie
    ax.plot(x, y, label=title, color=color, linewidth=1)

    if fill:
        ax.fill_between(x, y, color=color, alpha=0.3)

        # ---- Rolling mean ----
    if rolling_window is not None:
        roll_mean = y.rolling(rolling_window).mean()
        ax.plot(x, roll_mean,
                color="darkorange",
                linewidth=2,
                linestyle="--",
                label=f"Rolling mean ({rolling_window})")

        if show_rolling_var:
            roll_std = y.rolling(rolling_window).std()
            ax2 = ax.twinx()
            ax2.plot(x, roll_std,
                     color="orange",
                     linewidth=1.5,
                     alpha=0.6,
                     label=f"Rolling std ({rolling_window})")
            ax2.set_ylabel("Rolling std", color="crimson")
            ax2.tick_params(axis='y', colors="crimson")

    # Labels
    ax.set_xlabel("Year", fontweight="bold", color="#424242")
    ax.set_ylabel(ylabel, fontweight="bold", color="#424242")

    # Grid
    ax.grid(True, color="#d1cfcf", alpha=0.4)

    # ---- ticks por ano ----
    anos_unicos = sorted(x.year.unique().values)
    tick_pos = [pd.Timestamp(year=int(y), month=1, day=1) for y in anos_unicos]
    stride = max(1, len(tick_pos)//max_year_ticks)

    ax.set_xticks(tick_pos[::stride])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Estética
    ax.tick_params(axis='x', colors="#424242")
    ax.tick_params(axis='y', colors="#424242")
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()

def plot_exogs(df, cols, lag=1, marker='o'):
    
    x = df.index

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#fafafa")
    ax.set_facecolor("#fafafa")

    # Serie
    ax.plot(x, df[cols[0]], label=df[cols[0]].name, color='blue', linewidth=1, marker=marker, markersize=3)
    ax2 = ax.twinx()
    ax2.plot(x, df[cols[1]].shift(lag), label=df[cols[1]].name, color='orange', linewidth=1, marker=marker, markersize=3)

    # Labels
    ax.set_xlabel("Year", fontweight="bold", color="#424242")

    # Grid
    ax.grid(True, color="#d1cfcf", alpha=0.4)

    # ---- ticks por ano ----
    anos_unicos = sorted(x.year.unique().values)
    tick_pos = [pd.Timestamp(year=int(y), month=1, day=1) for y in anos_unicos]
    stride = max(1, len(tick_pos)//100)

    ax.set_xticks(tick_pos[::stride])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Estética
    ax.tick_params(axis='x', colors="#424242")
    ax.tick_params(axis='y', colors="#424242")
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_ylabel(cols[0], fontweight="bold", color="blue")
    ax2.set_ylabel(cols[1], fontweight="bold", color="orange")

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()