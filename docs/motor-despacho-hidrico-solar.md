# Motor de optimización de despacho hídrico-solar (Fase 3)

## 1. Objetivo

Fase 2 dejó un modelo que predice el caudal/aporte del embalse a un día. Fase 3 responde la siguiente pregunta: si además hubiera un parque fotovoltaico flotante sobre el embalse Peñol, ¿cuánta agua se podría dejar de turbinar cada día sin dejar de cumplir la obligación de energía firme, y cuánto sube el nivel mínimo que toca el embalse como resultado?

## 2. Qué es real y qué es simulado — esto es lo primero que hay que tener claro

**No existe hoy un proyecto de solar flotante en el embalse Peñol-Guatapé.** Todo el componente solar de este análisis es un escenario simulado sobre un recurso físico real (la irradiancia del punto). Todo lo demás — volumen del embalse, aportes de los ríos, generación de la Central Guatapé, obligación de energía firme — es dato histórico real de XM, el operador del mercado eléctrico colombiano.

| Variable | Real u observada | Simulada |
|---|---|---|
| Volumen útil del embalse Peñol (`VoluUtilDiarEner`, `PorcVoluUtilDiar`) | ✅ XM | |
| Aportes de energía de los ríos Guatapé y Nare (`AporEner`) | ✅ XM | |
| Generación real de la Central Guatapé (`Gene`) | ✅ XM | |
| Obligación de Energía Firme de la Central Guatapé (`ObligEnerFirme`) | ✅ XM | |
| Irradiancia solar en el punto del embalse | ✅ NASA POWER | |
| Generación fotovoltaica flotante | | ⚠️ Simulada (no existe el activo) |

## 3. Fuentes de datos y hallazgos reales durante la adquisición

Todas las fuentes son públicas y sin autenticación, mismo estándar del resto del proyecto.

### 3.1 API de XM (`servapibi.xm.com.co`)

Confirmado contra el catálogo oficial (`EquipoAnaliticaXM/API_XM`, `pydataxm/metricasAPI.json`) y contra el listado real de embalses/recursos (endpoint `Lists`):

- El embalse se llama `PENOL` (no "Guatapé" — ese es el nombre de la central, no del embalse, en la nomenclatura de XM).
- La central se llama, como recurso, `GUATAPE` — código `GTPE`, EPM, hidráulica, en operación desde 1972. **No confundir con `PLAYAS`**, la central aguas abajo que reutiliza el mismo caudal turbinado.

**Hallazgo real (2026-09-16, encontrado probando con `curl` antes de programar el parseo, no asumido):** para la entidad `Embalse` el filtro de la API usa el *nombre* (`PENOL`), pero para la entidad `Recurso` el filtro debe ir por el *código* (`GTPE`) — usar el nombre (`GUATAPE`) ahí devuelve una lista vacía sin ningún mensaje de error. Además, la respuesta horaria de la métrica `Gene` no trae una lista `HourlyValues` sino un diccionario `Values` con claves `Hour01`..`Hour24` más una clave `code` que no es un valor numérico y hay que excluir explícitamente al sumar.

**Unidades (verificadas, no asumidas):** la API no documenta las unidades en la respuesta. Se confirmó que `VoluUtilDiarEner`, `Gene` y `ObligEnerFirme` vienen en kWh crudos comparando el agregado `Sistema` de `VoluUtilDiarEner` (13.553.260.500 → 13.553 GWh) contra el nivel de embalses agregado que XM reporta públicamente para el país (~13.500 GWh en enero de 2026) — coinciden. `PorcVoluUtilDiar` es una fracción 0-1, no un porcentaje ya multiplicado por 100.

Se usó también `AporEner` ("Aportes Energía por Río") en vez de convertir el caudal (m³/s) del modelo de Fase 2 a energía con un factor propio — XM ya publica esa conversión con su propio modelo hidráulico oficial (cabeza, eficiencia de turbina), que es más confiable que estimar un factor ad-hoc con los datos limitados de este proyecto.

### 3.2 NASA POWER (`power.larc.nasa.gov`)

Irradiancia global horizontal diaria (`ALLSKY_SFC_SW_DWN`, kWh/m²/día) en el punto de la Presa Santa Rita (6,2611; -75,1900), mismo punto usado en la delineación de cuenca de Fase 1. Cobertura 2000-2026 completa, sin fragmentar por límites de la API (a diferencia de XM/CHIRPS). Media observada: 4,81 kWh/m²/día, consistente con la literatura de recurso solar andino colombiano.

## 4. El supuesto que más pesa: la capacidad instalada del parque solar simulado

El área real del espejo de agua del embalse Peñol-Guatapé **no está confirmada con precisión** — las fuentes consultadas difieren entre ~2.262 ha y ~74 km² según la delimitación exacta (espejo de agua vs. área de manejo DRMI de CORNARE, que incluye tierra). En vez de anclar la capacidad instalada a esa cifra no confirmada, se ancló a la **proporción real solar/hidro de proyectos ya construidos** — un enfoque menos sensible a esa incertidumbre:

