"""
Consolida las tres fuentes de datos descargadas en Fase 1 (XM, IDEAM, CHIRPS)
en un único dataset diario, alineado por fecha, listo como punto de partida
para el modelo de predicción de caudal (Fase 2).

Fuentes de entrada (ya descargadas por los scripts de esta misma carpeta):
- data/raw/xm_aportes/aportes_caudal_guatape_nare.csv       (scripts/descargar_xm_aportes.py)
- data/raw/ideam_caudal/*.csv                                (scripts/descargar_ideam_caudal.py)
- data/raw/chirps_diario/precipitacion_diaria.csv            (scripts/descargar_chirps.py)
- data/raw/chirps_mensual/precipitacion_mensual.csv          (scripts/descargar_chirps_mensual.py)

Alcance temporal real del dataset consolidado: el diario queda acotado por
la fuente más corta, que es CHIRPS diario (2024-01-01 a 2026-08-31, con
~12 días de latencia de publicación al final del periodo — ver
docs/dataset-consolidado-fase1.md). XM e IDEAM tienen mucha más profundidad
histórica (desde 2000 y 1974 respectivamente) que aquí queda sin usar; para
un modelo que solo necesite caudal+precipitación mensual se puede extender
el rango usando data/raw/chirps_mensual en su lugar.

Uso:
    python consolidar_dataset_fase1.py --salida ../data/processed/dataset_fase1_diario.csv
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def cargar_xm(ruta: Path) -> dict:
    """fecha -> {rio: caudal_m3s}"""
    datos = defaultdict(dict)
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            datos[fila["fecha"]][f"xm_{fila['rio'].lower()}_m3s"] = float(fila["caudal_m3s"])
    return datos


def cargar_ideam(carpeta: Path) -> dict:
    """fecha -> {estacion: caudal_m3s}, una columna por archivo *-Q_MEDIA_D.csv encontrado"""
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
    xm = cargar_xm(raiz / "data/raw/xm_aportes/aportes_caudal_guatape_nare.csv")
    ideam = cargar_ideam(raiz / "data/raw/ideam_caudal")
    chirps = cargar_chirps_diario(raiz / "data/raw/chirps_diario/precipitacion_diaria.csv")

    # El rango util es la interseccion de las fechas con CHIRPS (la fuente mas corta)
    fechas = sorted(chirps.keys())
    print(f"Rango CHIRPS (fuente limitante): {fechas[0]} a {fechas[-1]} ({len(fechas)} dias)")

    columnas_ideam = sorted({col for d in ideam.values() for col in d})
    columnas_xm = sorted({col for d in xm.values() for col in d})
    columnas = ["fecha"] + columnas_xm + columnas_ideam + ["chirps_precip_mm"]

    filas_salida = []
    faltantes_xm = faltantes_chirps = 0
    for fecha in fechas:
        fila = {"fecha": fecha}
        fila.update(xm.get(fecha, {}))
        fila.update(ideam.get(fecha, {}))
        fila.update(chirps.get(fecha, {}))
        if not xm.get(fecha):
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
    print(f"Columnas: {columnas}")
    print(f"Dias sin dato XM en el rango: {faltantes_xm}")
    print(f"Dias sin dato CHIRPS en el rango: {faltantes_chirps}")
    for col in columnas_ideam:
        n_validos = sum(1 for fila in filas_salida if fila.get(col) is not None)
        print(f"  Cobertura {col}: {n_validos}/{len(filas_salida)} ({100*n_validos/len(filas_salida):.1f}%)")
    print(f"\nGuardado en: {salida}")


if __name__ == "__main__":
    main()
