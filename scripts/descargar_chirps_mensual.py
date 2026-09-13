"""
Descarga precipitación mensual CHIRPS 2.0 para una cuenca de interés, sobre
todo el histórico disponible (1981-presente) sin el costo de ancho de banda
del producto diario completo.

Fuente: Climate Hazards Center, UC Santa Barbara (dominio público, sin auth).
https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/tifs/p05/

Decisión de alcance (documentada en docs/dataset-consolidado-fase1.md):
CHIRPS diario completo 2000-2026 son ~9.700 archivos (~25 GB transferidos),
impracticable en una sesión interactiva. Se usa el producto MENSUAL para
todo el histórico (contexto de largo plazo, ~320 archivos) y el producto
DIARIO (scripts/descargar_chirps.py) solo para una ventana reciente.

Uso:
    python descargar_chirps_mensual.py --inicio 2000-01 --fin 2026-08 --salida ../data/raw/chirps_mensual
"""

import argparse
import gzip
import io
import shutil
import sys
import time
from pathlib import Path

import requests

try:
    import rasterio
    from rasterio.windows import from_bounds
except ImportError:
    sys.exit("Falta 'rasterio'. Instalar con: pip install rasterio")

# A diferencia del producto diario (que usa tifs/p05/{anio}/), el mensual
# no tiene subcarpeta p05 -- los archivos estan directo bajo tifs/. Verificado
# con HTTP HEAD real antes de asumirlo (la carpeta p05 para mensual da 404).
BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/tifs"
BBOX_GUATAPE = (-75.3, 5.9, -74.9, 6.4)  # mismo bbox usado en descargar_chirps.py


def rango_meses(inicio: str, fin: str):
    """inicio/fin en formato 'YYYY-MM'."""
    y0, m0 = map(int, inicio.split("-"))
    y1, m1 = map(int, fin.split("-"))
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def descargar_mes(anio: int, mes: int, destino_tmp: Path, pausa: float = 0.3) -> Path | None:
    nombre = f"chirps-v2.0.{anio}.{mes:02d}"
    url = f"{BASE_URL}/{nombre}.tif.gz"
    ruta_tif = destino_tmp / f"{nombre}.tif"
    if ruta_tif.exists():
        return ruta_tif
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [AVISO] No se pudo descargar {anio}-{mes:02d}: {e}")
        return None
    with gzip.open(io.BytesIO(resp.content)) as f_in, open(ruta_tif, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    time.sleep(pausa)
    return ruta_tif


def recortar_y_promediar(ruta_tif: Path, bbox: tuple):
    with rasterio.open(ruta_tif) as src:
        win = from_bounds(*bbox, src.transform)
        datos = src.read(1, window=win)
    if datos.size == 0:
        return None
    return float(datos.mean()), float(datos.min()), float(datos.max())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inicio", required=True, help="Mes inicio YYYY-MM")
    ap.add_argument("--fin", required=True, help="Mes fin YYYY-MM")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--bbox", nargs=4, type=float, default=BBOX_GUATAPE)
    ap.add_argument("--mantener-globales", action="store_true")
    args = ap.parse_args()

    salida = Path(args.salida)
    tmp = salida / "_tmp_globales"
    salida.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)

    # Escritura incremental: si el proceso se interrumpe (timeout, corte de red),
    # no se pierde el trabajo ya hecho -- cada mes se escribe apenas se calcula,
    # no al final. Esto costo una corrida completa perdida durante el desarrollo
    # (ver docs/dataset-consolidado-fase1.md) y se corrigio antes de reintentar.
    csv_path = salida / "precipitacion_mensual.csv"
    ya_procesados = set()
    if csv_path.exists():
        with open(csv_path, encoding="utf-8") as f:
            ya_procesados = {row.split(",")[0] for row in f.readlines()[1:] if row.strip()}
        print(f"Reanudando: {len(ya_procesados)} meses ya estaban guardados de una corrida previa.")
    else:
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("mes,precip_media_mm,precip_min_mm,precip_max_mm\n")

    meses = list(rango_meses(args.inicio, args.fin))
    procesados_esta_corrida = 0
    for i, (anio, mes) in enumerate(meses, 1):
        clave = f"{anio}-{mes:02d}"
        if clave in ya_procesados:
            continue
        print(f"[{i}/{len(meses)}] Procesando {clave}...")
        ruta_tif = descargar_mes(anio, mes, tmp)
        if ruta_tif is None:
            continue
        resultado = recortar_y_promediar(ruta_tif, tuple(args.bbox))
        if resultado is None:
            continue
        media, minimo, maximo = resultado
        with open(csv_path, "a", encoding="utf-8") as f:
            f.write(f"{clave},{media},{minimo},{maximo}\n")
        procesados_esta_corrida += 1
        if not args.mantener_globales:
            ruta_tif.unlink(missing_ok=True)

    if not args.mantener_globales:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nListo. {procesados_esta_corrida} meses nuevos procesados en esta corrida. CSV: {csv_path}")


if __name__ == "__main__":
    main()
