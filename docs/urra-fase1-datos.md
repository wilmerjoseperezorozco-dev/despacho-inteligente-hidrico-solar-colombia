# Réplica en Urrá I (issue #14) — Fase 1: datos

Aplicación del framework de despacho hídrico-solar al embalse Urrá I (río Sinú, Córdoba), siguiendo exactamente la misma metodología ya validada para Peñol-Guatapé — mismas fuentes públicas sin autenticación, mismo estándar de verificación antes de programar el parseo.

## 1. Entidades confirmadas en el catálogo de XM

Verificado con `curl` directo contra `POST https://servapibi.xm.com.co/Lists` antes de programar el descargador (`scripts/descargar_xm_urra.py`), igual que se hizo para Guatapé:

| Entidad | Filtro | Tipo |
|---|---|---|
| Río | `SINU URRA` | `AporCaudal`, `AporEner` — filtro por Name |
| Embalse | `URRA1` | `VoluUtilDiarEner`, `PorcVoluUtilDiar` — filtro por Name |
| Recurso hidráulico | `URA1` (código) | `Gene`, `ObligEnerFirme` — Central Urrá I, 340 MW (4×85 MW), EPM-Urrá S.A., en operación desde 2000-02-14 |
| Recurso solar | `PSUA` "PARQUE SOLAR URRA" (código) | `Gene` — **generación real medida**, no simulada |

## 2. Hallazgo importante: generación solar real, pero con una identidad sin confirmar del todo

El recurso `PSUA` está **despachado centralmente** en XM desde 2025-01-31 (estado "PRUEBAS" al momento de esta consulta) — a diferencia de Guatapé, donde todo el componente solar tuvo que simularse desde cero, en Urrá existe una serie de generación solar real que puede usarse para calibrar el modelo.

Sin embargo, **no se pudo confirmar con certeza a qué proyecto físico corresponde exactamente `PSUA`**:

- Se confirmó por separado, contra el mismo catálogo, que **INTI I** (código `4XQ2`, 9,9 MW, en tierra, La Apartada, inaugurado mayo 2025) e **INTI II** (código `5UHA`, en pruebas desde sep-2025) son recursos **distintos** de `PSUA` — ninguno de los dos está "despachado centralmente" en XM, a diferencia de `PSUA`.
- Por eliminación y por su fecha de alta (anterior a INTI I/II), `PSUA` podría ser **Aquasol** (el piloto flotante de 1,5 MW inaugurado en 2023) — sería consistente con que esté despachado centralmente, al compartir la subestación de la propia Central Urrá I (a diferencia de INTI I/II, que se conectan a la subestación de Caucasia de EPM).
- **Pero la magnitud de generación observada no cuadra con esa hipótesis**: los días de julio-agosto 2026 muestran 62.000-87.000 kWh/día, lo que implica una capacidad instalada del orden de 15-17 MWp (asumiendo el mismo modelo de generación de `src/modelo_solar_flotante.py`) — **~10 veces más que los 1,5 MW reportados públicamente para Aquasol**.

**No se fuerza una conclusión.** Se documenta la incertidumbre: `PSUA` es real, mide generación solar real, y probablemente está asociado al embalse (por estar despachado centralmente junto con la central hidráulica), pero su identidad exacta y su capacidad real quedan sin confirmar — a verificar directamente con Urrá S.A. o un reporte técnico primario antes de usar esta serie como si fuera "Aquasol, 1,5 MW" sin más.

**Dato adicional real, no anticipado en la investigación de Fase 0**: Urrá S.A. tiene en marcha una expansión solar mucho mayor de lo que documentamos originalmente — INTI I (9,9 MW, ya operando), INTI II (segunda fase, en pruebas), y un proyecto de **90 MW** en desarrollo (fuente: Energía Estratégica, sin detalle técnico verificado más allá del titular). Esto es consistente con el orden de magnitud del escenario "intermedio" que ya habíamos calculado por proporción a Da Mi (~92 MWp) para Guatapé aplicado a Urrá — una coincidencia real que vale la pena señalar, no una validación causal.

## 3. Cuenca aportante (delineación automática)

Mismo método que Guatapé (SRTM 30m + pysheds, `scripts/delinear_cuenca.py`), punto de desfogue: coordenada del muro de la presa Urrá I (7,94; -76,29), confirmada contra el infobox de Wikipedia del embalse (junto con capacidad 340 MW y superficie del embalse 77 km² — a diferencia de Guatapé, aquí la superficie del embalse sí está confirmada con una única fuente consistente, sin la ambigüedad de cifras que tuvimos allá).

