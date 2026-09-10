"""
Descarga y recorta precipitación diaria CHIRPS 2.0 para una cuenca de interés.

Fuente: Climate Hazards Center, UC Santa Barbara (dominio público, sin autenticación).
https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05/

Probado end-to-end el 2026-09-10 con el archivo del 2023-06-15 recortado a la zona
de Guatapé/El Peñol-Nare (ver docs/datos-satelitales-precipitacion.md).

Uso:
    python descargar_chirps.py --inicio 2015-01-01 --fin 2015-01-31 --salida ../data/raw/chirps

Genera un CSV con la precipitación media diaria (mm/día) dentro del bbox indicado,
más los .tif recortados individuales (mucho más livianos que el ráster global de 0.05°).
"""

import argparse
import gzip
import io
import shutil
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

try:
    import rasterio
    from rasterio.windows import from_bounds
except ImportError:
    sys.exit(
        "Falta 'rasterio'. Instalar con: pip install rasterio "
        "(ya incluido en requirements.txt del repo)."
    )

BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05"

# Bbox por defecto: embalse Guatapé/El Peñol-Nare (Antioquia).
# Ajustar según la cuenca aportante exacta cuando se tenga el polígono real.
BBOX_GUATAPE = (-75.3, 5.9, -74.9, 6.4)  # (lon_min, lat_min, lon_max, lat_max)


def rango_fechas(inicio: date, fin: date):
    dia = inicio
    while dia <= fin:
        yield dia
        dia += timedelta(days=1)


def descargar_dia(fecha: date, destino_tmp: Path, pausa: float = 0.5) -> Path | None:
    """Descarga y descomprime el ráster global de un día. Devuelve la ruta local o None si falla."""
    nombre = f"chirps-v2.0.{fecha.year}.{fecha.month:02d}.{fecha.day:02d}"
    url = f"{BASE_URL}/{fecha.year}/{nombre}.tif.gz"
    ruta_tif = destino_tmp / f"{nombre}.tif"

    if ruta_tif.exists():
        return ruta_tif

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [AVISO] No se pudo descargar {fecha.isoformat()}: {e}")
        return None

    with gzip.open(io.BytesIO(resp.content)) as f_in, open(ruta_tif, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    time.sleep(pausa)  # no saturar el servidor público
    return ruta_tif


def recortar_y_promediar(ruta_tif: Path, bbox: tuple) -> tuple[float, float, float] | None:
    """Devuelve (media, min, max) de precipitación (mm/día) dentro del bbox."""
    with rasterio.open(ruta_tif) as src:
        win = from_bounds(*bbox, src.transform)
        datos = src.read(1, window=win)
    if datos.size == 0:
        return None
    return float(datos.mean()), float(datos.min()), float(datos.max())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inicio", required=True, help="Fecha inicio YYYY-MM-DD")
    ap.add_argument("--fin", required=True, help="Fecha fin YYYY-MM-DD")
    ap.add_argument("--salida", required=True, help="Carpeta de salida")
    ap.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("LON_MIN", "LAT_MIN", "LON_MAX", "LAT_MAX"),
        default=BBOX_GUATAPE,
        help="Bbox de recorte (por defecto: Guatapé/El Peñol-Nare)",
    )
    ap.add_argument(
        "--mantener-globales",
        action="store_true",
        help="Conservar los .tif globales descargados (ocupan ~57 MB cada uno; por defecto se borran tras recortar)",
    )
    args = ap.parse_args()

    inicio = date.fromisoformat(args.inicio)
    fin = date.fromisoformat(args.fin)
    salida = Path(args.salida)
    tmp = salida / "_tmp_globales"
    salida.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)

    csv_path = salida / "precipitacion_diaria.csv"
    filas = []

    for fecha in rango_fechas(inicio, fin):
        print(f"Procesando {fecha.isoformat()}...")
        ruta_tif = descargar_dia(fecha, tmp)
        if ruta_tif is None:
            continue
        resultado = recortar_y_promediar(ruta_tif, tuple(args.bbox))
        if resultado is None:
            continue
        media, minimo, maximo = resultado
        filas.append((fecha.isoformat(), media, minimo, maximo))
        if not args.mantener_globales:
            ruta_tif.unlink(missing_ok=True)

    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("fecha,precip_media_mm,precip_min_mm,precip_max_mm\n")
        for fila in filas:
            f.write(",".join(str(x) for x in fila) + "\n")

    if not args.mantener_globales:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nListo. {len(filas)} días procesados. CSV: {csv_path}")


if __name__ == "__main__":
    main()
