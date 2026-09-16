"""
Motor de optimización de despacho hídrico-solar — núcleo de Fase 3 (issue #11).

Qué resuelve: dado un historial real de aportes de energía al embalse
Peñol (AporEner de XM, ríos Guatapé+Nare), la obligación de energía firme
real de la Central Guatapé (ObligEnerFirme) y un escenario de generación
solar flotante simulada (src/modelo_solar_flotante.py), decide cuánta
energía debe turbinar la central cada día para cumplir la obligación con
el menor consumo posible del volumen almacenado — maximizando el nivel
mínimo que alcanza el embalse durante el período analizado.

Formulación (programación lineal, resuelta con PuLP/CBC):

    maximizar   z
    sujeto a    volumen(t) = volumen(t-1) + aportes(t) - hidro(t)
                hidro(t) + solar(t) >= obligacion(t)
                0 <= hidro(t) <= capacidad_maxima_diaria
                volumen(t) >= z                          para todo t
                volumen(0) = volumen_inicial (dato real)

z es, por construcción, el nivel más bajo que toca el embalse en todo el
período — maximizarlo es minimizar el riesgo de vaciado crítico, que es
literalmente el objetivo que describe el README para Fase 3.

HALLAZGO REAL sobre qué usar como "obligacion(t)" (--demanda): probar
primero con la Obligación de Energía Firme real mostró que es demasiado
baja (media 4,4 GWh/día) frente a los aportes típicos (media 19 GWh/día)
para ser una restricción activa casi nunca — el LP casi nunca necesita
turbinar, el embalse se llena, y el solar no tiene nada que sustituir
(mejora medida: +0,0 a +1,4 GWh en el piso mínimo sobre 6 años). Se
cambió el valor por defecto a igualar la generación real histórica
(media 9,2 GWh/día, más representativa del despacho efectivo real) —
ver docs/motor-despacho-hidrico-solar.md §5.3 para el resultado completo
de ambas versiones, no solo la que se adoptó.

LIMITACIÓN METODOLÓGICA EXPLÍCITA (léase antes de citar resultados):
este es un backtest de "información perfecta" (oracle) — el LP conoce de
antemano los aportes y la irradiancia reales de todo el período. Esto es
una cota superior de lo que la coordinación hídrico-solar podría lograr
con pronósticos perfectos, NO una política operativa desplegable en
tiempo real. Convertir esto en una política real (horizonte móvil con el
pronóstico de un día del modelo de Fase 2, o un modelo de pronóstico
multi-día nuevo) queda explícitamente para trabajo futuro. Ver docs del
motor de despacho para el detalle completo.

Para aislar el efecto real del solar (y no mezclarlo con decisiones
operativas históricas que no modelamos — vertimientos, otras plantas de
la cascada, señales de precio de bolsa, etc.), la comparación principal
es LP-sin-solar vs. LP-con-solar, ambas resueltas por este mismo motor
— no una comparación directa contra el volumen histórico real, que sí se
reporta aparte como referencia con sus propias advertencias.

Uso:
    python motor_despacho.py --dataset ../data/processed/dataset_fase3_despacho.csv \
        --inicio 2021-01-01 --fin 2026-08-31 --salida ../data/processed/despacho_resultados.csv
"""

import argparse

import pandas as pd
import pulp

CAPACIDAD_CENTRAL_GUATAPE_MW = 560.0
CAPACIDAD_NOMINAL_DIARIA_KWH = CAPACIDAD_CENTRAL_GUATAPE_MW * 24 * 1000

# HALLAZGO REAL (2026-09-16): en 14 de 2.069 días del período 2021-2026,
# la generación real reportada por XM superó levemente esta capacidad
# nominal (hasta 13.640.808 kWh/día vs. 13.440.000 kWh/día nominal, ~1,5%
# por encima) — las centrales hidráulicas pueden operar brevemente por
# encima de su capacidad nominal. Usar solo el valor nominal como cota
# volvía el LP "Infeasible" en escenarios de demanda=generacion_real con
# poca capacidad solar (el solar no alcanzaba a cubrir el faltante en
# esos días puntuales). Se usa el máximo real observado como cota cuando
# es mayor que el nominal, en vez de descartar el hallazgo o forzar el
# dato.

ESCENARIOS_SOLAR = ["piloto", "intermedio", "agresivo"]


