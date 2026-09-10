"""
Delineación automática de cuenca aportante a partir de un punto de desfogue,
usando DEM SRTM 30m (dominio público, sin autenticación) y pysheds.

Probado end-to-end el 2026-09-10 para la cuenca de Guatapé/El Peñol (río Nare).
Ver docs/delineacion-cuenca.md para el detalle metodológico completo, incluyendo
un error real encontrado y corregido durante la prueba (punto de desfogue
impreciso -> área absurda de 2 km²; corregido buscando el punto de máxima
acumulación de flujo en un radio de 2 km -> 1.047,6 km², orden de magnitud
físicamente plausible para un embalse hidroeléctrico grande).

Fuente del DEM: AWS Terrain Tiles / Mapzen (SRTM 30m, formato Skadi, sin login)
https://s3.amazonaws.com/elevation-tiles-prod/skadi/

IMPORTANTE: la precisión del resultado depende completamente de la precisión del
punto de desfogue. Un punto aproximado (ej. una etiqueta de "Embalse" en OSM)
puede caer en un tributario menor. Se recomienda usar la coordenada exacta del
muro de la presa o el punto donde el río se angosta hacia la estructura —
verificable en Google Earth con clic derecho sobre la imagen satelital.

Uso:
    python delinear_cuenca.py --lon -75.1799709 --lat 6.2855878 \
        --nombre "Guatape-El Penol" --salida ../data/processed/cuencas
"""

import argparse
import gzip
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import requests

if not hasattr(np, "in1d"):
    np.in1d = np.isin  # compat: pysheds usa la API de numpy < 2.0

try:
    import rasterio
    from rasterio.features import shapes
    from rasterio.merge import merge
    from pysheds.grid import Grid
except ImportError:
    sys.exit(
        "Faltan dependencias. Instalar con: pip install rasterio pysheds "
        "(ya incluidas en requirements.txt del repo)."
    )

SKADI_BASE = "https://s3.amazonaws.com/elevation-tiles-prod/skadi"


def tile_srtm(lat: float, lon: float) -> str:
    """Nombre del tile SRTM (esquina suroeste) que contiene el punto dado."""
    idx_lat = math.floor(lat)
    idx_lon = math.floor(lon)
    ns = "N" if idx_lat >= 0 else "S"
    ew = "E" if idx_lon >= 0 else "W"
    return f"{ns}{abs(idx_lat):02d}{ew}{abs(idx_lon):03d}"


def descargar_tile(nombre_tile: str, destino: Path) -> Path:
    ruta_hgt = destino / f"{nombre_tile}.hgt"
    if ruta_hgt.exists():
        return ruta_hgt
    url = f"{SKADI_BASE}/{nombre_tile[:3]}/{nombre_tile}.hgt.gz"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    ruta_gz = destino / f"{nombre_tile}.hgt.gz"
    ruta_gz.write_bytes(resp.content)
    with gzip.open(ruta_gz, "rb") as f_in, open(ruta_hgt, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return ruta_hgt


def preparar_dem(lat: float, lon: float, margen_grados: float, tmp: Path) -> Path:
    """Descarga los tiles SRTM necesarios, los mosaica y recorta a una ventana alrededor del punto."""
    lat_min, lat_max = lat - margen_grados, lat + margen_grados
    lon_min, lon_max = lon - margen_grados, lon + margen_grados

    tiles = set()
    for la in (lat_min, lat_max):
        for lo in (lon_min, lon_max):
            tiles.add(tile_srtm(la, lo))

    rutas = [descargar_tile(t, tmp) for t in sorted(tiles)]
    srcs = [rasterio.open(r) for r in rutas]
    mosaico, transform = merge(srcs)

    perfil = srcs[0].profile
    perfil.update(driver="GTiff", height=mosaico.shape[1], width=mosaico.shape[2], transform=transform)
    ruta_mosaico = tmp / "mosaico.tif"
    with rasterio.open(ruta_mosaico, "w", **perfil) as dst:
        dst.write(mosaico)

    with rasterio.open(ruta_mosaico) as src:
        from rasterio.windows import from_bounds
        win = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)
        datos = src.read(1, window=win)
        win_transform = src.window_transform(win)
        perfil.update(height=datos.shape[0], width=datos.shape[1], transform=win_transform)
        ruta_recorte = tmp / "dem_recorte.tif"
        with rasterio.open(ruta_recorte, "w", **perfil) as dst:
            dst.write(datos, 1)

    return ruta_recorte


