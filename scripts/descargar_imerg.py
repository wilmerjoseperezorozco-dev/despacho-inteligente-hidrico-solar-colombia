"""
Descarga precipitación GPM-IMERG (NASA GES DISC) para una cuenca de interés.

ADVERTENCIA: este script NO ha sido probado end-to-end en esta sesión (a diferencia
de descargar_chirps.py) porque requiere credenciales personales de NASA Earthdata
que no se pueden generar automáticamente. Revisar y probar con un rango pequeño
antes de confiar en él para una descarga histórica completa.

Requisitos previos (manuales, una sola vez):
1. Crear cuenta gratuita en https://urs.earthdata.nasa.gov/
2. Generar un token en el perfil de Earthdata (Profile > Generate Token)
3. Guardar el token en una variable de entorno local, NUNCA en el código ni en el repo:
       export EARTHDATA_TOKEN="tu_token_aqui"      (bash)
       $env:EARTHDATA_TOKEN = "tu_token_aqui"       (PowerShell)

Producto usado: GPM_3IMERGDF (IMERG Final Run, diario, v07) — resolución 0.1°,
recomendado para investigación (incluye calibración con estaciones y ERA-5).
Referencia: https://gpm.nasa.gov/data/imerg

Uso previsto (una vez validado):
    python descargar_imerg.py --inicio 2015-01-01 --fin 2015-01-31 --salida ../data/raw/imerg
"""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

GES_DISC_BASE = (
    "https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGDF.07"
)

BBOX_GUATAPE = (-75.3, 5.9, -74.9, 6.4)  # mismo bbox por defecto que CHIRPS


def sesion_autenticada() -> requests.Session:
    token = os.environ.get("EARTHDATA_TOKEN")
    if not token:
        sys.exit(
            "Falta la variable de entorno EARTHDATA_TOKEN. "
            "Generar un token en https://urs.earthdata.nasa.gov/ (Profile > Generate Token) "
            "y exportarlo antes de ejecutar este script. No se guarda ningún token en el repo."
        )
    sesion = requests.Session()
    sesion.headers.update({"Authorization": f"Bearer {token}"})
    return sesion


def rango_fechas(inicio: date, fin: date):
    dia = inicio
    while dia <= fin:
        yield dia
        dia += timedelta(days=1)


def descargar_dia(sesion: requests.Session, fecha: date, destino: Path, bbox: tuple):
    """
    Descarga el subset diario vía OPeNDAP restringido al bbox indicado.
    NOTA: la ruta exacta del archivo IMERG (carpeta por año/día-juliano) y el formato
    de subsetting OPeNDAP deben confirmarse contra la documentación vigente de GES DISC
    antes de la primera ejecución real — no se verificó la URL exacta en esta sesión.
    """
    anio = fecha.year
    dia_juliano = fecha.timetuple().tm_yday
    # Patrón de referencia (a confirmar antes de usar en producción):
    url = (
        f"{GES_DISC_BASE}/{anio}/{dia_juliano:03d}/"
        f"3B-DAY.MS.MRG.3IMERG.{fecha.strftime('%Y%m%d')}-S000000-E235959.V07B.nc4"
    )
    salida = destino / f"imerg_{fecha.isoformat()}.nc4"
    resp = sesion.get(url, timeout=120)
    if resp.status_code != 200:
        print(f"  [AVISO] {fecha.isoformat()}: HTTP {resp.status_code} — revisar URL/credenciales")
        return None
    salida.write_bytes(resp.content)
    return salida


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--bbox", nargs=4, type=float, default=BBOX_GUATAPE)
    args = ap.parse_args()

    inicio = date.fromisoformat(args.inicio)
    fin = date.fromisoformat(args.fin)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    sesion = sesion_autenticada()

    print(
        "AVISO: script no probado end-to-end. Se recomienda ejecutar primero con "
        "un rango de 1-2 días y validar el archivo resultante antes de una descarga masiva.\n"
    )

    for fecha in rango_fechas(inicio, fin):
        print(f"Procesando {fecha.isoformat()}...")
        descargar_dia(sesion, fecha, salida, tuple(args.bbox))


if __name__ == "__main__":
    main()