def _construir_modelo(df: pd.DataFrame, columna_solar: str | None, columna_demanda: str, sentido):
    n = len(df)
    aportes = df["aportes_totales_kwh"].values
    demanda = df[columna_demanda].values
    solar = df[columna_solar].values * 1000 if columna_solar else [0.0] * n  # MWh -> kWh
    volumen_inicial = df["volumen_util_kwh"].iloc[0]
    capacidad_maxima_diaria_kwh = max(CAPACIDAD_NOMINAL_DIARIA_KWH, df["generacion_kwh"].max())

    prob = pulp.LpProblem("despacho_hidrico_solar", sentido)
    hidro = [pulp.LpVariable(f"hidro_{t}", lowBound=0, upBound=capacidad_maxima_diaria_kwh) for t in range(n)]
    volumen = [pulp.LpVariable(f"volumen_{t}", lowBound=0) for t in range(n)]
    z = pulp.LpVariable("z_volumen_minimo")

    for t in range(n):
        anterior = volumen_inicial if t == 0 else volumen[t - 1]
        prob += volumen[t] == anterior + aportes[t] - hidro[t]
        prob += hidro[t] + solar[t] >= demanda[t]
        prob += volumen[t] >= z

    return prob, hidro, volumen, z


def resolver_lp(df: pd.DataFrame, columna_solar: str | None, columna_demanda: str) -> dict:
    """Resuelve el LP de despacho para el período de df, en dos etapas (lexicográfico).

    Si columna_solar es None, solar=0 (baseline). Ver HALLAZGO REAL más abajo
    sobre por qué es de dos etapas y no una sola.

    HALLAZGO REAL (2026-09-16): maximizar únicamente z (el piso mínimo del
    embalse) deja indeterminado cuánta agua se ahorra el resto de los días
    que no tocan ese mínimo — CBC devolvía soluciones "óptimas" en z pero
    que casi no usaban el solar disponible (ej. escenario agresivo: ~2.946
    GWh de solar generados en el período, pero solo ~88 GWh menos de
    hidráulica turbinada — un desajuste que no tiene sentido físico si el
    solar realmente estuviera sustituyendo hidráulica día a día). La causa
    es degeneración del LP: como el objetivo no premia usar el solar en
    días que no son el mínimo, el solver elige cualquier solución válida
    entre muchas equivalentes. Se corrige con una segunda etapa: fijar z
    en su valor óptimo y, entre todas las soluciones que lo logran,
    minimizar el turbinado total — así el resultado sí refleja "usar el
    solar siempre que esté disponible", no un artefacto del solver.
    """
    prob1, hidro1, volumen1, z1 = _construir_modelo(df, columna_solar, columna_demanda, pulp.LpMaximize)
    prob1 += z1
    estado1 = prob1.solve(pulp.PULP_CBC_CMD(msg=False))
    z_optimo = pulp.value(z1)

    # Tolerancia relativa, no absoluta: con volumenes del orden de 1e9-1e10 kWh,
    # un margen fijo de 1 kWh es menor que el error de punto flotante del propio
    # solver en la etapa 1 y volvía la etapa 2 "Infeasible" sin razón física
    # (hallazgo real, 2026-09-16 — se detectó al ver "Infeasible" en escenarios
    # donde la etapa 1 ya había resuelto "Optimal", lo cual es imposible si la
    # tolerancia fuera correcta).
    tolerancia = max(1000.0, abs(z_optimo) * 1e-6)
    prob2, hidro2, volumen2, z2 = _construir_modelo(df, columna_solar, columna_demanda, pulp.LpMinimize)
    prob2 += z2 >= z_optimo - tolerancia
    prob2 += pulp.lpSum(hidro2)
    estado2 = prob2.solve(pulp.PULP_CBC_CMD(msg=False))

    return {
        "estado": f"{pulp.LpStatus[estado1]}/{pulp.LpStatus[estado2]}",
        "z_volumen_minimo_kwh": z_optimo,
        "hidro_total_kwh": sum(pulp.value(h) for h in hidro2),
        "volumen_serie_kwh": [pulp.value(v) for v in volumen2],
        "hidro_serie_kwh": [pulp.value(h) for h in hidro2],
    }