**Resultado: 2.794,1 km²** (`data/processed/cuencas/cuenca_preliminar_urra-i.geojson`, marcado `PRELIMINAR`, igual criterio que Guatapé). No se encontró una fuente primaria (CVS, ANLA o Urrá S.A.) que publique la cifra exacta de área de cuenca aportante para contrastar — se intentó, sin éxito, en dos búsquedas. La única cifra encontrada (~13.000 km²) corresponde a la cuenca completa del río Sinú hasta su desembocadura, no a la cuenca aportante al embalse — no son comparables directamente, pero como referencia de orden de magnitud, 2.794 km² siendo ~21% de la cuenca total es geométricamente razonable para un embalse situado en la parte alta/montañosa del río (Parque Nacional Natural Paramillo).

## 4. Estaciones IDEAM de caudal en la cuenca del Alto Sinú

Encontradas 63 estaciones IDEAM dentro del bbox de la cuenca delineada; de ellas, solo 7 tienen la variable de caudal medio diario (`Q_MEDIA_D`) publicada. Descargadas y evaluadas las 6 más relevantes (`scripts/descargar_ideam_caudal.py --codigos ...`, resumen en `data/processed/ideam/resumen_calidad_caudal_urra.csv`):

| Código | Nombre | Corriente | Período | Cobertura | Estado actual |
|---|---|---|---|---|---|
| `0013037040` | CARRIZOLA | Sinú | 1993-2026 | 83,4% | **Activa — única estación útil para el período objetivo 2000-2026** |
| `0013047040` | TORO EL | Sinú | 1991-2010 | 88,2% | Suspendida antes del final del período objetivo |
| `0013037010` | ANGOSTURA DE URRA | Sinú | 1959-1995 | 91,2% | Suspendida antes de 2000 |
| `0013017020` | LIMON EL | Sinú | 1966-1998 | 82,2% | Suspendida antes de 2000 |
| `0013027010` | ESMERALDA LA | Esmeralda (tributario) | 1991-2000 | 87,7% | Se traslapa apenas con el inicio del período objetivo |
| `0013017030` | SALTO VIEJO | Sinú | 1974-1982 | 28,0% | Fuera del período objetivo, cobertura baja |

**Hallazgo honesto, mismo patrón que Guatapé (allá fue la estación Bodegas):** de 6 estaciones candidatas, solo **CARRIZOLA** cubre realmente el período 2000-2026 con buena cobertura. Esto deja al modelo de Urrá con un solo predictor tributario IDEAM (en vez de los 3 usables que tuvo Guatapé) — una limitación real que se documentará en los resultados del modelo, no se oculta.

## 5. Precipitación satelital e irradiancia solar

- **CHIRPS diario** (`scripts/descargar_chirps.py --bbox -76.52 7.54 -75.95 8.16`): descarga 2000-2026 en curso al momento de escribir este documento (mismo proceso lento de siempre, ~horas, reanudable si se interrumpe).
- **Irradiancia solar NASA POWER** (`scripts/descargar_solar_power.py --lat 7.94 --lon -76.29 --nombre urra`): completado, 9.740 días. Media 4,29 kWh/m²/día — **algo menor que Peñol-Guatapé (4,81)**, un hallazgo real e inicialmente contraintuitivo (Córdoba es más tropical/costero que el altiplano antioqueño), consistente con mayor cobertura de nubosidad en la cuenca del Alto Sinú (bosque húmedo tropical, Parque Nacional Paramillo).

## 6. Próximos pasos (Fase 2 y 3 para Urrá)

1. Terminar las descargas en curso (CHIRPS, historial completo de XM).
2. Consolidar dataset diario (análogo a `scripts/consolidar_dataset_fase1.py`, adaptado a un solo río).
3. Entrenar el modelo de predicción de caudal/energía reutilizando `src/modelo_gbm_regularizado.py` sin cambios de arquitectura (ya es genérico vía `--objetivo`).
4. Correr el motor de despacho (`src/motor_despacho.py`, también genérico) — con la ventaja adicional de poder validar el escenario "solar" contra la generación real de `PSUA` en el tramo donde ambas series se solapan (jul-ago 2026 en adelante), algo que no fue posible hacer para Guatapé.
