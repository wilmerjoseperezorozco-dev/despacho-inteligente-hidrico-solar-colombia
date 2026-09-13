# Aportes hídricos oficiales de XM — la mejor variable objetivo encontrada hasta ahora

## 1. Qué es y por qué es mejor que una estación aislada

XM (operador del Sistema Interconectado Nacional) publica diariamente los **"Aportes de Caudal por Río"** — el caudal atribuido operativamente a cada río del sistema hidroeléctrico colombiano, que es la métrica que el propio operador usa para tomar decisiones reales de despacho. A diferencia de una estación limnimétrica aislada (que mide un punto específico de un afluente), esta serie representa el aporte hídrico consolidado que XM le atribuye al embalse — es, literalmente, el dato que ya usa la industria para lo que este proyecto quiere predecir.

Se encontraron y verificaron series para **GUATAPE** y **NARE** — los dos ríos que alimentan directamente el embalse Peñol-Guatapé — con datos diarios desde el año 2000 hasta el presente (26+ años).

## 2. Cómo se encontró el acceso

El portal moderno de datos abiertos de XM (SiMEM, `simem.co`) no tiene un dataset tabular directo para esta métrica bajo un ID fácil de adivinar. Se encontró en su lugar el repositorio oficial `EquipoAnaliticaXM/API_XM` en GitHub, que contiene el paquete `pydataxm` — la librería oficial de XM para consultar su **API histórica** (anterior a SiMEM, todavía activa y pública).

- Catálogo de métricas: `pydataxm/metricasAPI.json` (JSON doblemente codificado; confirma la métrica `AporCaudal` = "Aportes Caudal por Río", entidad `Rio`, periodicidad diaria)
- Endpoint verificado: `POST https://servapibi.xm.com.co/daily`
- Cuerpo de la solicitud: `{"MetricId": "AporCaudal", "StartDate": "...", "EndDate": "...", "Entity": "Rio", "Filter": ["GUATAPE", "NARE"]}`
- **Sin autenticación requerida.**
- Límite real de la API: ~31 días por solicitud (igual al límite que la propia librería oficial `pydataxm` respeta internamente, fragmentando por mes calendario).

## 3. Hallazgo real durante la descarga: XM renombró el río "NARE" a "NARE CP"

La primera corrida (filtrando solo por `"NARE CP"`) devolvió apenas 1.108 registros contra 9.745 de `"GUATAPE"` — una asimetría que no tenía explicación hidrológica y que se investigó en vez de ignorarse. Se confirmó, consultando año por año, que:

- **"NARE"** (sin sufijo) tiene datos desde 2000 hasta finales de 2023.
- **"NARE CP"** aparece recién a partir de comienzos de 2024.
- No hay traslape de fechas entre ambos nombres — es un renombre de la misma entidad, no dos ríos distintos ni un error de digitación.

No se encontró un glosario oficial de XM que documente este cambio de nombre; se infirió exclusivamente por disponibilidad de datos. El script `descargar_xm_aportes.py` se corrigió para consultar ambos alias y consolidarlos bajo el nombre canónico `NARE`, dejando registrado el nombre original de XM en cada fila (columna `nombre_xm_original`) para trazabilidad.

## 4. Datos confirmados — descarga completa (2000-01-01 a 2026-09-12)

| Río | Registros | Cobertura | Mínimo | Máximo | Media |
|---|---|---|---|---|---|
| GUATAPE | 9.745 | 99,9% | 0,37 m³/s | 243,79 m³/s | 36,14 m³/s |
| NARE (consolidado NARE + NARE CP) | 9.745 | 99,9% | 5,65 m³/s | 309,67 m³/s | 45,70 m³/s |

Prácticamente sin huecos en 26 años — la mejor cobertura de todas las fuentes de caudal usadas en este proyecto hasta ahora (comparar con `docs/datos-ideam-caudal.md`, donde la mejor estación IDEAM tiene 99,2% pero en una ventana mucho más corta, y ninguna llega al 100% de aprobación).

Ejecutada con [`scripts/descargar_xm_aportes.py`](../scripts/descargar_xm_aportes.py). Resumen completo en [`data/processed/xm/resumen_aportes_guatape_nare.csv`](../data/processed/xm/resumen_aportes_guatape_nare.csv).

## 5. Cómo se compara con las series de estaciones IDEAM

Este dato de XM y las 4 series de estaciones IDEAM (`docs/datos-ideam-caudal.md`) miden cosas relacionadas pero no idénticas:

- **XM (GUATAPE, NARE):** aporte operativo consolidado atribuido al embalse — la variable objetivo natural para el modelo de despacho.
- **IDEAM (Puente Real, Puente La Feria, Riotex, etc.):** caudal de tributarios específicos aguas arriba — útiles como variables predictoras/explicativas del aporte total, no como sustituto de él.

**Implicación para el diseño del modelo:** la serie de XM debería ser la variable objetivo (lo que el modelo predice), y las series de IDEAM + la precipitación satelital (CHIRPS) deberían ser las variables predictoras (lo que el modelo usa para predecir). Esto es más coherente que usar cualquiera de las estaciones de tributario como objetivo aislado.

## 6. Pendiente

- [ ] Confirmar con una fuente oficial de XM (glosario SiMEM o UPME) por qué renombraron "NARE" a "NARE CP" en 2024, y si existen otros ríos del catálogo con el mismo tipo de renombre no detectado aún.
- [ ] Revisar si existen aportes por río para otros embalses del complejo (Playas, Punchina) que permitan modelar el sistema completo, no solo Peñol-Guatapé de forma aislada.
- [ ] Cruzar temporalmente esta serie con las de IDEAM y CHIRPS para construir el dataset consolidado de entrenamiento (Fase 2).
