"""
Descarga las series operativas reales del embalse Peñol y de la Central
Guatapé necesarias para el motor de despacho de Fase 3 — misma API pública
de XM ya usada en descargar_xm_aportes.py (sin autenticación).

Métricas confirmadas contra el catálogo oficial de XM
(EquipoAnaliticaXM/API_XM, pydataxm/metricasAPI.json) y contra el listado
real de embalses/recursos (endpoint Lists):

    VoluUtilDiarEner  Embalse=PENOL   Diaria   Volumen útil, en energía (kWh crudo de la API)
    PorcVoluUtilDiar  Embalse=PENOL   Diaria   Volumen útil como fracción 0-1 (no 0-100)
    Gene              Recurso=GTPE    Horaria  Generación real (kWh)
    ObligEnerFirme    Recurso=GTPE    Diaria   Obligación Energía Firme (kWh)

UNIDADES (verificadas, no asumidas): la API no documenta unidades en la
respuesta. Se confirmó que "VoluUtilDiarEner"/"Gene"/"ObligEnerFirme"
vienen en kWh crudos comparando el agregado "Sistema" de VoluUtilDiarEner
(13.553.260.500 -> 13.553 GWh) contra el nivel de embalses agregado del
país que XM reporta públicamente (~13.500 GWh en ene-2026) — coinciden.
Dividir por 1e6 para obtener GWh. "PorcVoluUtilDiar" es una fracción
(0.949 = 94.9%), no un porcentaje ya multiplicado por 100.

El embalse se llama "PENOL" y la central asociada es el recurso "GUATAPE"
(código GTPE, EPM, hidráulica, en operación desde 1972) — verificado vía
POST https://servapibi.xm.com.co/Lists con MetricId=ListadoEmbalses y
ListadoRecursos. No confundir con el recurso "PLAYAS", la central aguas
abajo que reutiliza el mismo caudal turbinado.

HALLAZGO REAL (2026-09-16, probado con curl antes de programar el
parseo): para la entidad "Embalse" el filtro usa el Name ("PENOL"), pero
para la entidad "Recurso" el filtro debe ir por el Code ("GTPE"), no por
el Name ("GUATAPE") — usar el Name ahí devuelve Items vacíos sin error.
Además, la respuesta horaria de "Gene" no trae una lista "HourlyValues"
sino un diccionario "Values" con claves "Hour01".."Hour24" más una clave
"code" que no es un valor numérico. Algunas horas faltantes vienen como
cadena vacía "" en vez de null — encontrado en producción (2026-09-16)
al toparse con un ValueError en el primer mes de 2000, no anticipado.

Ver issue #9 para el contexto completo.

Uso:
    python descargar_xm_embalse_generacion.py --inicio 2000-01-01 \
        --fin 2026-09-12 --salida ../data/raw/xm_embalse_generacion
"""

import argparse
import calendar
import csv
from datetime import date
from pathlib import Path

import requests
import time

API_BASE = "https://servapibi.xm.com.co"

METRICAS_DIARIAS = {
    "VoluUtilDiarEner": {"entity": "Embalse", "filtro": ["PENOL"], "columna": "volumen_util_kwh"},
    "PorcVoluUtilDiar": {"entity": "Embalse", "filtro": ["PENOL"], "columna": "volumen_util_pct"},
    "ObligEnerFirme": {"entity": "Recurso", "filtro": ["GTPE"], "columna": "obligacion_energia_firme_kwh"},
}

METRICA_HORARIA = {"id": "Gene", "entity": "Recurso", "filtro": ["GTPE"], "columna": "generacion_kwh"}


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


def ya_procesados(csv_path: Path, columna_fecha: str = "fecha") -> set:
    if not csv_path.exists():
        return set()
    with open(csv_path, encoding="utf-8") as f:
        return {row[columna_fecha] for row in csv.DictReader(f)}


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


def consultar_horaria(metric_id: str, entity: str, filtro: list, desde: date, hasta: date, pausa: float = 0.3) -> list:
    body = {"MetricId": metric_id, "StartDate": desde.isoformat(), "EndDate": hasta.isoformat(), "Entity": entity, "Filter": filtro}
    resp = requests.post(f"{API_BASE}/hourly", json=body, timeout=60)
    time.sleep(pausa)
    if resp.status_code != 200:
        print(f"  [AVISO] {metric_id} {desde} a {hasta}: HTTP {resp.status_code}")
        return []
    filas = []
    for item in resp.json().get("Items", []):
        fecha = item["Date"]
        for entidad in item.get("HourlyEntities", []):
            valores = entidad.get("Values", {})
            horas = [float(v) for k, v in valores.items() if k.lower().startswith("hour") and v not in (None, "")]
            if not horas:
                continue
            filas.append({"fecha": fecha, "generacion_diaria_kwh": sum(horas)})
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


def descargar_generacion_horaria(inicio: date, fin: date, salida: Path):
    csv_path = salida / "gene_guatape_diario.csv"
    procesadas = ya_procesados(csv_path)
    meses = list(rangos_mensuales(inicio, fin))
    escribir_encabezado = not csv_path.exists()
    cfg = METRICA_HORARIA
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", cfg["columna"]])
        if escribir_encabezado:
            w.writeheader()
        for i, (desde, hasta) in enumerate(meses, 1):
            if desde.isoformat() in procesadas and hasta.isoformat() in procesadas:
                continue
            print(f"[Gene] [{i}/{len(meses)}] {desde} a {hasta}...")
            filas = consultar_horaria(cfg["id"], cfg["entity"], cfg["filtro"], desde, hasta)
            for fila in filas:
                if fila["fecha"] in procesadas:
                    continue
                w.writerow({"fecha": fila["fecha"], cfg["columna"]: fila["generacion_diaria_kwh"]})
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

    for metric_id, cfg in METRICAS_DIARIAS.items():
        descargar_metrica_diaria(metric_id, cfg, inicio, fin, salida)

    descargar_generacion_horaria(inicio, fin, salida)

    print("\nListo.")


if __name__ == "__main__":
    main()
