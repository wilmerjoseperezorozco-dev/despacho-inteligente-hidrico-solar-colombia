"""
Consolida los datos reales de Fase 3 (volumen del embalse, aportes en
energía, obligación de energía firme — todos de XM) junto con los tres
escenarios de generación solar flotante simulada, en un único dataset
listo para el motor de despacho (src/motor_despacho.py).

A diferencia del dataset de Fase 1 (que se limita al rango de CHIRPS),
aquí el rango efectivo lo determina la intersección de las series XM
descargadas (issue #9), que ya cubren 2000-2026 igual que el resto del
proyecto.

Uso:
    python consolidar_dataset_fase3.py --salida ../data/processed/dataset_fase3_despacho.csv
"""

import argparse
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).parent.parent


def cargar_volumen() -> pd.DataFrame:
    vol = pd.read_csv(RAIZ / "data/raw/xm_embalse_generacion/voluutildiarener.csv", parse_dates=["fecha"])
    porc = pd.read_csv(RAIZ / "data/raw/xm_embalse_generacion/porcvoluutildiar.csv", parse_dates=["fecha"])
    return vol.merge(porc, on="fecha", how="outer")


def cargar_obligacion_generacion() -> pd.DataFrame:
    oblig = pd.read_csv(RAIZ / "data/raw/xm_embalse_generacion/obligenerfirme.csv", parse_dates=["fecha"])
    gene = pd.read_csv(RAIZ / "data/raw/xm_embalse_generacion/gene_guatape_diario.csv", parse_dates=["fecha"])
    return oblig.merge(gene, on="fecha", how="outer")


def cargar_aportes_energia() -> pd.DataFrame:
    df = pd.read_csv(RAIZ / "data/raw/xm_aportes_energia/aportes_energia_guatape_nare.csv", parse_dates=["fecha"])
    pivote = df.pivot_table(index="fecha", columns="rio", values="aporte_energia_kwh", aggfunc="first")
    pivote.columns = [f"aporte_energia_{c.lower()}_kwh" for c in pivote.columns]
    return pivote.reset_index()


def cargar_solar() -> pd.DataFrame:
    return pd.read_csv(RAIZ / "data/processed/solar_flotante_escenarios.csv", parse_dates=["fecha"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()

    volumen = cargar_volumen()
    oblig_gene = cargar_obligacion_generacion()
    aportes = cargar_aportes_energia()
    solar = cargar_solar()

    df = volumen.merge(oblig_gene, on="fecha", how="inner").merge(aportes, on="fecha", how="inner").merge(solar, on="fecha", how="inner")
    df = df.sort_values("fecha").reset_index(drop=True)

    filas_totales = len(df)
    filas_con_huecos = df.isna().any(axis=1).sum()
    print(f"Filas consolidadas: {filas_totales} ({df['fecha'].min().date()} a {df['fecha'].max().date()})")
    print(f"Filas con al menos un valor faltante: {filas_con_huecos} ({filas_con_huecos / filas_totales:.1%})")

    df.to_csv(args.salida, index=False)
    print(f"Guardado en: {args.salida}")


if __name__ == "__main__":
    main()
