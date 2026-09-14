"""
Primer modelo de Gradient Boosting para predicción de caudal a 1 día,
comparado contra los baselines de persistencia y climatología
(docs/modelo-baseline-caudal.md).

DECISIÓN DE LIBRERÍA: requirements.txt lista xgboost y lightgbm, pero
ninguno estaba instalado en el entorno de esta sesión. Se usa
sklearn.ensemble.GradientBoostingRegressor (Gradient Boosting genuino,
ya disponible) en vez de instalar una dependencia pesada adicional para un
primer prototipo. Ventaja adicional: expone feature_importances_
directamente, a diferencia de HistGradientBoostingRegressor. Cambiar a
xgboost/lightgbm queda como mejora futura si el desempeño lo justifica.

Variables predictoras (ver docs/modelo-baseline-caudal.md sección 5 para
la justificación de por qué la precipitación podría ayudar mas en GUATAPE):
- Caudal propio rezagado 1, 2 y 3 días (autocorrelación, igual que persistencia)
- Precipitación CHIRPS del día actual y rezagada 1-3 días
- Precipitación acumulada de los últimos 3 días (humedad antecedente)
- Caudal de 3 estaciones tributarias IDEAM (se excluye Bodegas, 0% cobertura
  en este rango — ver docs/dataset-consolidado-fase1.md)
- Estacionalidad (seno/coseno del día del año)

Validación: split cronológico único (no walk-forward recursivo) — mismo
punto de corte que los baselines (últimos 195 días = test) para que la
comparación sea directa. Un split único entrenado una vez es una
simplificación razonable para un primer prototipo; reentrenar día a día
(walk-forward recursivo real) queda como mejora futura si este modelo
muestra señal real.

Uso:
    python modelo_gbm_caudal.py --objetivo xm_guatape_m3s
    python modelo_gbm_caudal.py --objetivo xm_nare_m3s
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).parent))
from metricas_hidrologia import resumen_metricas

COLUMNAS_IDEAM_USABLES = ["ideam_0023087150_m3s", "ideam_0023087660_m3s", "ideam_0023087670_m3s"]


def construir_features(df: pd.DataFrame, objetivo: str) -> pd.DataFrame:
    """
    BUG REAL encontrado y corregido el 2026-09-14 (ver docs/bug-q-hoy-faltante.md):
    esta funcion NO incluia el caudal de HOY (fila D, sin desplazar) como predictor
    explicito -- solo q_lag1/2/3 (ayer, antier, hace 3 dias). El objetivo (objetivo_t1)
    es el caudal de MAÑANA (D+1), asi que el modelo nunca veia el dato mas reciente y
    mas predictivo, mientras que la persistencia si lo usa (Q(t+1)=Q(t)). Esto afecto
    a todos los modelos GBM de este proyecto hasta encontrarse (v1, v2). Corregido
    agregando q_hoy = df[objetivo] sin desplazar.
    """
    df = df.copy().sort_values("fecha").reset_index(drop=True)

    df["q_hoy"] = df[objetivo]
    for lag in (1, 2, 3):
        df[f"q_lag{lag}"] = df[objetivo].shift(lag)
        df[f"precip_lag{lag}"] = df["chirps_precip_mm"].shift(lag)

    df["precip_hoy"] = df["chirps_precip_mm"]
    df["precip_acum3"] = df["chirps_precip_mm"].rolling(3).sum()

    # Las estaciones IDEAM tienen huecos reales de reporte (ver
    # docs/dataset-consolidado-fase1.md) -- el mas relevante aqui es que
    # Puente La Feria (Marinilla) dejo de reportar el ultimo mes del dataset
    # al momento de esta corrida. Un dropna() ciego sobre estas columnas
    # truncaria injustamente el periodo de prueba mas reciente y rompería
    # la comparabilidad con el baseline (docs/modelo-baseline-caudal.md).
    # Se imputa con forward-fill acotado (7 dias) + mediana de la columna
    # para lo que quede sin llenar -- una estacion tributaria caida no
    # deberia bloquear toda la prediccion en un sistema pensado para operar.
    for col in COLUMNAS_IDEAM_USABLES:
        df[f"{col}_faltante"] = df[col].isna().astype(int)
        serie_imputada = df[col].ffill(limit=7)
        serie_imputada = serie_imputada.fillna(serie_imputada.median())
        df[f"{col}_hoy"] = serie_imputada

    dia_anio = df["fecha"].dt.dayofyear
    df["mes_sin"] = np.sin(2 * np.pi * dia_anio / 365.25)
    df["mes_cos"] = np.cos(2 * np.pi * dia_anio / 365.25)

    df["objetivo_t1"] = df[objetivo].shift(-1)  # lo que se predice: el caudal de MAÑANA

    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="../data/processed/dataset_fase1_diario.csv")
    ap.add_argument("--objetivo", default="xm_guatape_m3s")
    ap.add_argument("--frac-test", type=float, default=0.2)
    ap.add_argument("--salida", default=None)
    args = ap.parse_args()

    df = pd.read_csv(args.dataset, parse_dates=["fecha"])
    df_feat = construir_features(df, args.objetivo)

    columnas_predictoras = (
        ["q_hoy"]
        + [f"q_lag{l}" for l in (1, 2, 3)]
        + [f"precip_lag{l}" for l in (1, 2, 3)]
        + ["precip_hoy", "precip_acum3"]
        + [f"{c}_hoy" for c in COLUMNAS_IDEAM_USABLES]
        + [f"{c}_faltante" for c in COLUMNAS_IDEAM_USABLES]
        + ["mes_sin", "mes_cos"]
    )

    df_valido = df_feat.dropna(subset=columnas_predictoras + ["objetivo_t1"]).reset_index(drop=True)
    print(f"Filas utilizables tras crear features y quitar NaN de bordes/rezagos: {len(df_valido)} de {len(df_feat)}")

    n = len(df_valido)
    corte = int(n * (1 - args.frac_test))
    train, test = df_valido.iloc[:corte], df_valido.iloc[corte:]
    print(f"Train: {train['fecha'].min().date()} a {train['fecha'].max().date()} ({len(train)} días)")
    print(f"Test:  {test['fecha'].min().date()} a {test['fecha'].max().date()} ({len(test)} días)\n")

    X_train, y_train = train[columnas_predictoras], train["objetivo_t1"]
    X_test, y_test = test[columnas_predictoras], test["objetivo_t1"]

    modelo = GradientBoostingRegressor(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        min_samples_leaf=10,
        random_state=42,
    )
    modelo.fit(X_train, y_train)

    pred_train = modelo.predict(X_train)
    pred_test = modelo.predict(X_test)

    metricas_train = resumen_metricas(y_train.values, pred_train)
    metricas_test = resumen_metricas(y_test.values, pred_test)

    tabla = pd.DataFrame({"train": metricas_train, "test": metricas_test}).T
    print("Desempeño del modelo GBM:")
    print(tabla.to_string())

    if metricas_train["nse"] - metricas_test["nse"] > 0.3:
        print(
            "\nAVISO: la diferencia NSE train-test es grande (>0.3) -- señal de sobreajuste real, "
            "no solo un modelo que generaliza peor de lo esperado. Revisar antes de confiar en el resultado de test."
        )

    importancias = pd.Series(modelo.feature_importances_, index=columnas_predictoras).sort_values(ascending=False)
    print("\nImportancia de variables (Gradient Boosting):")
    print(importancias.to_string())

    salida = Path(args.salida) if args.salida else Path(f"../data/processed/gbm_resultados_{args.objetivo}.csv")
    salida.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(salida)

    ruta_importancias = salida.parent / f"gbm_importancias_{args.objetivo}.csv"
    importancias.to_csv(ruta_importancias, header=["importancia"])

    ruta_pred = salida.parent / f"gbm_predicciones_{args.objetivo}.csv"
    df_pred_out = test[["fecha"]].copy()
    df_pred_out["obs"] = y_test.values
    df_pred_out["pred_gbm"] = pred_test
    df_pred_out.to_csv(ruta_pred, index=False)

    print(f"\nGuardado: {salida}, {ruta_importancias}, {ruta_pred}")


if __name__ == "__main__":
    main()
