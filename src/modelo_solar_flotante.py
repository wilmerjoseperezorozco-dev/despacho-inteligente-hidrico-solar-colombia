"""
Simulación de generación fotovoltaica flotante sobre el embalse Peñol, a
partir de irradiancia real (NASA POWER) — no existe hoy un proyecto real
de solar flotante en este embalse, así que esta es una capa de escenario
simulado sobre un recurso físico real. Ver docs/motor-despacho-hidrico-solar.md
e issue #10 para la justificación completa de los supuestos.

Modelo: energía diaria = capacidad instalada (MWp) x irradiancia global
horizontal (kWh/m2/dia, numéricamente equivalente a "horas sol pico") x
performance ratio (PR). Es el mismo principio de cálculo que usa PVWatts
(NREL) en su forma más simple, sin resolución horaria ni derateo térmico
explícito (T2M se descarga pero no se usa todavía — ver limitación abajo).

PR = 0.78: valor típico de sistemas fotovoltaicos conectados a red
(pérdidas de inversor, cableado, suciedad, mismatch) — orden de magnitud
consistente con los defaults de pérdidas de sistema de PVWatts (~14%,
DC:AC ~0.86) más pérdidas adicionales de mismatch/suciedad no cubiertas
por ese valor. No se aplica el efecto de enfriamiento por agua reportado
en la literatura de solar flotante (rendimieto ligeramente mayor que en
tierra) — se omite por conservador, ver limitación.

Escenarios de capacidad instalada, anclados a precedentes reales (no
arbitrarios) documentados en docs/arquitectura-y-benchmarking.md:

    piloto      5 MWp    ~ Alqueva (Portugal), piloto pequeño real
    intermedio  151 MWp  ~ misma proporción solar/hidro que Da Mi (Vietnam):
                           47,5 MWp / 175 MW hidro = 27,1% -> aplicado a
                           los 560 MW de Central Guatapé
    agresivo    372 MWp  ~ misma proporción que Longyangxia (China):
                           850 MWp / 1.280 MW hidro = 66,4% -> aplicado a
                           los 560 MW de Central Guatapé

LIMITACIÓN CONOCIDA: el área real del espejo de agua del embalse
Peñol-Guatapé no está confirmada con precisión — las fuentes consultadas
difieren entre ~2.262 ha y ~74 km² (ver docs/motor-despacho-hidrico-solar.md
para el detalle). Se optó por anclar la capacidad a la PROPORCIÓN
solar/hidro de proyectos reales en vez de a un área de cobertura propia,
precisamente para no depender de esa cifra no confirmada.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

PERFORMANCE_RATIO = 0.78

CAPACIDAD_CENTRAL_GUATAPE_MW = 560.0

ESCENARIOS_MWP = {
    "piloto": 5.0,
    "intermedio": round(CAPACIDAD_CENTRAL_GUATAPE_MW * (47.5 / 175.0), 1),
    "agresivo": round(CAPACIDAD_CENTRAL_GUATAPE_MW * (850.0 / 1280.0), 1),
}


@dataclass(frozen=True)
class EscenarioSolar:
    nombre: str
    capacidad_mwp: float


def generar_energia_mwh(irradiancia_kwh_m2_dia: pd.Series, capacidad_mwp: float, pr: float = PERFORMANCE_RATIO) -> pd.Series:
    """Energía diaria (MWh) generada por un parque FV flotante de la capacidad dada."""
    irradiancia_valida = irradiancia_kwh_m2_dia.clip(lower=0)
    return capacidad_mwp * irradiancia_valida * pr


def cargar_irradiancia(ruta_csv: str) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv, parse_dates=["fecha"])
    df["allsky_sfc_sw_dwn"] = df["allsky_sfc_sw_dwn"].replace(-999.0, np.nan)
    df["allsky_sfc_sw_dwn"] = df["allsky_sfc_sw_dwn"].interpolate(limit=3)
    return df


def simular_escenarios(df_irradiancia: pd.DataFrame) -> pd.DataFrame:
    resultado = df_irradiancia[["fecha"]].copy()
    for nombre, capacidad in ESCENARIOS_MWP.items():
        resultado[f"solar_mwh_{nombre}"] = generar_energia_mwh(df_irradiancia["allsky_sfc_sw_dwn"], capacidad)
    return resultado


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entrada", required=True, help="CSV de solar_power_penol.csv")
    ap.add_argument("--salida", required=True, help="CSV de salida con energía simulada por escenario")
    args = ap.parse_args()

    df = cargar_irradiancia(args.entrada)
    out = simular_escenarios(df)
    out.to_csv(args.salida, index=False)

    print("Escenarios de capacidad instalada (MWp):", ESCENARIOS_MWP)
    for nombre in ESCENARIOS_MWP:
        col = f"solar_mwh_{nombre}"
        print(f"  {nombre}: media {out[col].mean():.1f} MWh/día, total {out[col].sum() / 1000:.0f} GWh en el período")
