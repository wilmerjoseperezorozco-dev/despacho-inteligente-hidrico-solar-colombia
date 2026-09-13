"""
Modelo baseline de predicción de caudal a 1 día (Fase 2, primer modelo).

Objetivo: establecer el punto de comparación honesto antes de probar cualquier
modelo de machine learning — sin esto, no hay forma de saber si un modelo más
complejo realmente mejora algo (ver docs/arquitectura-y-benchmarking.md).

Dos baselines evaluados:
1. Persistencia ingenua: Q(t+1) = Q(t) — el caudal de hoy es la mejor
   predicción de mañana. Es el baseline estándar en pronóstico de caudal
   diario porque el caudal tiene autocorrelación muy alta día a día.
2. Climatología expandida: Q(t+1) = media de todos los días anteriores a t
   (recalculada cada día, sin usar el futuro) — el "no sabemos nada del día
   específico, solo el promedio histórico hasta ahora".

Validación: walk-forward con ventana expandida, NO split aleatorio (una
serie de tiempo con split aleatorio infla artificialmente el desempeño
porque el modelo "ve" información adyacente al punto de prueba).

Métricas: NSE, KGE (+ sus 3 componentes), RMSE, MAE, PBIAS — ver
src/metricas_hidrologia.py y la justificación en
docs/arquitectura-y-benchmarking.md (no solo RMSE/MSE genérico).

Uso:
    python modelo_baseline_caudal.py --objetivo xm_guatape_m3s
    python modelo_baseline_caudal.py --objetivo xm_nare_m3s
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from metricas_hidrologia import resumen_metricas


def cargar_serie(ruta_csv: Path, columna_objetivo: str) -> pd.Series:
    df = pd.read_csv(ruta_csv, parse_dates=["fecha"])
    df = df.sort_values("fecha").set_index("fecha")
    serie = df[columna_objetivo].dropna()
    return serie


def walk_forward_persistencia(serie: pd.Series, inicio_test: int) -> pd.DataFrame:
    """Q_pred(t) = Q_obs(t-1). Sin entrenamiento -- disponible desde el segundo dato."""
    obs = serie.values
    pred = np.roll(obs, 1)
    df = pd.DataFrame({"fecha": serie.index, "obs": obs, "pred_persistencia": pred})
    return df.iloc[inicio_test:].reset_index(drop=True)


def walk_forward_climatologia(serie: pd.Series, inicio_test: int) -> pd.DataFrame:
    """Q_pred(t) = media de obs[0:t] (ventana expandida, sin ver el futuro)."""
    obs = serie.values
    medias_expandidas = pd.Series(obs).expanding().mean().shift(1).values  # media de todo lo anterior a t
    df = pd.DataFrame({"fecha": serie.index, "obs": obs, "pred_climatologia": medias_expandidas})
    return df.iloc[inicio_test:].reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dataset",
        default="../data/processed/dataset_fase1_diario.csv",
        help="Ruta al dataset consolidado de Fase 1",
    )
    ap.add_argument("--objetivo", default="xm_guatape_m3s", help="Columna objetivo a predecir")
    ap.add_argument("--frac-test", type=float, default=0.2, help="Fracción final de la serie usada como test")
    ap.add_argument("--salida", default="../data/processed/baseline_resultados.csv")
    args = ap.parse_args()

    ruta = Path(args.dataset)
    serie = cargar_serie(ruta, args.objetivo)
    print(f"Serie objetivo: {args.objetivo}")
    print(f"Rango: {serie.index.min().date()} a {serie.index.max().date()} ({len(serie)} días con dato)")

    inicio_test = int(len(serie) * (1 - args.frac_test))
    fecha_corte = serie.index[inicio_test]
    print(f"Corte train/test (walk-forward): test empieza en {fecha_corte.date()} ({len(serie) - inicio_test} días de test)\n")

    df_persist = walk_forward_persistencia(serie, inicio_test)
    df_clima = walk_forward_climatologia(serie, inicio_test)

    resultados = {}
    resultados["persistencia"] = resumen_metricas(df_persist["obs"], df_persist["pred_persistencia"])
    resultados["climatologia_expandida"] = resumen_metricas(df_clima["obs"], df_clima["pred_climatologia"])

    tabla = pd.DataFrame(resultados).T
    tabla.index.name = "modelo"
    print(tabla.to_string())

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(salida)
    print(f"\nResultados guardados en: {salida}")

    # Guardar tambien las predicciones dia a dia para inspeccion/graficacion posterior
    df_pred = df_persist.merge(df_clima[["fecha", "pred_climatologia"]], on="fecha")
    ruta_pred = salida.parent / f"baseline_predicciones_{args.objetivo}.csv"
    df_pred.to_csv(ruta_pred, index=False)
    print(f"Predicciones día a día guardadas en: {ruta_pred}")

    mejor = tabla["nse"].astype(float).idxmax()
    print(f"\nMejor baseline por NSE: {mejor} (NSE={tabla.loc[mejor, 'nse']})")
    if tabla.loc["persistencia", "nse"] < 0:
        print(
            "AVISO: NSE de persistencia < 0 significa que ni siquiera supera predecir la media -- "
            "revisar si hay algo inusual en la serie antes de confiar en cualquier modelo mas complejo."
        )


if __name__ == "__main__":
    main()
