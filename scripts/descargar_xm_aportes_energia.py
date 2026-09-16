"""
Descarga "Aportes Energía por Río" de XM — el equivalente energético
oficial (kWh) de los mismos aportes de caudal (m3/s) usados en Fase 2.

Por qué esta métrica y no una conversión propia caudal->energía: XM ya
publica el aporte convertido a energía usando su propio modelo hidráulico
oficial (cabeza, eficiencia de turbina, etc.), que es más confiable que
estimar un factor de conversión ad-hoc con los datos limitados de este
proyecto. Ver docs del motor de despacho (Fase 3, issue #11) para el
razonamiento completo.

MetricId: AporEner, Entity: Rio (mismo patrón de entidad por Name que
AporCaudal — no requiere el Code como los recursos "Gene"/"ObligEnerFirme").

Reutiliza el mismo hallazgo de descargar_xm_aportes.py: XM renombró la
entidad "NARE" a "NARE CP" entre 2023 y 2024 — se consultan ambos alias y
se consolidan bajo un nombre canónico.

Uso:
    python descargar_xm_aportes_energia.py --inicio 2000-01-01 \
        --fin 2026-09-12 --salida ../data/raw/xm_aportes_energia
"""

import argparse
import calendar
import csv
import time
from datetime import date
from pathlib import Path

import requests

API_URL = "https://servapibi.xm.com.co/daily"

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
    body = {"MetricId": "AporEner", "StartDate": desde.isoformat(), "EndDate": hasta.isoformat(), "Entity": "Rio", "Filter": alias_todos}
    resp = requests.post(API_URL, json=body, timeout=60)
    time.sleep(pausa)
    if resp.status_code != 200:
        print(f"  [AVISO] {desde} a {hasta}: HTTP {resp.status_code}")
        return []
    filas = []
    for item in resp.json().get("Items", []):
        fecha = item["Date"]
        for entidad in item.get("DailyEntities", []):
            filas.append({"fecha": fecha, "nombre_xm": entidad["Name"], "aporte_energia_kwh": entidad["Value"]})
    return filas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()

    inicio = date.fromisoformat(args.inicio)
    fin = date.fromisoformat(args.fin)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    alias_todos = [a for aliases in RIOS_CUENCA_GUATAPE.values() for a in aliases]
    alias_a_canonico = {a: c for c, aliases in RIOS_CUENCA_GUATAPE.items() for a in aliases}

    todas_filas = []
    meses = list(rangos_mensuales(inicio, fin))
    for i, (desde, hasta) in enumerate(meses, 1):
        print(f"[{i}/{len(meses)}] {desde} a {hasta}...")
        todas_filas.extend(consultar_mes(desde, hasta, alias_todos))

    por_canonico_fecha = {}
    solapes = []
    for f in todas_filas:
        canonico = alias_a_canonico[f["nombre_xm"]]
        clave = (canonico, f["fecha"])
        if clave in por_canonico_fecha:
            solapes.append(clave)
        por_canonico_fecha[clave] = {"fecha": f["fecha"], "rio": canonico, "aporte_energia_kwh": f["aporte_energia_kwh"], "nombre_xm_original": f["nombre_xm"]}

    if solapes:
        print(f"\n[AVISO] {len(solapes)} fechas con datos duplicados entre alias del mismo rio.")

    filas = sorted(por_canonico_fecha.values(), key=lambda r: (r["rio"], r["fecha"]))
    csv_path = salida / "aportes_energia_guatape_nare.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", "rio", "aporte_energia_kwh", "nombre_xm_original"])
        w.writeheader()
        w.writerows(filas)

    print(f"\nListo. {len(filas)} registros guardados en: {csv_path}")
    for canonico in RIOS_CUENCA_GUATAPE:
        valores = [f["aporte_energia_kwh"] for f in filas if f["rio"] == canonico]
        if valores:
            fechas = sorted(f["fecha"] for f in filas if f["rio"] == canonico)
            print(f"  {canonico}: {len(valores)} registros ({fechas[0]} a {fechas[-1]})")
        else:
            print(f"  {canonico}: sin datos en el rango consultado")


if __name__ == "__main__":
    main()
