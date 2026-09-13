"""
Descarga la serie oficial de "Aportes Caudal por Río" de XM (operador del
Sistema Interconectado Nacional colombiano) — la misma métrica que XM usa
operativamente para el despacho hídrico del país.

API pública sin autenticación, descubierta a partir del repositorio oficial
EquipoAnaliticaXM/API_XM (paquete pydataxm):
    https://github.com/EquipoAnaliticaXM/API_XM

Endpoint: POST https://servapibi.xm.com.co/daily
Body: {"MetricId": "AporCaudal", "StartDate": "...", "EndDate": "...",
       "Entity": "Rio", "Filter": ["GUATAPE", "NARE CP"]}

Probado end-to-end el 2026-09-13. Series confirmadas para los ríos GUATAPE
y NARE (las corrientes que alimentan directamente el embalse Peñol-Guatapé),
con datos disponibles desde el año 2000 hasta el presente (26+ años).

HALLAZGO IMPORTANTE (2026-09-13): XM renombró la entidad "NARE" a "NARE CP"
entre finales de 2023 y comienzos de 2024 — ambos nombres se refieren al
mismo río, en periodos distintos. Este script consulta ambos alias y los
consolida bajo un único nombre canónico para obtener una serie continua.
No se encontró un glosario oficial de XM que documente el cambio de nombre;
se infirió comparando la disponibilidad de datos año por año.

IMPORTANTE: la API solo acepta rangos de hasta ~31 días por solicitud (igual
que la librería oficial pydataxm) — este script fragmenta automáticamente
por mes calendario.

Uso:
    python descargar_xm_aportes.py --inicio 2000-01-01 --fin 2026-09-12 \
        --salida ../data/raw/xm_aportes
"""

import argparse
import calendar
import csv
import time
from datetime import date
from pathlib import Path

import requests

API_URL = "https://servapibi.xm.com.co/daily"

# Nombre canónico -> alias históricos usados por XM para la misma corriente.
# NARE/NARE CP: XM renombró la entidad entre finales de 2023 y comienzos de 2024
# (verificado por disponibilidad de datos, no por un glosario oficial).
RIOS_CUENCA_GUATAPE = {
    "GUATAPE": ["GUATAPE"],
    "NARE": ["NARE", "NARE CP"],
}


def rangos_mensuales(inicio: date, fin: date):
    actual = date(inicio.year, inicio.month, 1)
    while actual <= fin:
        ultimo_dia = calendar.monthrange(actual.year, actual.month)[1]
        fin_mes = date(actual.year, actual.month, ultimo_dia)
        desde = max(actual, inicio)
        hasta = min(fin_mes, fin)
        yield desde, hasta
        if actual.month == 12:
            actual = date(actual.year + 1, 1, 1)
        else:
            actual = date(actual.year, actual.month + 1, 1)


def consultar_mes(desde: date, hasta: date, alias_todos: list, pausa: float = 0.3) -> list:
    body = {
        "MetricId": "AporCaudal",
        "StartDate": desde.isoformat(),
        "EndDate": hasta.isoformat(),
        "Entity": "Rio",
        "Filter": alias_todos,
    }
    resp = requests.post(API_URL, json=body, timeout=60)
    time.sleep(pausa)  # no saturar la API pública de XM
    if resp.status_code != 200:
        print(f"  [AVISO] {desde} a {hasta}: HTTP {resp.status_code}")
        return []
    data = resp.json()
    filas = []
    for item in data.get("Items", []):
        fecha = item["Date"]
        for entidad in item.get("DailyEntities", []):
            filas.append({"fecha": fecha, "nombre_xm": entidad["Name"], "caudal_m3s": entidad["Value"]})
    return filas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inicio", required=True, help="Fecha inicio YYYY-MM-DD")
    ap.add_argument("--fin", required=True, help="Fecha fin YYYY-MM-DD")
    ap.add_argument("--salida", required=True, help="Carpeta de salida")
    args = ap.parse_args()

    inicio = date.fromisoformat(args.inicio)
    fin = date.fromisoformat(args.fin)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    alias_todos = [alias for aliases in RIOS_CUENCA_GUATAPE.values() for alias in aliases]
    alias_a_canonico = {alias: canonico for canonico, aliases in RIOS_CUENCA_GUATAPE.items() for alias in aliases}

    todas_filas = []
    meses = list(rangos_mensuales(inicio, fin))
    for i, (desde, hasta) in enumerate(meses, 1):
        print(f"[{i}/{len(meses)}] Consultando {desde} a {hasta}...")
        todas_filas.extend(consultar_mes(desde, hasta, alias_todos))

    # Consolidar alias bajo el nombre canonico, detectando solapes reales (no deberian existir)
    por_canonico_fecha = {}
    solapes = []
    for f in todas_filas:
        canonico = alias_a_canonico[f["nombre_xm"]]
        clave = (canonico, f["fecha"])
        if clave in por_canonico_fecha:
            solapes.append(clave)
        por_canonico_fecha[clave] = {"fecha": f["fecha"], "rio": canonico, "caudal_m3s": f["caudal_m3s"], "nombre_xm_original": f["nombre_xm"]}

    if solapes:
        print(f"\n[AVISO] Se encontraron {len(solapes)} fechas con datos duplicados entre alias del mismo rio — revisar antes de usar la serie.")

    filas_consolidadas = sorted(por_canonico_fecha.values(), key=lambda r: (r["rio"], r["fecha"]))

    csv_path = salida / "aportes_caudal_guatape_nare.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", "rio", "caudal_m3s", "nombre_xm_original"])
        w.writeheader()
        w.writerows(filas_consolidadas)

    print(f"\nListo. {len(filas_consolidadas)} registros guardados en: {csv_path}")
    for canonico in RIOS_CUENCA_GUATAPE:
        valores = [f["caudal_m3s"] for f in filas_consolidadas if f["rio"] == canonico]
        if valores:
            fechas = sorted(f["fecha"] for f in filas_consolidadas if f["rio"] == canonico)
            print(
                f"  {canonico}: {len(valores)} registros ({fechas[0]} a {fechas[-1]}), "
                f"min={min(valores):.2f} max={max(valores):.2f} media={sum(valores)/len(valores):.2f} m3/s"
            )
        else:
            print(f"  {canonico}: sin datos en el rango consultado")


if __name__ == "__main__":
    main()