def preparar_dataset(df: pd.DataFrame, inicio: str, fin: str) -> pd.DataFrame:
    df = df[(df["fecha"] >= inicio) & (df["fecha"] <= fin)].sort_values("fecha").reset_index(drop=True)
    df["aportes_totales_kwh"] = df["aporte_energia_guatape_kwh"] + df["aporte_energia_nare_kwh"]
    dias_sin_generacion = df["generacion_kwh"].isna().sum()
    if dias_sin_generacion:
        print(f"[AVISO] {dias_sin_generacion} días sin dato de generación real — se rellenan por interpolación para poder usar 'generacion_real' como demanda.")
        df["generacion_kwh"] = df["generacion_kwh"].interpolate(limit=7).bfill()
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument(
        "--demanda",
        choices=["obligacion", "generacion_real"],
        default="generacion_real",
        help="obligacion = solo la Obligacion de Energia Firme (resultó ser demasiado baja para ser una restricción activa casi nunca, ver docs); generacion_real = iguala la generación hidráulica real histórica (más representativa del despacho efectivo)",
    )
    args = ap.parse_args()
    columna_demanda = "obligacion_energia_firme_kwh" if args.demanda == "obligacion" else "generacion_kwh"

    df_completo = pd.read_csv(args.dataset, parse_dates=["fecha"])
    df_completo["fecha"] = df_completo["fecha"].astype(str)
    df = preparar_dataset(df_completo, args.inicio, args.fin)
    print(f"Período: {df['fecha'].iloc[0]} a {df['fecha'].iloc[-1]} ({len(df)} días) | demanda: {args.demanda}")

    volumen_minimo_real_kwh = df["volumen_util_kwh"].min()
    print(f"\n[Referencia] Volumen mínimo REAL observado en el período: {volumen_minimo_real_kwh / 1e6:.1f} GWh")
    print("  (referencia con advertencia: incluye decisiones operativas reales no modeladas aquí)")

    print("\n[LP sin solar] Resolviendo (línea base de este mismo motor)...")
    base = resolver_lp(df, None, columna_demanda)
    print(f"  Estado: {base['estado']} | z (mínimo alcanzado) = {base['z_volumen_minimo_kwh'] / 1e6:.1f} GWh | hidro total = {base['hidro_total_kwh'] / 1e6:.1f} GWh")

    filas_resultado = [{"fecha": df["fecha"].iloc[t], "volumen_sin_solar_kwh": base["volumen_serie_kwh"][t], "hidro_sin_solar_kwh": base["hidro_serie_kwh"][t]} for t in range(len(df))]
    resultados = pd.DataFrame(filas_resultado)

    resumen = {"escenario": "sin_solar", "z_volumen_minimo_gwh": base["z_volumen_minimo_kwh"] / 1e6, "hidro_total_gwh": base["hidro_total_kwh"] / 1e6, "mejora_vs_sin_solar_gwh": 0.0}
    resumenes = [resumen]

    for escenario in ESCENARIOS_SOLAR:
        columna = f"solar_mwh_{escenario}"
        if columna not in df.columns:
            print(f"\n[AVISO] Falta columna {columna}, se omite el escenario {escenario}.")
            continue
        print(f"\n[LP con solar — {escenario}] Resolviendo...")
        con_solar = resolver_lp(df, columna, columna_demanda)
        mejora = (con_solar["z_volumen_minimo_kwh"] - base["z_volumen_minimo_kwh"]) / 1e6
        print(f"  Estado: {con_solar['estado']} | z = {con_solar['z_volumen_minimo_kwh'] / 1e6:.1f} GWh | hidro total = {con_solar['hidro_total_kwh'] / 1e6:.1f} GWh | mejora del piso = {mejora:+.1f} GWh")
        resultados[f"volumen_{escenario}_kwh"] = con_solar["volumen_serie_kwh"]
        resultados[f"hidro_{escenario}_kwh"] = con_solar["hidro_serie_kwh"]
        resumenes.append({"escenario": escenario, "z_volumen_minimo_gwh": con_solar["z_volumen_minimo_kwh"] / 1e6, "hidro_total_gwh": con_solar["hidro_total_kwh"] / 1e6, "mejora_vs_sin_solar_gwh": mejora})

    resultados.to_csv(args.salida, index=False)
    resumen_path = args.salida.replace(".csv", "_resumen.csv")
    pd.DataFrame(resumenes).to_csv(resumen_path, index=False)
    print(f"\nResultados: {args.salida}")
    print(f"Resumen: {resumen_path}")


if __name__ == "__main__":
    main()
