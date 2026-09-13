"""
Segunda versión del modelo de Gradient Boosting — ataca el sobreajuste real
detectado en modelo_gbm_caudal.py (diferencia NSE train-test >0.3 en ambos
ríos, ver docs/modelo-gbm-caudal.md sección 6).

Tres cambios concretos, no solo "bajar un hiperparámetro a ojo":

1. HistGradientBoostingRegressor en vez de GradientBoostingRegressor:
   regularización L2 nativa (l2_regularization) y early stopping integrado,
   en vez de solo limitar max_depth manualmente.
2. Selección de hiperparámetros por validación cruzada temporal
   (TimeSeriesSplit) sobre el período de entrenamiento únicamente — el
   período de prueba nunca se toca durante la búsqueda, para no inflar el
   resultado final por sobreajustar la elección de hiperparámetros al test.
3. Walk-forward real con reentrenamiento periódico en el período de prueba
   (no un único ajuste estático) — evalúa el modelo en múltiples ventanas
   de generalización real en vez de confiar en un solo split.

NOTA: HistGradientBoostingRegressor no expone feature_importances_ (a
diferencia de GradientBoostingRegressor). Se usa importancia por permutación
(sklearn.inspection.permutation_importance) sobre el conjunto de prueba —
en varios aspectos más honesta que la importancia por impureza de todas
formas, porque mide el efecto real en el error de predicción.

Uso:
    python modelo_gbm_regularizado.py --objetivo xm_guatape_m3s
    python modelo_gbm_regularizado.py --objetivo xm_nare_m3s
"""

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import TimeSeriesSplit

sys.path.insert(0, str(Path(__file__).parent))
from metricas_hidrologia import resumen_metricas
from modelo_gbm_caudal import COLUMNAS_IDEAM_USABLES, construir_features

GRILLA_HIPERPARAMETROS = {
    "max_leaf_nodes": [7, 15, 31],
    "learning_rate": [0.02, 0.05],
    "l2_regularization": [0.0, 1.0, 5.0],
    "min_samples_leaf": [15, 25],
}


def seleccionar_hiperparametros(X_train: pd.DataFrame, y_train: pd.Series, n_splits: int = 5) -> dict:
    """Busqueda por validacion cruzada temporal (TimeSeriesSplit) -- nunca toca el test."""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    combinaciones = [
        dict(zip(GRILLA_HIPERPARAMETROS.keys(), valores))
        for valores in itertools.product(*GRILLA_HIPERPARAMETROS.values())
    ]

    resultados = []
    for params in combinaciones:
        nse_folds, gap_folds = [], []
        for idx_train, idx_val in tscv.split(X_train):
            X_tr, X_val = X_train.iloc[idx_train], X_train.iloc[idx_val]
            y_tr, y_val = y_train.iloc[idx_train], y_train.iloc[idx_val]
            modelo = HistGradientBoostingRegressor(
                max_iter=300,
                early_stopping=True,
                n_iter_no_change=15,
                validation_fraction=0.15,
                random_state=42,
                **params,
            )
            modelo.fit(X_tr, y_tr)
            nse_tr = resumen_metricas(y_tr.values, modelo.predict(X_tr))["nse"]
            nse_val = resumen_metricas(y_val.values, modelo.predict(X_val))["nse"]
            nse_folds.append(nse_val)
            gap_folds.append(nse_tr - nse_val)

        resultados.append(
            {
                **params,
                "nse_val_promedio": np.mean(nse_folds),
                "gap_train_val_promedio": np.mean(gap_folds),
            }
        )

    tabla = pd.DataFrame(resultados).sort_values("nse_val_promedio", ascending=False)
    return tabla