def delinear(dem_path: Path, lon: float, lat: float, radio_busqueda_grados: float = 0.02):
    grid = Grid.from_raster(str(dem_path))
    dem = grid.read_raster(str(dem_path))

    pit_filled = grid.fill_pits(dem)
    flooded = grid.fill_depressions(pit_filled)
    inflated = grid.resolve_flats(flooded)
    fdir = grid.flowdir(inflated)
    acc = grid.accumulation(fdir)

    res = abs(grid.affine[0])
    radio_celdas = max(1, int(radio_busqueda_grados / res))
    col0 = int((lon - grid.affine[2]) / grid.affine[0])
    row0 = int((lat - grid.affine[5]) / grid.affine[4])

    acc_arr = np.asarray(acc)
    r0, r1 = max(0, row0 - radio_celdas), min(acc_arr.shape[0], row0 + radio_celdas)
    c0, c1 = max(0, col0 - radio_celdas), min(acc_arr.shape[1], col0 + radio_celdas)
    ventana = acc_arr[r0:r1, c0:c1]
    idx = np.unravel_index(np.argmax(ventana), ventana.shape)
    row_max, col_max = r0 + idx[0], c0 + idx[1]
    x_max = grid.affine[2] + col_max * grid.affine[0]
    y_max = grid.affine[5] + row_max * grid.affine[4]
    acumulacion_max = float(acc_arr[row_max, col_max])

    catch = grid.catchment(x=x_max, y=y_max, fdir=fdir, xytype="coordinate")
    mascara = np.asarray(catch).astype("uint8")
    ncel = float(mascara.sum())
    area_km2 = ncel * (res * 111.32) * (res * 110.57)

    return {
        "punto_ajustado": (x_max, y_max),
        "acumulacion_flujo": acumulacion_max,
        "area_km2": round(area_km2, 1),
        "mascara": mascara,
        "affine": grid.affine,
    }


def exportar_geojson(resultado: dict, nombre: str, salida: Path):
    resultados_vec = list(
        shapes(resultado["mascara"], mask=resultado["mascara"].astype(bool), transform=resultado["affine"])
    )
    geoms = [g for g, v in resultados_vec if v == 1]
    if not geoms:
        print("[AVISO] No se generó ningún polígono — revisar el punto de desfogue.")
        return None

    # Si hay varios fragmentos (ruido de celdas aisladas), se toma el de mayor extensión
    def extension(g):
        coords = g["coordinates"][0]
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))

    principal = max(geoms, key=extension)

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "nombre": f"Cuenca aportante preliminar - {nombre}",
                    "metodo": "SRTM 30m + pysheds (D8), punto de max. acumulación de flujo en radio de búsqueda",
                    "area_km2_aprox": resultado["area_km2"],
                    "estado": "PRELIMINAR - validar con coordenada exacta del punto de desfogue (muro de presa)",
                },
                "geometry": principal,
            }
        ],
    }
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / f"cuenca_preliminar_{nombre.lower().replace(' ', '_')}.geojson"
    import json
    ruta.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lon", type=float, required=True, help="Longitud del punto de desfogue")
    ap.add_argument("--lat", type=float, required=True, help="Latitud del punto de desfogue")
    ap.add_argument("--nombre", required=True, help="Nombre identificador de la cuenca/embalse")
    ap.add_argument("--salida", required=True, help="Carpeta de salida del GeoJSON")
    ap.add_argument(
        "--margen-dem",
        type=float,
        default=0.4,
        help="Margen en grados alrededor del punto para descargar el DEM (default 0.4 ~ 44 km)",
    )
    ap.add_argument(
        "--radio-busqueda",
        type=float,
        default=0.02,
        help="Radio en grados para buscar la celda de mayor acumulación de flujo cerca del punto (default 0.02 ~ 2.2 km)",
    )
    ap.add_argument("--tmp", default="_tmp_dem", help="Carpeta temporal para tiles DEM")
    args = ap.parse_args()

    tmp = Path(args.tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    print(f"Preparando DEM alrededor de ({args.lon}, {args.lat})...")
    dem_path = preparar_dem(args.lat, args.lon, args.margen_dem, tmp)

    print("Delineando cuenca (fill -> flowdir -> accumulation -> catchment)...")
    resultado = delinear(dem_path, args.lon, args.lat, args.radio_busqueda)

    print(f"Punto ajustado a la red de drenaje: {resultado['punto_ajustado']}")
    print(f"Acumulación de flujo en ese punto: {resultado['acumulacion_flujo']:.0f} celdas")
    print(f"Área aproximada de la cuenca: {resultado['area_km2']} km²")

    ruta = exportar_geojson(resultado, args.nombre, Path(args.salida))
    if ruta:
        print(f"GeoJSON guardado en: {ruta}")

    print(
        "\nRECORDATORIO: este resultado es preliminar. Verificar el área contra una fuente "
        "oficial (IDEAM/CORNARE/EPM) y, si es posible, repetir con la coordenada exacta del "
        "muro de la presa antes de usarlo como insumo definitivo del modelo."
    )


if __name__ == "__main__":
    main()
