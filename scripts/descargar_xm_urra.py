"""
Descarga todas las series de XM necesarias para replicar el framework de
despacho hídrico-solar en el embalse Urrá I (río Sinú, Córdoba) — issue #14.

A diferencia de Guatapé (dos ríos, Nare+Guatapé), Urrá es un sistema de
un solo río, lo que simplifica el pipeline: un único script consolidado
en vez de tres separados.

Entidades confirmadas contra el catálogo real de XM (verificado con
curl antes de programar el parseo, mismo método que en Guatapé):

    Rio     "SINU URRA"   (AporCaudal, AporEner — filtro por Name)
    Embalse "URRA1"       (VoluUtilDiarEner, PorcVoluUtilDiar — filtro por Name)
    Recurso "URA1"        (Gene, ObligEnerFirme — hidráulica, filtro por Code)
    Recurso "PSUA"        (Gene — PARQUE SOLAR URRA, filtro por Code)

HALLAZGO IMPORTANTE: "PSUA" (Parque Solar Urrá) está registrado en XM como
recurso DESPACHADO CENTRALMENTE desde 2025-01-31 (estado "PRUEBAS" al
momento de esta descarga) — es, con alta probabilidad, el proyecto
Aquasol integrado al mercado eléctrico. Esto significa que para Urrá,
a diferencia de Guatapé, existe generación solar REAL medida (aunque
con un historial corto, desde mediados de 2026) que puede usarse para
calibrar/validar el modelo de generación FV simulado en vez de depender
solo de irradiancia — ver docs correspondientes del issue #14.

Uso:
    python descargar_xm_urra.py --inicio 2000-01-01 --fin 2026-09-12 \
        --salida ../data/raw/xm_urra
"""

import argparse
import calendar
import csv
import time
from datetime import date
from pathlib import Path

import requests

API_BASE = "https://servapibi.xm.com.co"

METRICAS_DIARIAS_RIO = {
    "AporCaudal": {"entity": "Rio", "filtro": ["SINU URRA"], "columna": "caudal_m3s"},
    "AporEner": {"entity": "Rio", "filtro": ["SINU URRA"], "columna": "aporte_energia_kwh"},
}

METRICAS_DIARIAS_EMBALSE = {
    "VoluUtilDiarEner": {"entity": "Embalse", "filtro": ["URRA1"], "columna": "volumen_util_kwh"},
    "PorcVoluUtilDiar": {"entity": "Embalse", "filtro": ["URRA1"], "columna": "volumen_util_pct"},
}

METRICA_OBLIGACION = {"entity": "Recurso", "filtro": ["URA1"], "columna": "obligacion_energia_firme_kwh"}

METRICAS_HORARIAS = {
    "gene_urra1_hidraulica": {"filtro": ["URA1"], "columna": "generacion_hidraulica_kwh"},
    "gene_psua_solar_real": {"filtro": ["PSUA"], "columna": "generacion_solar_real_kwh"},
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


def ya_procesados(csv_path: Path) -> set:
    if not csv_path.exists():
        return set()
    with open(csv_path, encoding="utf-8") as f:
        return {row["fecha"] for row in csv.DictReader(f)}


def consultar_diaria(metric_id: str, entity: str, filtro: list, desde: date, hasta: date, pausa: float = 0.3) -> list:
    body = {"MetricId": metric_id, "StartDate": desde.isoformat(), "EndDate": hasta.isoformat(), "Entity": entity, "Filter": filtro}
    resp = requests.post(f"{API_BASE}/daily", json=body, timeout=60)
    time.sleep(pausa)
    if resp.status_code != 200:
        print(f"  [AVISO] {metric_id} {desde} a {hasta}: HTTP {resp.status_code}")
        return []
    filas = []
    for item in resp.json().get("Items", []):
        fecha = item["Date"]
        for entidad in item.get("DailyEntities", []):
            filas.append({"fecha": fecha, "valor": entidad["Value"]})
    return filas


def consultar_horaria(filtro: list, desde: date, hasta: date, pausa: float = 0.3) -> list:
    body = {"MetricId": "Gene", "StartDate": desde.isoformat(), "EndDate": hasta.isoformat(), "Entity": "Recurso", "Filter": filtro}
    resp = requests.post(f"{API_BASE}/hourly", json=body, timeout=60)
    time.sleep(pausa)
    if resp.status_code != 200:
        print(f"  [AVISO] Gene {filtro} {desde} a {hasta}: HTTP {resp.status_code}")
        return []
    filas = []
    for item in resp.json().get("Items", []):
        fecha = item["Date"]
        for entidad in item.get("HourlyEntities", []):
            valores = entidad.get("Values", {})
            horas = [float(v) for k, v in valores.items() if k.lower().startswith("hour") and v not in (None, "")]
            filas.append({"fecha": fecha, "total_diario": sum(horas) if horas else 0.0})
    return filas


def descargar_metrica_diaria(metric_id: str, cfg: dict, inicio: date, fin: date, salida: Path):
    csv_path = salida / f"{metric_id.lower()}.csv"
    procesadas = ya_procesados(csv_path)
    meses = list(rangos_mensuales(inicio, fin))
    escribir_encabezado = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", cfg["columna"]])
        if escribir_encabezado:
            w.writeheader()
        for i, (desde, hasta) in enumerate(meses, 1):
            if desde.isoformat() in procesadas and hasta.isoformat() in procesadas:
                continue
            print(f"[{metric_id}] [{i}/{len(meses)}] {desde} a {hasta}...")
            filas = consultar_diaria(metric_id, cfg["entity"], cfg["filtro"], desde, hasta)
            for fila in filas:
                if fila["fecha"] in procesadas:
                    continue
                w.writerow({"fecha": fila["fecha"], cfg["columna"]: fila["valor"]})
                procesadas.add(fila["fecha"])
            f.flush()
    print(f"  -> {csv_path} ({len(procesadas)} fechas)")


def descargar_metrica_horaria(nombre_salida: str, cfg: dict, inicio: date, fin: date, salida: Path):
    csv_path = salida / f"{nombre_salida}.csv"
    procesadas = ya_procesados(csv_path)
    meses = list(rangos_mensuales(inicio, fin))
    escribir_encabezado = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", cfg["columna"]])
        if escribir_encabezado:
            w.writeheader()
        for i, (desde, hasta) in enumerate(meses, 1):
            if desde.isoformat() in procesadas and hasta.isoformat() in procesadas:
                continue
            print(f"[{nombre_salida}] [{i}/{len(meses)}] {desde} a {hasta}...")
            filas = consultar_horaria(cfg["filtro"], desde, hasta)
            for fila in filas:
                if fila["fecha"] in procesadas:
                    continue
                w.writerow({"fecha": fila["fecha"], cfg["columna"]: fila["total_diario"]})
                procesadas.add(fila["fecha"])
            f.flush()
    print(f"  -> {csv_path} ({len(procesadas)} fechas)")


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

    for metric_id, cfg in METRICAS_DIARIAS_RIO.items():
        descargar_metrica_diaria(metric_id, cfg, inicio, fin, salida)
    for metric_id, cfg in METRICAS_DIARIAS_EMBALSE.items():
        descargar_metrica_diaria(metric_id, cfg, inicio, fin, salida)
    descargar_metrica_diaria("ObligEnerFirme", METRICA_OBLIGACION, inicio, fin, salida)
    for nombre_salida, cfg in METRICAS_HORARIAS.items():
        descargar_metrica_horaria(nombre_salida, cfg, inicio, fin, salida)

    print("\nListo.")


if __name__ == "__main__":
    main()
