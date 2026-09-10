# Despacho Inteligente Hídrico-Solar — Colombia

**Investigación aplicada para coordinar en tiempo real la generación hidroeléctrica y la solar fotovoltaica flotante sobre un mismo embalse, mediante predicción de caudal basada en microclimas andinos.**

---

## Contexto

Colombia genera cerca del 70% de su electricidad a partir de fuentes hídricas, lo que hace al sistema altamente sensible a la variabilidad climática andina: los fenómenos de El Niño y las sequías prolongadas han forzado en más de una ocasión al país a operar cerca de niveles críticos de embalse. En paralelo, ya existen en el territorio los primeros pilotos de generación solar flotante sobre los mismos embalses hidroeléctricos — EPM en El Peñol-Guatapé y el proyecto Aquasol en la represa de Urrá (Córdoba) — pero operan como instalaciones independientes, sin una capa de decisión que coordine en tiempo real cuándo generar con agua, cuándo generar con sol, y cuándo conservar el recurso hídrico.

Este proyecto investiga el diseño de esa capa de coordinación: un sistema que (1) prediga el caudal afluente a un embalse a partir de variables de microclima andino, y (2) use esa predicción para optimizar el despacho conjunto agua-sol, reduciendo además la evaporación natural del embalse mediante la cobertura fotovoltaica flotante.

Es un proyecto en **etapa de investigación**, con vocación de convertirse en una propuesta técnica formal para actores del sector (operadores de embalse, UPME, academia) una vez validada la hipótesis con datos históricos públicos.

---

## Problema técnico

1. **Predicción de caudal**: los modelos hidrológicos nacionales (IDEAM) operan a escala de cuenca y con fines de alerta, no de despacho operativo diario de una central específica.
2. **Coordinación hídrico-solar**: los pilotos de solar flotante en Colombia son estáticos — generan energía, pero no existe públicamente un motor de optimización que decida, embalse por embalse y en tiempo real, la mezcla óptima de generación para minimizar riesgo de vaciado y maximizar aprovechamiento solar.
3. **Evaporación**: la cobertura flotante reduce evaporación por sombreado, pero su efecto no ha sido modelado junto con la operación hídrica como una sola variable de decisión.

---

## Componentes técnicos

### 1. Modelo de predicción de caudal (microclimas andinos)
Modelo de aprendizaje automático (arquitecturas candidatas: LSTM / Gradient Boosting sobre series temporales) entrenado con series históricas de precipitación, temperatura y caudal de estaciones IDEAM en la cuenca de interés, con el objetivo de generar pronósticos de caudal afluente a corto y mediano plazo por microcuenca.

### 2. Motor de optimización de despacho hídrico-solar
Algoritmo de optimización (programación estocástica / control predictivo) que, dado el pronóstico de caudal y la generación solar esperada, recomienda la mezcla de despacho que minimiza el riesgo de vaciado crítico del embalse y maximiza la energía firme entregada.

### 3. Modelo de reducción de evaporación
Cuantificación del efecto de la cobertura fotovoltaica flotante sobre la tasa de evaporación del embalse, integrado como variable adicional de conservación de recurso dentro del motor de optimización.

---

## Antecedentes y referentes (no se parte de cero)

| Referente | Aporte | Lo que no resuelve |
|---|---|---|
| IDEAM — Modelación hidrológica nacional | Series históricas y modelos de cuenca | No opera a nivel de despacho diario de una central |
| EPM — Piloto solar flotante El Peñol-Guatapé | Primer piloto de la región, meta de escalar al 10% del área del embalse | Generación estática, sin coordinación con el nivel del embalse |
| Aquasol — Urrá, Córdoba (2023) | Mayor planta flotante de la región (1,5 MWp) | Mismo caso: sin motor de despacho conjunto |
| UPME / CREG | Marco regulatorio y de planeación del sistema eléctrico | No existe lineamiento específico de coordinación hídrico-solar en tiempo real |

---

## Fuentes de datos previstas

- IDEAM (hidrología y clima — datos abiertos)
- XM (operador del mercado eléctrico — series de generación y embalses)
- UPME (planeación energética, atlas de recursos)
- Literatura académica sobre despacho hidro-solar híbrido (fuera de Colombia, para contraste metodológico)

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

- Validación del modelo de predicción de caudal contra registros históricos reales (no simulados)
- Comparación del motor de despacho contra la operación real observada en un embalse de referencia (backtesting)
- Declaración explícita de supuestos e incertidumbre en cada pronóstico
- Ningún resultado se presenta como recomendación operativa hasta validación con datos reales

---

## Estado del proyecto

| Fase | Descripción | Estado |
|---|---|---|
| Fase 0 — Marco y alcance | Investigación preliminar, selección de línea prioritaria, definición de alcance | ✅ Completada |
| Fase 1 — Datos y estado del arte | Recolección de series IDEAM/XM, revisión de literatura de despacho hidro-solar | ⏳ En progreso |
| Fase 2 — Modelo de predicción de caudal | Entrenamiento y validación del modelo con datos históricos | ⏳ Pendiente |
| Fase 3 — Motor de optimización de despacho | Diseño y simulación del algoritmo de coordinación hídrico-solar | ⏳ Pendiente |
| Fase 4 — Validación y propuesta | Backtesting, documentación técnica y propuesta formal a actores del sector | ⏳ Pendiente |

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

## Licencia

Por definir. Contenido de investigación en desarrollo activo.
