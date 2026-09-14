"""
Modelo de picos de caudal (issue #3): clasificación de crecida + magnitud
condicional, en vez de una regresión directa sobre el valor absoluto.

Motivación (docs/modelo-gbm-caudal.md sección 8, confirmada de nuevo en
docs/dataset-extendido-2000-2026.md): los modelos de regresión directa
(persistencia y Gradient Boosting) subestiman sistemáticamente los picos
más extremos de caudal -- los árboles de decisión no pueden predecir
valores fuera del rango visto en entrenamiento, y son justamente esos
eventos los de mayor relevancia para prevenir crecidas o vaciados.

Diseño tipo "hurdle" (umbral), en dos etapas:
1. Clasificador binario: ¿el cambio de caudal de hoy a mañana será un
   evento de crecida? (|Δcaudal| > percentil 90 de |Δcaudal| EN EL
   PERÍODO DE ENTRENAMIENTO -- el umbral nunca se calcula sobre el test,
   para no filtrar información del futuro).
2. Regresor de magnitud, entrenado SOLO sobre los días de evento del
   entrenamiento (log1p del objetivo, igual que en modelo_gbm_regularizado.py
   -- ver docs/experimento-log-nare.md para la justificación).

Predicción final: si el clasificador predice evento, se usa el regresor
de magnitud; si no, se usa la persistencia simple -- que ya demostró ser
un baseline difícil de superar en días "normales" (docs/modelo-baseline-caudal.md).

Se evalúa por separado el desempeño (a) en todo el período de prueba y
(b) únicamente en los días que SÍ fueron eventos reales de crecida --
que es la pregunta que realmente le interesa a este experimento.

Uso:
    python modelo_picos_caudal.py --objetivo xm_guatape_m3s
    python modelo_picos_caudal.py --objetivo xm_nare_m3s
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

sys.path.insert(0, str(Path(__file__).parent))
from metricas_hidrologia import resumen_metricas
from modelo_gbm_caudal import COLUMNAS_IDEAM_USABLES, construir_features

COLUMNAS_PREDICTORAS = (
    ["q_hoy"]
    + [f"q_lag{l}" for l in (1, 2, 3)]
    + [f"precip_lag{l}" for l in (1, 2, 3)]
    + ["precip_hoy", "precip_acum3"]
    + [f"{c}_hoy" for c in COLUMNAS_IDEAM_USABLES]
    + [f"{c}_faltante" for c in COLUMNAS_IDEAM_USABLES]
    + ["mes_sin", "mes_cos"]
)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="../data/processed/dataset_fase1_diario.csv")
    ap.add_argument("--objetivo", default="xm_guatape_m3s")
    ap.add_argument("--frac-test", type=float, default=0.2)
    ap.add_argument("--percentil-evento", type=float, default=90.0, help="Percentil de |Δcaudal| que define un evento de crecida")
    args = ap.parse_args()

    df = pd.read_csv(args.dataset, parse_dates=["fecha"])
    df_feat = construir_features(df, args.objetivo)
    # delta_q: cambio real de caudal de HOY a MAÑANA (objetivo_t1 - q_hoy) -- define el
    # evento de crecida. Usar q_lag1 (ayer) aqui seria un error de un dia de desfase.
    df_feat["delta_q"] = df_feat["objetivo_t1"] - df_feat["q_hoy"]

    df_valido = df_feat.dropna(subset=COLUMNAS_PREDICTORAS + ["objetivo_t1", "delta_q"]).reset_index(drop=True)
    n = len(df_valido)
    corte = int(n * (1 - args.frac_test))
    train, test = df_valido.iloc[:corte], df_valido.iloc[corte:]
    print(f"Train: {train['fecha'].min().date()} a {train['fecha'].max().date()} ({len(train)} días)")
    print(f"Test:  {test['fecha'].min().date()} a {test['fecha'].max().date()} ({len(test)} días)\n")

    # Umbral de evento calculado SOLO con el periodo de entrenamiento
    umbral = train["delta_q"].abs().quantile(args.percentil_evento / 100)
    print(f"Umbral de evento (percentil {args.percentil_evento} de |delta_caudal| en train): {umbral:.2f} m3/s")

    train = train.copy()
    test = test.copy()
    train["evento"] = (train["delta_q"].abs() > umbral).astype(int)
    test["evento"] = (test["delta_q"].abs() > umbral).astype(int)
    print(f"Tasa de eventos en train: {train['evento'].mean():.3f} | en test: {test['evento'].mean():.3f}\n")

    # --- Etapa 1: clasificador de evento ---
    clasificador = HistGradientBoostingClassifier(max_iter=200, max_leaf_nodes=15, learning_rate=0.05, random_state=42)
    clasificador.fit(train[COLUMNAS_PREDICTORAS], train["evento"])
    pred_evento_test = clasificador.predict(test[COLUMNAS_PREDICTORAS])

    precision, recall, f1, _ = precision_recall_fscore_support(
        test["evento"], pred_evento_test, average="binary", zero_division=0
    )
    print("Desempeño del clasificador de eventos en test:")
    print(f"  Precisión: {precision:.3f}  Recall: {recall:.3f}  F1: {f1:.3f}")
    print(f"  Matriz de confusión [[TN,FP],[FN,TP]]:\n{confusion_matrix(test['evento'], pred_evento_test)}\n")

    # --- Etapa 2: regresor de magnitud, entrenado SOLO en eventos de train ---
    train_eventos = train[train["evento"] == 1]
    print(f"Filas de evento en train para entrenar el regresor de magnitud: {len(train_eventos)}")
    regresor_evento = HistGradientBoostingRegressor(
        max_iter=200, max_leaf_nodes=15, learning_rate=0.05, l2_regularization=1.0, random_state=42
    )
    regresor_evento.fit(train_eventos[COLUMNAS_PREDICTORAS], np.log1p(train_eventos["objetivo_t1"]))

    # --- Predicción combinada tipo "hurdle" ---
    pred_magnitud_si_evento = np.expm1(regresor_evento.predict(test[COLUMNAS_PREDICTORAS]))
    pred_persistencia = test["q_hoy"].values  # Q(t+1) = Q(t): persistencia real, no un dia atrasada
    pred_hurdle = np.where(pred_evento_test == 1, pred_magnitud_si_evento, pred_persistencia)

    # --- Evaluación: todo el periodo de prueba ---
    metricas_persistencia = resumen_metricas(test["objetivo_t1"].values, pred_persistencia)
    metricas_hurdle = resumen_metricas(test["objetivo_t1"].values, pred_hurdle)

    print("Métricas en TODO el período de prueba:")
    print(pd.DataFrame({"persistencia": metricas_persistencia, "modelo_picos": metricas_hurdle}).T.to_string())

    # --- Evaluación: SOLO los días que fueron eventos reales (la pregunta que importa) ---
    mask_eventos_reales = test["evento"].values == 1
    n_eventos_reales = mask_eventos_reales.sum()
    print(f"\nMétricas SOLO en los {n_eventos_reales} días que fueron eventos reales de crecida en test:")
    if n_eventos_reales > 5:
        metricas_persistencia_ev = resumen_metricas(test["objetivo_t1"].values[mask_eventos_reales], pred_persistencia[mask_eventos_reales])
        metricas_hurdle_ev = resumen_metricas(test["objetivo_t1"].values[mask_eventos_reales], pred_hurdle[mask_eventos_reales])
        print(pd.DataFrame({"persistencia": metricas_persistencia_ev, "modelo_picos": metricas_hurdle_ev}).T.to_string())
    else:
        print("  Muy pocos eventos reales en test para una métrica confiable.")

    # Guardar
    salida_dir = Path("../data/processed")
    df_out = test[["fecha", "objetivo_t1", "evento"]].copy()
    df_out["pred_evento"] = pred_evento_test
    df_out["pred_persistencia"] = pred_persistencia
    df_out["pred_hurdle"] = pred_hurdle
    df_out.to_csv(salida_dir / f"picos_predicciones_{args.objetivo}.csv", index=False)
    print(f"\nGuardado en {salida_dir}/picos_predicciones_{args.objetivo}.csv")


if __name__ == "__main__":
    main()
