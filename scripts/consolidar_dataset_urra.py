"""
Consolida las fuentes de datos descargadas para la réplica en Urrá I
(issue #14) en un único dataset diario, análogo a
consolidar_dataset_fase1.py pero para un solo río (Sinú), no dos.

Fuentes de entrada:
- data/raw/xm_urra/aporcaudal.csv          (objetivo del modelo, m3/s)
- data/raw/xm_urra/aporener.csv            (equivalente en energía, para Fase 3)
- data/raw/ideam_caudal_urra/*.csv         (predictor tributario; solo CARRIZOLA
                                             cubre 2000-2026, ver docs/urra-fase1-datos.md)
- data/raw/chirps_urra/precipitacion_diaria.csv

El rango útil queda acotado por CHIRPS (la fuente más corta), igual
criterio que en Guatapé.

Uso:
    python consolidar_dataset_urra.py --salida ../data/processed/dataset_urra_diario.csv
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def cargar_xm_caudal(ruta: Path) -> dict:
    datos = {}
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            datos[fila["fecha"]] = {"xm_urra_m3s": float(fila["caudal_m3s"])}
    return datos


def cargar_xm_energia(ruta: Path) -> dict:
    datos = {}
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            datos[fila["fecha"]] = {"xm_urra_aporte_energia_kwh": float(fila["aporte_energia_kwh"])}
    return datos


def cargar_ideam(carpeta: Path) -> dict:
    datos = defaultdict(dict)
    for ruta in sorted(carpeta.glob("*-Q_MEDIA_D.csv")):
        codigo = ruta.name.replace("-Q_MEDIA_D.csv", "")
        with open(ruta, encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                fecha = fila["fechaObservacion"][:10]
                if fila["valorObservado"]:
                    datos[fecha][f"ideam_{codigo}_m3s"] = float(fila["valorObservado"])
    return datos


def cargar_chirps_diario(ruta: Path) -> dict:
    datos = {}
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            datos[fila["fecha"]] = {"chirps_precip_mm": float(fila["precip_media_mm"])}
    return datos


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raiz", default="..", help="Carpeta raiz del repo (default: ..)")
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()

    raiz = Path(args.raiz)
    xm_caudal = cargar_xm_caudal(raiz / "data/raw/xm_urra/aporcaudal.csv")
    xm_energia = cargar_xm_energia(raiz / "data/raw/xm_urra/aporener.csv")
    ideam = cargar_ideam(raiz / "data/raw/ideam_caudal_urra")
    chirps = cargar_chirps_diario(raiz / "data/raw/chirps_urra/precipitacion_diaria.csv")

    fechas = sorted(chirps.keys())
    print(f"Rango CHIRPS (fuente limitante): {fechas[0]} a {fechas[-1]} ({len(fechas)} dias)")

    columnas_ideam = sorted({col for d in ideam.values() for col in d})
    columnas = ["fecha", "xm_urra_m3s", "xm_urra_aporte_energia_kwh"] + columnas_ideam + ["chirps_precip_mm"]

    filas_salida = []
    faltantes_xm = faltantes_chirps = 0
    for fecha in fechas:
        fila = {"fecha": fecha}
        fila.update(xm_caudal.get(fecha, {}))
        fila.update(xm_energia.get(fecha, {}))
        fila.update(ideam.get(fecha, {}))
        fila.update(chirps.get(fecha, {}))
        if not xm_caudal.get(fecha):
            faltantes_xm += 1
        if not chirps.get(fecha):
            faltantes_chirps += 1
        filas_salida.append(fila)

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas_salida)

    print(f"\nDataset consolidado: {len(filas_salida)} filas, {len(columnas)} columnas")
    print(f"Dias sin dato XM (caudal) en el rango: {faltantes_xm}")
    print(f"Dias sin dato CHIRPS en el rango: {faltantes_chirps}")
    for col in columnas_ideam:
        n_validos = sum(1 for fila in filas_salida if fila.get(col) is not None)
        print(f"  Cobertura {col}: {n_validos}/{len(filas_salida)} ({100*n_validos/len(filas_salida):.1f}%)")
    print(f"\nGuardado en: {salida}")


if __name__ == "__main__":
    main()
