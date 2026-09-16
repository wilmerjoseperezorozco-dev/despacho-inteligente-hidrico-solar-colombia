"""
Descarga irradiancia solar diaria en el punto del embalse Peñol-Guatapé,
insumo real para simular la generación fotovoltaica flotante de Fase 3.

IMPORTANTE (ver issue #10): no existe hoy un proyecto real de solar flotante
en este embalse. Esta serie es la base física real (irradiancia observada
por satélite/reanálisis) sobre la que luego se simula un escenario de
generación FV — el escenario es hipotético, la irradiancia no.

Fuente: NASA POWER (Prediction Of Worldwide Energy Resources),
power.larc.nasa.gov — API pública sin autenticación, cobertura 1981-presente.
Verificado end-to-end el 2026-09-16 para el punto de la Presa Santa Rita
(6.2611, -75.1900), mismo punto usado en la delineación de cuenca de Fase 1.

Parámetros descargados:
    ALLSKY_SFC_SW_DWN   Irradiancia global horizontal real (kWh/m2/dia)
    CLRSKY_SFC_SW_DWN   Irradiancia en cielo despejado (kWh/m2/dia) — techo teorico
    T2M                 Temperatura a 2m (C) — para el derateo termico del panel

A diferencia de CHIRPS/XM, esta API no tiene límite de rango por solicitud
documentado en la práctica; aun así se descarga por bloques anuales para
poder reanudar si se interrumpe.

Reutilizable para otros embalses vía --lat/--lon/--nombre (usado por primera
vez el 2026-09-16 para el embalse Urrá I, río Sinú — issue #14).

Uso:
    python descargar_solar_power.py --inicio 2000-01-01 --fin 2026-08-31 \
        --salida ../data/raw/solar_power
    python descargar_solar_power.py --inicio 2000-01-01 --fin 2026-08-31 \
        --lat 7.94 --lon -76.29 --nombre urra --salida ../data/raw/solar_power_urra
"""

import argparse
import csv
from datetime import date
from pathlib import Path

import requests

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
LAT_DEFAULT, LON_DEFAULT = 6.2611, -75.1900  # Presa Santa Rita, embalse Peñol-Guatapé
PARAMETROS = ["ALLSKY_SFC_SW_DWN", "CLRSKY_SFC_SW_DWN", "T2M"]


def rangos_anuales(inicio: date, fin: date):
    for anio in range(inicio.year, fin.year + 1):
        desde = date(anio, 1, 1) if anio != inicio.year else inicio
        hasta = date(anio, 12, 31) if anio != fin.year else fin
        yield desde, hasta


def ya_procesados(csv_path: Path) -> set:
    if not csv_path.exists():
        return set()
    with open(csv_path, encoding="utf-8") as f:
        return {row["fecha"] for row in csv.DictReader(f)}


def consultar_anio(desde: date, hasta: date, lat: float, lon: float) -> dict:
    params = {
        "parameters": ",".join(PARAMETROS),
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": desde.strftime("%Y%m%d"),
        "end": hasta.strftime("%Y%m%d"),
        "format": "JSON",
    }
    resp = requests.get(API_URL, params=params, timeout=120)
    if resp.status_code != 200:
        print(f"  [AVISO] {desde} a {hasta}: HTTP {resp.status_code}")
        return {}
    return resp.json().get("properties", {}).get("parameter", {})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--lat", type=float, default=LAT_DEFAULT, help="Latitud del punto (por defecto: Presa Santa Rita, Peñol-Guatapé)")
    ap.add_argument("--lon", type=float, default=LON_DEFAULT, help="Longitud del punto (por defecto: Presa Santa Rita, Peñol-Guatapé)")
    ap.add_argument("--nombre", default="penol", help="Identificador para el nombre del archivo de salida (por defecto: penol)")
    args = ap.parse_args()

    inicio = date.fromisoformat(args.inicio)
    fin = date.fromisoformat(args.fin)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    csv_path = salida / f"solar_power_{args.nombre}.csv"
    procesadas = ya_procesados(csv_path)
    columnas = ["fecha"] + [p.lower() for p in PARAMETROS]
    escribir_encabezado = not csv_path.exists()

    bloques = list(rangos_anuales(inicio, fin))
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        if escribir_encabezado:
            w.writeheader()
        for i, (desde, hasta) in enumerate(bloques, 1):
            fechas_bloque = {d.strftime("%Y%m%d") for d in _dias(desde, hasta)}
            if fechas_bloque and fechas_bloque.issubset({f.replace("-", "") for f in procesadas}):
                continue
            print(f"[{i}/{len(bloques)}] {desde} a {hasta}...")
            props = consultar_anio(desde, hasta, args.lat, args.lon)
            if not props:
                continue
            fechas_api = sorted(props.get(PARAMETROS[0], {}).keys())
            for fecha_str in fechas_api:
                fecha_iso = f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:]}"
                if fecha_iso in procesadas:
                    continue
                fila = {"fecha": fecha_iso}
                for p in PARAMETROS:
                    fila[p.lower()] = props.get(p, {}).get(fecha_str)
                w.writerow(fila)
                procesadas.add(fecha_iso)
            f.flush()

    print(f"\nListo. {len(procesadas)} días guardados en: {csv_path}")


def _dias(desde: date, hasta: date):
    from datetime import timedelta

    d = desde
    while d <= hasta:
        yield d
        d += timedelta(days=1)


if __name__ == "__main__":
    main()