def walk_forward_hist_gbm(
    df_valido: pd.DataFrame,
    columnas: list,
    objetivo_col: str,
    inicio_test: int,
    params: dict,
    ventana_reentreno: int = 30,
) -> pd.DataFrame:
    """Reentrena cada `ventana_reentreno` dias con todo lo disponible hasta ese punto
    (ventana expandida), y predice solo el bloque siguiente -- nunca ve el futuro."""
    predicciones = []
    n = len(df_valido)
    corte = inicio_test
    while corte < n:
        fin_bloque = min(corte + ventana_reentreno, n)
        train = df_valido.iloc[:corte]
        bloque = df_valido.iloc[corte:fin_bloque]

        modelo = HistGradientBoostingRegressor(
            max_iter=300,
            early_stopping=True,
            n_iter_no_change=15,
            validation_fraction=0.15,
            random_state=42,
            **params,
        )
        modelo.fit(train[columnas], train[objetivo_col])
        pred = modelo.predict(bloque[columnas])

        predicciones.append(
            pd.DataFrame({"fecha": bloque["fecha"].values, "obs": bloque[objetivo_col].values, "pred_gbm_v2": pred})
        )
        corte = fin_bloque

    return pd.concat(predicciones, ignore_index=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="../data/processed/dataset_fase1_diario.csv")
    ap.add_argument("--objetivo", default="xm_guatape_m3s")
    ap.add_argument("--frac-test", type=float, default=0.2)
    ap.add_argument("--ventana-reentreno", type=int, default=30)
    args = ap.parse_args()

    df = pd.read_csv(args.dataset, parse_dates=["fecha"])
    df_feat = construir_features(df, args.objetivo)

    columnas = (
        [f"q_lag{l}" for l in (1, 2, 3)]
        + [f"precip_lag{l}" for l in (1, 2, 3)]
        + ["precip_hoy", "precip_acum3"]
        + [f"{c}_hoy" for c in COLUMNAS_IDEAM_USABLES]
        + [f"{c}_faltante" for c in COLUMNAS_IDEAM_USABLES]
        + ["mes_sin", "mes_cos"]
    )
    df_valido = df_feat.dropna(subset=columnas + ["objetivo_t1"]).reset_index(drop=True)

    n = len(df_valido)
    corte = int(n * (1 - args.frac_test))
    train = df_valido.iloc[:corte]
    print(f"Train para seleccion de hiperparametros: {train['fecha'].min().date()} a {train['fecha'].max().date()} ({len(train)} dias)")
    print(f"Test (walk-forward, nunca visto durante la seleccion): {df_valido.iloc[corte]['fecha'].date()} a {df_valido.iloc[-1]['fecha'].date()} ({n - corte} dias)\n")

    print("Buscando hiperparametros por validacion cruzada temporal (TimeSeriesSplit, 5 folds)...")
    tabla_busqueda = seleccionar_hiperparametros(train[columnas], train["objetivo_t1"])
    print(tabla_busqueda.head(10).to_string(index=False))

    mejor = tabla_busqueda.iloc[0]
    params_elegidos = {k: mejor[k] for k in GRILLA_HIPERPARAMETROS}
    # sklearn devuelve floats desde la grilla -- max_leaf_nodes y min_samples_leaf deben ser enteros
    params_elegidos["max_leaf_nodes"] = int(params_elegidos["max_leaf_nodes"])
    params_elegidos["min_samples_leaf"] = int(params_elegidos["min_samples_leaf"])
    print(f"\nHiperparametros elegidos (mejor NSE promedio de validacion): {params_elegidos}")
    print(f"Gap train-val promedio con esta configuracion: {mejor['gap_train_val_promedio']:.4f} (antes era >0.3 con el modelo v1)")

    print(f"\nCorriendo walk-forward real en el periodo de prueba (reentreno cada {args.ventana_reentreno} dias)...")
    df_pred = walk_forward_hist_gbm(df_valido, columnas, "objetivo_t1", corte, params_elegidos, args.ventana_reentreno)

    metricas_test = resumen_metricas(df_pred["obs"].values, df_pred["pred_gbm_v2"].values)
    print("\nDesempeño en test (walk-forward real, no un solo ajuste estatico):")
    for k, v in metricas_test.items():
        print(f"  {k}: {v}")

    # Importancia por permutacion sobre el ultimo modelo entrenado (el que ve mas datos)
    modelo_final = HistGradientBoostingRegressor(
        max_iter=300, early_stopping=True, n_iter_no_change=15, validation_fraction=0.15, random_state=42, **params_elegidos
    )
    modelo_final.fit(train[columnas], train["objetivo_t1"])
    resultado_perm = permutation_importance(
        modelo_final, df_valido.iloc[corte:][columnas], df_valido.iloc[corte:]["objetivo_t1"],
        n_repeats=20, random_state=42, scoring="neg_mean_squared_error",
    )
    importancias = pd.Series(resultado_perm.importances_mean, index=columnas).sort_values(ascending=False)
    print("\nImportancia por permutacion (reduccion de MSE al mezclar cada variable, en el periodo de prueba):")
    print(importancias.to_string())

    salida_dir = Path("../data/processed")
    tabla_busqueda.to_csv(salida_dir / f"gbm_v2_busqueda_hiperparametros_{args.objetivo}.csv", index=False)
    pd.Series(metricas_test).to_csv(salida_dir / f"gbm_v2_resultados_{args.objetivo}.csv", header=["valor"])
    importancias.to_csv(salida_dir / f"gbm_v2_importancias_{args.objetivo}.csv", header=["importancia"])
    df_pred.to_csv(salida_dir / f"gbm_v2_predicciones_{args.objetivo}.csv", index=False)
    print(f"\nGuardado en {salida_dir}/gbm_v2_*_{args.objetivo}.csv")


if __name__ == "__main__":
    main()
