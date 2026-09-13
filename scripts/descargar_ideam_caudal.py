"""
Descarga series históricas de caudal medio diario (IDEAM) para estaciones
dentro de una cuenca de interés, usando el bucket público S3 del IDEAM
(sin autenticación) descubierto en la guía oficial:

    https://datos.ideam.gov.co/s3-estacionesideam/guia/Notebook - Guia de Descarga Datos Parquet.ipynb

Catálogo oficial de estaciones: s3://s3-estacionesideam/catalogo/estaciones/csv/catalogo.csv
Catálogo oficial de variables:  s3://s3-estacionesideam/catalogo/variables/csv/variables.csv
Series históricas:              s3://s3-estacionesideam/observaciones/historicos/csv/{ETIQUETA}/{CODIGO}-{ETIQUETA}.csv

Probado end-to-end el 2026-09-13 con 4 estaciones reales de la cuenca aportante
al embalse Peñol-Guatapé (meseta oriente antioqueño, aguas arriba de la Presa
Santa Rita): Puente Real (Río Negro), Puente La Feria (Marinilla), Bodegas
(Q. Leonera) y Riotex (Q. La Mosca). Ver docs/datos-ideam-caudal.md.

IMPORTANTE: todos los registros descargados vienen marcados por IDEAM como
"Preliminar" (no "Aprobado") — son datos operativos, no la versión final
validada por el instituto. Documentar esto siempre que se usen.

Uso:
    python descargar_ideam_caudal.py --codigos 0023087150 0023087660 0023087670 0023087690 --salida ../data/raw/ideam_caudal
"""

import argparse
import csv
from datetime import date
from pathlib import Path

import requests

BASE_URL = "https://datos.ideam.gov.co/s3-estacionesideam/observaciones/historicos/csv/Q_MEDIA_D"

# Estaciones identificadas como parte de la cuenca aportante al embalse
# Peñol-Guatapé (aguas arriba de la Presa Santa Rita) — ver docs/delineacion-cuenca.md
# y docs/datos-ideam-caudal.md para la justificación de cada una.
ESTACIONES_CUENCA_GUATAPE = {
    "0023087150": "Puente Real (Río Negro)",
    "0023087660": "Puente La Feria (Marinilla)",
    "0023087670": "Riotex (Quebrada La Mosca)",
    "0023087690": "Bodegas (Quebrada Leonera)",
}


def descargar_estacion(codigo: str, destino: Path) -> Path | None:
    url = f"{BASE_URL}/{codigo}-Q_MEDIA_D.csv"
    resp = requests.get(url, timeout=60)
    if resp.status_code != 200:
        print(f"  [AVISO] {codigo}: HTTP {resp.status_code} — la estación puede no tener caudal medio diario publicado")
        return None
    ruta = destino / f"{codigo}-Q_MEDIA_D.csv"
    ruta.write_bytes(resp.content)
    return ruta


def resumir(ruta: Path, codigo: str, nombre: str) -> dict:
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        return {"codigo": codigo, "nombre": nombre, "registros": 0}

    fechas = sorted(r["fechaObservacion"][:10] for r in filas)
    valores = [float(r["valorObservado"]) for r in filas if r["valorObservado"]]
    aprobados = sum(1 for r in filas if r["nivelAprobacion"] == "Aprobado")
    dias_totales = (date.fromisoformat(fechas[-1]) - date.fromisoformat(fechas[0])).days + 1

    return {
        "codigo": codigo,
        "nombre": nombre,
        "fecha_inicio": fechas[0],
        "fecha_fin": fechas[-1],
        "registros": len(filas),
        "dias_totales_periodo": dias_totales,
        "cobertura_pct": round(100 * len(filas) / dias_totales, 1),
        "aprobados": aprobados,
        "preliminares": len(filas) - aprobados,
        "caudal_min_m3s": round(min(valores), 2) if valores else None,
        "caudal_max_m3s": round(max(valores), 2) if valores else None,
        "caudal_medio_m3s": round(sum(valores) / len(valores), 2) if valores else None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--codigos",
        nargs="+",
        default=list(ESTACIONES_CUENCA_GUATAPE.keys()),
        help="Códigos de estación IDEAM a descargar (10 dígitos, con ceros a la izquierda)",
    )
    ap.add_argument("--salida", required=True, help="Carpeta de salida para los CSV crudos")
    ap.add_argument(
        "--resumen",
        default=None,
        help="Ruta del CSV de resumen de calidad/cobertura a generar (opcional)",
    )
    args = ap.parse_args()

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    resumenes = []
    for codigo in args.codigos:
        nombre = ESTACIONES_CUENCA_GUATAPE.get(codigo, "(nombre no registrado localmente)")
        print(f"Descargando {codigo} — {nombre}...")
        ruta = descargar_estacion(codigo, salida)
        if ruta is None:
            continue
        resumenes.append(resumir(ruta, codigo, nombre))

    if args.resumen and resumenes:
        campos = list(resumenes[0].keys())
        with open(args.resumen, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(resumenes)
        print(f"\nResumen de calidad guardado en: {args.resumen}")

    print("\nRESUMEN:")
    for r in resumenes:
        print(
            f"  {r['codigo']} {r['nombre']}: {r.get('fecha_inicio')} a {r.get('fecha_fin')} "
            f"({r.get('registros')} registros, {r.get('cobertura_pct')}% cobertura, "
            f"{r.get('preliminares')} preliminares / {r.get('aprobados')} aprobados)"
        )

    print(
        "\nRECORDATORIO: todos los registros de este bucket vienen marcados como "
        "'Preliminar' salvo indicación contraria — no son la versión final validada por IDEAM."
    )


if __name__ == "__main__":
    main()
