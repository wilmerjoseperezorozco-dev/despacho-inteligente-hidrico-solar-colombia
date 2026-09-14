# Despacho Inteligente Hídrico-Solar — Colombia

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22757736.svg)](https://doi.org/10.5281/zenodo.22757736)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Investigación aplicada para coordinar en tiempo real la generación hidroeléctrica y la solar fotovoltaica flotante sobre un mismo embalse, mediante predicción de caudal basada en microclimas andinos.**

*[Read this in English ↓](#english-version)*

---

## Contexto

Colombia genera cerca del 70% de su electricidad a partir de fuentes hídricas, lo que hace al sistema altamente sensible a la variabilidad climática andina: los fenómenos de El Niño y las sequías prolongadas han forzado en más de una ocasión al país a operar cerca de niveles críticos de embalse. En paralelo, ya existen en el territorio los primeros pilotos de generación solar flotante sobre los mismos embalses hidroeléctricos — EPM en El Peñol-Guatapé y el proyecto Aquasol en la represa de Urrá (Córdoba) — pero operan como instalaciones independientes, sin una capa de decisión que coordine en tiempo real cuándo generar con agua, cuándo generar con sol, y cuándo conservar el recurso hídrico.

Este proyecto investiga el diseño de esa capa de coordinación: un sistema que (1) prediga el caudal afluente a un embalse a partir de variables de microclima andino, y (2) use esa predicción para optimizar el despacho conjunto agua-sol, reduciendo además la evaporación natural del embalse mediante la cobertura fotovoltaica flotante.

Es un proyecto en **etapa de investigación**, con vocación de convertirse en una propuesta técnica formal para actores del sector (operadores de embalse, UPME, academia) una vez validada la hipótesis con datos históricos públicos.

**Motivación adicional (2026-09-13):** la demanda eléctrica de la inteligencia artificial está creciendo más rápido que la capacidad de generación firme disponible globalmente, y los grandes compradores de energía ya buscan específicamente "clean firm power" — exactamente lo que este sistema está diseñado para producir. Ver [`docs/oportunidad-demanda-ia-energia.md`](docs/oportunidad-demanda-ia-energia.md) para el análisis completo, con cifras verificadas de Colombia, precedentes internacionales (Paraguay) y el contexto de ritmo/prudencia con el que la propia industria de IA está pidiendo avanzar.

## Artículo

El trabajo hasta la fecha (Fases 0-2) está consolidado como manuscrito en formato de artículo científico: [`despacho-hidrico-solar-guatape-articulo.docx`](despacho-hidrico-solar-guatape-articulo.docx). Incluye revisión de antecedentes (incl. el precedente directo de Poveda et al. 2001 sobre el río Nare), metodología completa, resultados con métricas reales (NSE/KGE/PBIAS), discusión honesta de limitaciones, y contexto de la demanda energética global hacia 2030.

---

## Proceso de investigación y hallazgos clave

Esta sección resume, en orden cronológico, qué se hizo, qué se encontró, y por qué se tomó cada decisión — el detalle completo de cada paso está en `docs/`, pero el objetivo aquí es que no haya que reconstruir la historia leyendo 20 documentos.

### Fase 0 — Por qué esta línea y no otra

Se evaluaron 5 líneas de aprovechamiento energético con IA en Colombia (predicción de caudal, coordinación hídrico-solar, inspección de transmisión, pérdidas de distribución, biomasa/geotermia). Se priorizó la coordinación hídrico-solar por ser el vacío más claro y demostrable: los pilotos de EPM (Guatapé) y Aquasol (Urrá) ya existen físicamente, pero **ninguno tiene una capa de decisión que coordine agua y sol en tiempo real** — verificado revisando la literatura y prensa especializada disponible, no asumido. Comparación internacional verificada: de los pocos precedentes globales con coordinación real (no solo generación estática), solo China (Longyangxia) y Portugal (Alqueva) califican — el vacío es real incluso fuera de Colombia.

### Fase 1 — Datos: qué se encontró y qué hubo que corregir

Se identificaron y verificaron **tres fuentes oficiales de acceso público**, ninguna documentada previamente como tal en la literatura consultada:

- **XM** (operador del mercado eléctrico): endpoint histórico público sin autenticación (`servapibi.xm.com.co`), serie "Aportes Caudal por Río" desde el año 2000.
- **IDEAM**: bucket S3 público sin autenticación (`datos.ideam.gov.co`) para caudal medio diario; **no publica un producto diario curado de precipitación** (solo acumulado crudo cada 10 min), lo que justificó usar precipitación satelital.
- **CHIRPS** (precipitación satelital, UC Santa Bárbara): 0,05° de resolución, dominio público.

**La cuenca aportante** se delineó de forma automática (modelo digital de elevación SRTM + algoritmo de flujo D8), y se validó con una coordenada real de la Presa Santa Rita aportada externamente — confirmada de forma independiente al coincidir exactamente con la coordenada del infobox de Wikipedia para el embalse.

**Errores reales encontrados y corregidos durante la descarga de datos:**
- Dos scripts de descarga no escribían resultados de forma incremental — una corrida completa de varios cientos de días **se perdió entera** al interrumpirse por un límite de tiempo, antes de corregirlo con escritura incremental y reanudación automática.
- El primer intento de delinear la cuenca con un punto de entrada aproximado dio un área de 2 km² (absurdo para un embalse de esta escala) — corregido ajustando el punto a la celda de mayor acumulación de flujo.
- XM renombró silenciosamente el río "Nare" a "Nare CP" entre 2023 y 2024 sin traslape de fechas — detectado por una asimetría en el conteo de registros, no documentado por XM en ninguna parte.

El dataset diario consolidado se extendió de 974 días (2024-2026) a **9.740 días consecutivos (2000-2026, 100% de cobertura, cero huecos)** — verificado explícitamente, no asumido.

### Fase 2 — Modelado: la evolución honesta, con resultados negativos incluidos

| Paso | Qué se hizo | Resultado |
|---|---|---|
| Baseline (persistencia y climatología) | Validación *walk-forward*, métricas hidrológicas estándar (NSE, KGE, PBIAS) | Guatapé: persistencia con NSE negativo (río con crecidas abruptas); Nare: persistencia ya fuerte (NSE 0,36 en el dataset corto) |
| Gradient Boosting v1 | Primer modelo de ML con precipitación y tributarios como predictores | Mejora en Guatapé; **empeora** en Nare frente a la persistencia — sobreajuste real detectado (gap train-test > 0,3) |
| Gradient Boosting v2 (regularizado) | Regularización L2 nativa + búsqueda de hiperparámetros por validación cruzada temporal | La búsqueda no encontró ninguna configuración con gap < 0,3 → diagnóstico: el sobreajuste era **limitación de volumen de datos**, no de configuración |
| Extensión del dataset (10x) | CHIRPS diario completo 2000-2026 | Confirmado: el gap bajó de 0,42-0,48 a 0,12-0,16 sin cambiar una línea de código |
| Corrección de un bug real | El modelo nunca incluía el caudal del **propio día** como predictor (solo ayer, antier, hace 3 días) — la persistencia sí lo usa | **NARE supera a la persistencia por primera vez en todo el proyecto** (NSE 0,833 vs. 0,815) |
| Experimento Riotex | Una estación tributaria mostró importancia negativa con el dataset corto → se removió → con el dataset extendido, la conclusión **no se sostuvo** → se revirtió | Lección metodológica: no generalizar de una muestra pequeña, documentado en su momento y confirmado después |
| Modelo de picos (clasificación de crecida + magnitud) | Enfoque de dos etapas para los eventos extremos que la regresión directa subestima | No superó a la regresión simple ya corregida — cerrado como *not planned*, con la causa (bajo recall del clasificador) documentada |

### Métricas vigentes (dataset completo 2000-2026, mismo período de prueba 2021-2026)

| Río | Modelo | NSE | KGE | PBIAS |
|---|---|---|---|---|
| Guatapé | Persistencia | -0,04 | 0,48 | 0,1% |
| **Guatapé** | **Gradient Boosting (corregido)** | **0,272** | 0,32 | 1,0% |
| Nare | Persistencia | 0,815 | 0,91 | 0,1% |
| **Nare** | **Gradient Boosting + log1p (corregido)** | **0,833** | 0,82 | 1,2% |

Fuente y metodología completas: [`docs/bug-q-hoy-faltante.md`](docs/bug-q-hoy-faltante.md) (números vigentes) y [`docs/dataset-extendido-2000-2026.md`](docs/dataset-extendido-2000-2026.md) (contexto del dataset).

### Todos los errores reales encontrados y corregidos en este proyecto

Se documentan explícitamente porque son tan parte del resultado como las métricas — cada uno tiene su commit y su documento:

1. Pérdida completa de una corrida de descarga por escritura no incremental (corregido con reanudación automática).
2. Ventana de prueba inconsistente entre modelos por un hueco de reporte en una estación IDEAM (corregido con imputación explícita).
3. Renombre silencioso de una entidad en la API de XM ("Nare" → "Nare CP"), detectado por asimetría de datos, no documentado por la fuente.
4. Conclusión sobre una variable predictora (Riotex) que no se replicó al escalar los datos — revertida explícitamente.
5. **Bug de mayor impacto**: el caudal del día actual nunca se incluía como predictor, pese a ser la señal más obviamente útil — corregido, cambia el resultado principal del proyecto (Nare pasa a superar la persistencia).
6. Un archivo vacío colado accidentalmente en un commit público, encontrado en auditoría y eliminado.
7. Licencia declarada en `CITATION.cff` sin archivo `LICENSE` físico — corregido.

---

## Problema técnico

1. **Predicción de caudal**: los modelos hidrológicos nacionales (IDEAM) operan a escala de cuenca y con fines de alerta, no de despacho operativo diario de una central específica.
2. **Coordinación hídrico-solar**: los pilotos de solar flotante en Colombia son estáticos — generan energía, pero no existe públicamente un motor de optimización que decida, embalse por embalse y en tiempo real, la mezcla óptima de generación para minimizar riesgo de vaciado y maximizar aprovechamiento solar.
3. **Evaporación**: la cobertura flotante reduce evaporación por sombreado, pero su efecto no ha sido modelado junto con la operación hídrica como una sola variable de decisión.

---

## Componentes técnicos

### 1. Modelo de predicción de caudal (microclimas andinos)
Modelo de aprendizaje automático (Gradient Boosting sobre series temporales, con caudal rezagado, precipitación satelital y estaciones tributarias como predictores) entrenado con series históricas de precipitación, temperatura y caudal en la cuenca de interés, con el objetivo de generar pronósticos de caudal afluente a corto plazo.

### 2. Motor de optimización de despacho hídrico-solar
Algoritmo de optimización (programación estocástica / control predictivo) que, dado el pronóstico de caudal y la generación solar esperada, recomienda la mezcla de despacho que minimiza el riesgo de vaciado crítico del embalse y maximiza la energía firme entregada. *(Pendiente de Fase 3.)*

### 3. Modelo de reducción de evaporación
Cuantificación del efecto de la cobertura fotovoltaica flotante sobre la tasa de evaporación del embalse, integrado como variable adicional de conservación de recurso dentro del motor de optimización. *(Pendiente de Fase 3.)*

---

## Antecedentes y referentes (no se parte de cero)

| Referente | Aporte | Lo que no resuelve |
|---|---|---|
| Poveda et al. (2001), Universidad Nacional de Colombia | Predicción no lineal de caudales mensuales del mismo río Nare | Resolución mensual, sin precipitación satelital ni objetivo de coordinación con solar |
| IDEAM — Modelación hidrológica nacional | Series históricas y modelos de cuenca | No opera a nivel de despacho diario de una central |
| EPM — Piloto solar flotante El Peñol-Guatapé | Primer piloto de la región, meta de escalar al 10% del área del embalse | Generación estática, sin coordinación con el nivel del embalse |
| Aquasol — Urrá, Córdoba (2023) | Mayor planta flotante de la región (1,5 MWp) | Mismo caso: sin motor de despacho conjunto |
| UPME / CREG | Marco regulatorio y de planeación del sistema eléctrico | No existe lineamiento específico de coordinación hídrico-solar en tiempo real |

---

## Fuentes de datos (verificadas y en uso)

- **IDEAM** — caudal medio diario (bucket S3 público) e hidrología de referencia.
- **XM** — aportes de caudal oficiales por río, mercado eléctrico mayorista (endpoint histórico público).
- **CHIRPS** — precipitación satelital diaria y mensual (UC Santa Bárbara, dominio público).
- **UPME** — planeación energética, atlas de recursos (contexto, no todavía integrado como serie de entrenamiento).

---

## Alianzas institucionales potenciales

| Institución | Rol previsto |
|---|---|
| IDEAM | Series hidroclimáticas de referencia |
| XM | Datos de operación y generación del SIN |
| UPME | Contraste de política energética y viabilidad |
| Academia (grupos de energía de universidades colombianas) | Validación metodológica |

---

## Rigor metodológico

- Validación *walk-forward* contra registros históricos reales (no simulados), nunca split aleatorio en series de tiempo.
- Métricas hidrológicas estándar (NSE, KGE y sus componentes, PBIAS) en vez de solo error cuadrático genérico.
- Búsqueda de hiperparámetros por validación cruzada temporal, sin tocar nunca el período de prueba.
- Cada resultado negativo o hallazgo que contradice una hipótesis previa se documenta explícitamente, no se descarta ni se oculta (ver la sección de errores reales arriba).
- Ningún resultado se presenta como recomendación operativa hasta validación adicional.

---

## Estado del proyecto

| Fase | Descripción | Estado |
|---|---|---|
| Fase 0 — Marco y alcance | Investigación preliminar, selección de línea prioritaria, definición de alcance | ✅ Completada |
| Fase 1 — Datos y estado del arte | Series XM/IDEAM/CHIRPS, delineación de cuenca, dataset consolidado | ✅ Completada — 9.740 días (2000-2026), 100% de cobertura |
| Fase 2 — Modelo de predicción de caudal | Entrenamiento y validación con datos históricos | ✅ Completada — Nare supera a la persistencia (NSE 0,833 vs 0,815); Guatapé en NSE 0,272; ver [`docs/fase-2-cierre.md`](docs/fase-2-cierre.md) |
| Fase 3 — Motor de optimización de despacho | Diseño y simulación del algoritmo de coordinación hídrico-solar | ⏳ Pendiente |
| Fase 4 — Validación y propuesta | Backtesting, documentación técnica y propuesta formal a actores del sector | ⏳ Pendiente |

Issues públicos de trabajo pendiente concreto: [ver issues abiertos](https://github.com/wilmerjoseperezorozco-dev/despacho-inteligente-hidrico-solar-colombia/issues).

---

## Estructura del repositorio

```
despacho-inteligente-hidrico-solar-colombia/
├── docs/           # Investigación, hallazgos y documentación técnica
├── data/
│   ├── raw/        # Datos crudos descargados (no versionados)
│   └── processed/  # Datos procesados para modelado
├── notebooks/      # Exploración y prototipado
├── src/            # Código fuente del modelo y del motor de optimización
├── scripts/        # Scripts de ingesta y automatización
└── tests/          # Pruebas
```

---

## Cómo citar

Este repositorio está archivado permanentemente en Zenodo. Para citar el proyecto en general (apunta siempre a la última versión), usar el DOI de concepto `10.5281/zenodo.22757736`; para citar esta versión específica (v0.1.1), usar `10.5281/zenodo.22757737`. También se puede usar el botón "Cite this repository" de GitHub (lee automáticamente `CITATION.cff`).

## Licencia

MIT — ver [`LICENSE`](LICENSE). Contenido de investigación en desarrollo activo.

---

<a id="english-version"></a>
## English version

**Applied research on real-time coordination between hydropower generation and floating photovoltaic solar on the same reservoir, using streamflow prediction based on Andean microclimates.**

### Context

Colombia generates roughly 70% of its electricity from hydropower, making the national grid highly sensitive to Andean climate variability — El Niño events and prolonged droughts have repeatedly pushed the country close to critical reservoir levels. At the same time, Colombia already has the region's first floating solar pilots installed directly on hydropower reservoirs — EPM at El Peñol-Guatapé and the Aquasol project at Urrá (Córdoba) — but both operate as independent installations, with no decision layer coordinating in real time when to generate with water, when to generate with sun, and when to conserve the water resource.

This project investigates the design of that coordination layer: a system that (1) predicts inflow to a reservoir from Andean microclimate variables, and (2) uses that prediction to optimize joint water-solar dispatch, also reducing natural reservoir evaporation via the floating photovoltaic cover.

This is a **research-stage** project, intended to become a formal technical proposal for sector actors (reservoir operators, UPME, academia) once the hypothesis is validated against public historical data.

**Additional motivation (2026-09-13):** global AI electricity demand is growing faster than available firm generation capacity, and large energy buyers are specifically seeking "clean firm power" — exactly what this system is designed to produce. See [`docs/oportunidad-demanda-ia-energia.md`](docs/oportunidad-demanda-ia-energia.md) (Spanish) for the full analysis with verified figures.

### Research process and key findings

**Phase 0 — Why this line of research.** Five lines of AI-driven energy research for Colombia were evaluated; hydro-solar dispatch coordination was prioritized because it is a clear, demonstrable gap: Colombia's existing floating solar pilots (EPM Guatapé, Aquasol Urrá) are real but **static** — none coordinates water and sun dispatch in real time. Verified internationally too: of the few global precedents with genuine coordination (not just co-located generation), only China's Longyangxia and Portugal's Alqueva plant qualify.

**Phase 1 — Data.** Three official, publicly accessible data sources were identified and verified, none previously documented as such: **XM** (market operator, public historical endpoint, no auth, daily river inflow since 2000), **IDEAM** (public S3 bucket, no auth, daily mean streamflow — but no curated daily precipitation product, which is why satellite precipitation was needed), and **CHIRPS** (satellite precipitation, public domain, 0.05° resolution). The contributing watershed was automatically delineated (SRTM elevation model + D8 flow algorithm) and validated against a real dam-wall coordinate that independently matched Wikipedia's own infobox coordinate for the reservoir.

**Real bugs found and fixed during data acquisition:** two download scripts did not write results incrementally — an entire multi-hundred-day run was **lost completely** when interrupted, before being fixed with incremental writes and automatic resume. XM silently renamed the "Nare" river entity to "Nare CP" between 2023 and 2024 with no date overlap — caught by a record-count asymmetry, not documented anywhere by the source. The daily consolidated dataset was extended from 974 days (2024-2026) to **9,740 consecutive days (2000-2026, 100% coverage, zero gaps)** — explicitly verified, not assumed.

**Phase 2 — Modeling: the honest evolution, negative results included.**

| Step | What was done | Result |
|---|---|---|
| Baseline (persistence & climatology) | Walk-forward validation, standard hydrology metrics (NSE, KGE, PBIAS) | Guatapé: negative NSE for persistence (flashy river); Nare: persistence already strong |
| Gradient Boosting v1 | First ML model with precipitation and tributaries as predictors | Improves Guatapé; **worsens** Nare vs. persistence — real overfitting detected (train-test NSE gap > 0.3) |
| Gradient Boosting v2 (regularized) | Native L2 regularization + hyperparameter search via time-series cross-validation | No configuration closed the gap below 0.3 → diagnosis: overfitting was a **data-volume limitation**, not a configuration issue |
| Dataset extension (10x) | Full daily CHIRPS 2000-2026 | Confirmed: gap dropped from 0.42-0.48 to 0.12-0.16 with zero code changes |
| Real bug fixed | The model never included **today's own flow** as a predictor (only yesterday, day before, 3 days before) — persistence correctly uses it | **Nare beats persistence for the first time in the project** (NSE 0.833 vs. 0.815) |
| Riotex experiment | One tributary station showed negative importance on the short dataset → removed → did not replicate on the extended dataset → reverted | Methodological lesson: don't generalize from a small test window — documented at the time and confirmed later |
| Peak/flood model (classification + conditional magnitude) | Two-stage approach for extreme events that direct regression underestimates | Did not beat the corrected simple regression — closed as *not planned*, with root cause (low classifier recall) documented |

**Current metrics (full 2000-2026 dataset, same 2021-2026 test period):**

| River | Model | NSE | KGE | PBIAS |
|---|---|---|---|---|
| Guatapé | Persistence | -0.04 | 0.48 | 0.1% |
| **Guatapé** | **Gradient Boosting (fixed)** | **0.272** | 0.32 | 1.0% |
| Nare | Persistence | 0.815 | 0.91 | 0.1% |
| **Nare** | **Gradient Boosting + log1p (fixed)** | **0.833** | 0.82 | 1.2% |

Full methodology: [`docs/bug-q-hoy-faltante.md`](docs/bug-q-hoy-faltante.md) (Spanish — current numbers) and [`docs/dataset-extendido-2000-2026.md`](docs/dataset-extendido-2000-2026.md).

**All real bugs found and fixed in this project** (documented because they are as much part of the result as the metrics): (1) complete loss of a download run from non-incremental writes, fixed with auto-resume; (2) inconsistent test window across models from an IDEAM station reporting gap, fixed with explicit imputation; (3) a silent entity rename in the XM API ("Nare" → "Nare CP"), caught by a data asymmetry, undocumented by the source; (4) a predictor-variable conclusion (Riotex) that did not replicate at scale — explicitly reverted; (5) **highest-impact bug**: today's own flow was never included as a predictor despite being the most obviously useful signal — fixed, and it changes the project's headline result; (6) an empty file accidentally committed to the public repo, found in audit and removed; (7) a license declared in `CITATION.cff` with no physical `LICENSE` file — fixed.

### Technical problem

1. **Streamflow prediction**: national hydrological models (IDEAM) operate at basin scale for alert purposes, not daily operational dispatch of a specific plant.
2. **Hydro-solar coordination**: Colombia's floating solar pilots are static — they generate energy, but no publicly known optimization engine decides, reservoir by reservoir and in real time, the optimal generation mix to minimize drawdown risk and maximize solar use.
3. **Evaporation**: floating cover reduces evaporation through shading, but this effect has not been modeled jointly with water operations as a single decision variable.

### Repository structure

```
despacho-inteligente-hidrico-solar-colombia/
├── docs/           # Research, findings, and technical documentation
├── data/
│   ├── raw/        # Downloaded raw data (not versioned)
│   └── processed/  # Processed data for modeling
├── notebooks/      # Exploration and prototyping
├── src/            # Model and dispatch-optimization source code
├── scripts/        # Ingestion and automation scripts
└── tests/          # Tests
```

### How to cite

This repository is permanently archived on Zenodo. Cite the project in general with the concept DOI `10.5281/zenodo.22757736` (always resolves to the latest version), or this specific version (v0.1.1) with `10.5281/zenodo.22757737`. GitHub's "Cite this repository" button also works (reads `CITATION.cff` automatically).

### License

MIT — see [`LICENSE`](LICENSE). Active research project.
