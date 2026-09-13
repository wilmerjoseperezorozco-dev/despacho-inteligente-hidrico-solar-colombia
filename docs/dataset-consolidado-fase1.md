# Dataset consolidado de Fase 1 — cierre de la etapa de datos

## 1. Qué se consolidó

[`scripts/consolidar_dataset_fase1.py`](../scripts/consolidar_dataset_fase1.py) une las tres fuentes descargadas en Fase 1 en un único archivo diario:

- **XM** (`docs/datos-xm-aportes.md`): aportes de caudal oficiales GUATAPE y NARE, 2000-2026.
- **IDEAM** (`docs/datos-ideam-caudal.md`): caudal medio diario de 4 estaciones tributarias en la cuenca aportante.
- **CHIRPS diario** (`docs/datos-satelitales-precipitacion.md`): precipitación satelital sobre el bbox de la cuenca delineada.

Resultado: [`data/processed/dataset_fase1_diario.csv`](../data/processed/dataset_fase1_diario.csv) — 974 filas, 8 columnas.

## 2. Por qué el rango es 2024-01-01 a 2026-08-31, y no 2000-2026

El rango útil del dataset consolidado queda acotado por la fuente más corta: **CHIRPS diario**. Descargar CHIRPS diario para todo el histórico de XM/IDEAM (2000-2026, ~9.700 días) significaría transferir del orden de 25 GB — impracticable en una sesión interactiva. Se decidió deliberadamente:

- **CHIRPS diario**: solo para una ventana reciente (2024-01-01 en adelante) — suficiente para prototipar el modelo.
- **CHIRPS mensual**: para todo el histórico 2000-2026 (`data/raw/chirps_mensual/precipitacion_mensual.csv`, 320 meses) — útil para un análisis exploratorio de largo plazo o un modelo mensual, no para el modelo diario.

Esta es una decisión de alcance documentada, no una limitación oculta. Extender CHIRPS diario a todo el histórico queda como tarea futura explícita (sección 5).

## 3. Hallazgo real durante la descarga: CHIRPS diario tiene ~12 días de latencia

La descarga de CHIRPS diario hasta 2026-09-12 solo llegó hasta **2026-08-31** — los primeros 12 días de septiembre de 2026 devolvieron HTTP 404 (el archivo aún no existe en el servidor). Esto no es un error del script: CHIRPS publica su producto diario preliminar con un retraso real de aproximadamente dos semanas. Cualquier uso operativo futuro de este pipeline debe considerar esta latencia — no se puede asumir que "hoy" tiene dato satelital disponible.

## 4. Hallazgo real durante la descarga: pérdida de progreso por falta de escritura incremental (corregido)

La primera corrida de `descargar_chirps_mensual.py` (320 meses) se interrumpió por el límite de tiempo del entorno de ejecución y **perdió el 100% del progreso**, porque el script original solo escribía el CSV de salida al final, no incrementalmente. Se corrigió tanto `descargar_chirps_mensual.py` como `descargar_chirps.py` para que:

- Escriban cada fila apenas se calcula (no al final).
- Al reiniciarse, lean el CSV existente y salten las fechas ya procesadas (reanudables).

Sin esta corrección, cada interrupción habría significado empezar de cero. Se documenta aquí porque es exactamente el tipo de bug silencioso que puede pasar desapercibido si no se verifica el archivo de salida real después de cada corrida (no solo el código de salida del proceso).

## 5. Cobertura real del dataset consolidado

| Columna | Cobertura en el rango 2024-01-01 a 2026-08-31 |
|---|---|
| `xm_guatape_m3s` | 100% |
| `xm_nare_m3s` | 100% |
| `chirps_precip_mm` | 100% |
| `ideam_0023087150_m3s` (Puente Real, Río Negro) | 99,6% |
| `ideam_0023087670_m3s` (Riotex, Q. La Mosca) | 100% |
| `ideam_0023087660_m3s` (Puente La Feria, Marinilla) | 93,4% |
| `ideam_0023087690_m3s` (Bodegas, Q. Leonera) | **0%** |

La estación Bodegas aparece con 0% de cobertura en este rango porque, como ya se documentó en `docs/datos-ideam-caudal.md`, **dejó de reportar en 1998** — muy anterior a esta ventana. Se deja la columna presente mas no se elimina en silencio, para que quede explícito en el propio dataset que esa fuente no aporta nada en este periodo (mejor que borrarla sin dejar rastro).

## 6. Pendiente para Fase 2

- [ ] Decidir si el modelo de Fase 2 se entrena con este dataset diario (2024-2026, corto pero completo) o si se amplía primero descargando más años de CHIRPS diario (requiere una corrida de varias horas, ver sección 2).
- [ ] Eliminar o imputar explícitamente la columna de Bodegas (100% nula en este rango) antes de entrenar cualquier modelo.
- [ ] Aplicar la corrección de sesgo satelital-vs-estación descrita en `docs/datos-satelitales-precipitacion.md` (quantile mapping) antes de usar `chirps_precip_mm` como predictor — no se aplicó todavía, este dataset tiene el dato crudo.
- [ ] Evaluar si conviene un dataset paralelo a nivel mensual (usando `chirps_mensual` + agregación mensual de XM/IDEAM) para aprovechar los 26 años completos en un modelo de menor resolución temporal.