| Escenario | Precedente real | Cálculo | Capacidad resultante |
|---|---|---|---|
| Piloto | Alqueva (Portugal): 5 MW, piloto pequeño real | Directo | 5 MWp |
| Intermedio | Da Mi (Vietnam): 47,5 MWp / 175 MW hidro = 27,1% | 560 MW × 27,1% | 152 MWp |
| Agresivo | Longyangxia (China): 850 MWp / 1.280 MW hidro = 66,4% | 560 MW × 66,4% | 372 MWp |

Los tres precedentes ya estaban documentados y verificados en `docs/arquitectura-y-benchmarking.md` (Fase 0). La central Guatapé tiene 560 MW de capacidad instalada (confirmado en Wikipedia y, de forma independiente, contra la generación real observada de XM: 10-13 GWh/día equivalen a un factor de planta de 75-95% sobre 560 MW, plausible para una central hidráulica de base).

**Verificación cruzada del modelo de generación FV:** el escenario intermedio (152 MWp) simula ~212 GWh/año. Da Mi, con 47,5 MWp reales (3,2 veces menos capacidad), reporta ~70 GWh/año reales. Escalando linealmente, 152 MWp deberían producir ~224 GWh/año — el modelo simulado (212 GWh/año) queda dentro de un margen razonable de esa cifra real, dando confianza en el modelo de generación (`src/modelo_solar_flotante.py`: capacidad × irradiancia × performance ratio 0,78, mismo principio de cálculo que usa PVWatts de NREL en su forma simple).

**Lo que este modelo NO incluye, a propósito:** el efecto de enfriamiento por agua que la literatura de solar flotante reporta como una ganancia de rendimiento adicional frente a paneles en tierra — se omite por conservador, no se inventa un factor. Tampoco se modela el derateo térmico horario (se descargó la temperatura T2M pero no se usó en esta primera versión).

## 5. El motor de optimización

Programación lineal (PuLP + CBC) que decide, para cada día del período analizado, cuánta energía debe turbinar la Central Guatapé para cumplir la Obligación de Energía Firme con el menor consumo posible del volumen almacenado — formalmente, **maximiza el nivel más bajo que toca el embalse durante todo el período** (variable `z`):

```
maximizar   z
sujeto a    volumen(t) = volumen(t-1) + aportes(t) - hidro(t)
            hidro(t) + solar(t) >= obligacion(t)
            0 <= hidro(t) <= capacidad_maxima_diaria   (560 MW x 24h)
            volumen(t) >= z                             para todo t
            volumen(0) = volumen inicial real
```

Ver `src/motor_despacho.py` para la implementación completa.

### 5.1 Limitación metodológica explícita — leer antes de citar resultados

**Este es un backtest de información perfecta ("oracle"), no una política operativa desplegable en tiempo real.** El LP conoce de antemano los aportes reales y la irradiancia real de todo el período que optimiza. Esto da una **cota superior** de lo que la coordinación hídrico-solar podría lograr si se tuviera un pronóstico perfecto — es el punto de partida correcto (así se hace en la literatura de coordinación hidrotérmica: primero el óptimo con información perfecta, después la política real con pronóstico e incertidumbre), pero no hay que confundirlo con un resultado desplegable.

Convertir esto en una política real de horizonte móvil (usando el pronóstico a un día del modelo de Fase 2, o construyendo un pronóstico multi-día nuevo) queda **explícitamente para trabajo futuro** — es el puente natural entre Fase 2 y una Fase 3 más madura, y una vía sólida para que otro investigador continúe desde aquí.

### 5.2 Por qué la comparación principal no es contra el historial real

El volumen histórico real del embalse refleja decisiones operativas de EPM/XM que este modelo no captura — vertimientos, la cascada Peñol-Playas-San Carlos, señales de precio de bolsa, mantenimientos. Comparar directamente contra ese historial mezclaría el efecto del solar con todos esos factores no modelados. Por eso la comparación principal es **LP-sin-solar vs. LP-con-solar, resueltas por el mismo motor** — aísla el efecto marginal real del solar. El volumen mínimo histórico real se reporta aparte, solo como referencia con esta advertencia explícita.

## 6. Resultados

Ver `docs/fase-3-resultados.md` (generado después de correr el backtest completo).

## 7. Trabajo futuro (explícitamente fuera de alcance de esta entrega)

- Política de horizonte móvil con pronóstico real (no información perfecta) — el paso natural siguiente.
- Modelo de reducción de evaporación por cobertura flotante, integrado como variable adicional de conservación de recurso (mencionado en el README desde Fase 0, sigue pendiente).
- Confirmar el área real del espejo de agua del embalse para poder anclar también un escenario de capacidad "por cobertura física", complementario al de "por proporción a precedentes reales" usado aquí.
- Programación estocástica (en vez de determinista) si se quiere capturar explícitamente la incertidumbre del pronóstico, no solo su valor esperado.
