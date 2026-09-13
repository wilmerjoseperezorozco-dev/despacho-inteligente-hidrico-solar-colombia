# Series históricas de caudal (IDEAM) — descubrimiento, selección y calidad real

## 1. Cómo se encontró el acceso público

`datos.gov.co` publica los datasets de IDEAM, pero varios de ellos (como "Caudales Medios Diarios de los Ríos de Colombia", `jxnq-r3i9`) están marcados como **no tabulares** — no se pueden consultar con SQL vía la API estándar. Al inspeccionar sus metadatos se encontró un `additionalAccessPoints` apuntando a un bucket S3 público del propio IDEAM (`datos.ideam.gov.co`), confirmado por sus cabeceras HTTP (`Server: Nutanix Objects`) como un almacenamiento de objetos compatible con S3, **sin autenticación**.

Dentro de ese bucket existe una guía oficial en Jupyter Notebook (`guia/Notebook - Guia de Descarga Datos Parquet.ipynb`) que documenta las rutas oficiales:

- Catálogo de estaciones: `s3://s3-estacionesideam/catalogo/estaciones/csv/catalogo.csv`
- Catálogo de variables: `s3://s3-estacionesideam/catalogo/variables/csv/variables.csv`
- Series históricas: `s3://s3-estacionesideam/observaciones/historicos/csv/{ETIQUETA}/{CODIGO}-{ETIQUETA}.csv`

Verificado con descarga real: `Q_MEDIA_D` (caudal medio diario) para 4 estaciones, ver sección 3.

## 2. Hallazgo importante: la precipitación diaria NO tiene el mismo nivel de curación que el caudal

El catálogo oficial de variables (`catalogo/variables/csv/variables.csv`, descargado y verificado) muestra que para **Caudal** existen productos curados en las tres periodicidades: `Q_MEDIA_D` / `Q_MEDIA_M` / `Q_MEDIA_A` (además de máximos y mínimos). Para **Precipitación**, en cambio, el único producto disponible en este bucket es `0240` — *"Precipitación acumulada 10 minutos"* — un dato crudo de alta frecuencia de estaciones automáticas, **sin ningún agregado diario, mensual o anual publicado**.

**Consecuencia práctica:** no se puede sustituir la ruta satelital (CHIRPS/IMERG, ver `docs/datos-satelitales-precipitacion.md`) por series de estación IDEAM para precipitación diaria de largo plazo — no existe ese producto curado en este acceso público. La combinación planeada (satélite + estación como corrección de sesgo puntual) sigue siendo necesaria, no redundante.

## 3. Estaciones seleccionadas — cuenca aportante al embalse Peñol-Guatapé

Se filtró el Catálogo Nacional de Estaciones del IDEAM (`hp9r-jxuu` en datos.gov.co) por el bbox de la cuenca ya delineada (ver `docs/delineacion-cuenca.md`) y se cruzó contra los archivos realmente publicados en `Q_MEDIA_D`. De las estaciones limnimétricas/limnigráficas activas en la zona, se identificaron dos grupos:

- **Aguas arriba de la Presa Santa Rita (dentro de la cuenca aportante)**: estaciones en la meseta del oriente antioqueño (Río Negro, Marinilla y quebradas asociadas), que drenan hacia el embalse desde el suroeste.
- **Aguas abajo de la presa** (excluidas de "cuenca aportante"): estaciones sobre el río Guatapé y San Carlos (ej. código `0023087640`, `0023087650`), que miden el agua ya turbinada/derivada hacia el complejo San Carlos, no el afluente al embalse.

Las estaciones **Santa Rita (`23087420`)** y **Vertedero Santa Rita (`23087590`)** — literalmente en el muro de la presa — existen en el catálogo pero **no tienen archivo `Q_MEDIA_D` publicado** en este bucket (probablemente reportan solo nivel, no caudal calculado). Se documenta esta ausencia explícitamente para no dar la impresión de que se usó la estación "ideal" cuando en realidad se usaron las mejores disponibles.

### Estaciones descargadas y verificadas (2026-09-13)

| Código | Nombre | Corriente | Rango real | Registros | Cobertura | Estado de aprobación |
|---|---|---|---|---|---|---|
| 0023087150 | Puente Real | Río Negro | 1974-01-01 a 2026-09-11 | 17.546 | 91,2% | 100% Preliminar |
| 0023087660 | Puente La Feria | Marinilla | 1994-01-01 a 2026-07-31 | 8.024 | 67,4% | 100% Preliminar |
| 0023087670 | Riotex | Quebrada La Mosca | 1994-01-01 a 2026-08-31 | 11.841 | 99,2% | 100% Preliminar |
| 0023087690 | Bodegas | Quebrada Leonera | 1994-01-01 a 1998-08-31 | 1.662 | 97,5% | 100% Preliminar |

Resumen completo en [`data/processed/ideam/resumen_calidad_caudal_guatape.csv`](../data/processed/ideam/resumen_calidad_caudal_guatape.csv) (generado por `scripts/descargar_ideam_caudal.py`, reproducible).

## 4. Advertencia de calidad — leer antes de usar estos datos en el modelo

**El 100% de los registros descargados están marcados como `"Preliminar"`, ninguno como `"Aprobado"`.** Esto significa que son datos operativos que IDEAM aún no ha sometido a su control de calidad final (proceso que institucionalmente toma tiempo). No es un error de la descarga — es el estado real de publicación de estos datos. Cualquier resultado del modelo debe declarar esta limitación, y cuando IDEAM publique versiones "Aprobado" de estos mismos periodos, deben preferirse sobre las preliminares.

**Estación Bodegas (Q. Leonera)** dejó de reportar en 1998 — probablemente fue suspendida o reemplazada. No usar su serie más allá de ese corte sin verificar el estado actual de la estación en el catálogo.

**Puente La Feria (Marinilla)** tiene la cobertura más baja (67,4%) de las cuatro — tiene huecos reales que deben tratarse explícitamente en el preprocesamiento (no interpolar silenciosamente sin dejarlo documentado).

## 5. Script asociado

[`scripts/descargar_ideam_caudal.py`](../scripts/descargar_ideam_caudal.py) — probado end-to-end el 2026-09-13, sin autenticación requerida, reusable para cualquier otra estación del catálogo IDEAM (pasar el código de 10 dígitos con ceros a la izquierda).

## 6. Pendiente

- [ ] Confirmar por qué Santa Rita y Vertedero Santa Rita no tienen `Q_MEDIA_D` publicado (¿solo reportan nivel? ¿existe una tabla de calibración nivel-caudal aplicable?).
- [ ] Evaluar si XM/SIMEM tiene un dato equivalente de "aportes hídricos" directamente para el embalse Peñol-Guatapé que sirva como serie objetivo del modelo (más relevante operativamente que un afluente aislado).
- [ ] Investigar por qué Puente La Feria y Bodegas tienen huecos/cortes — ¿mantenimiento, cambio de instrumentación, o algo que documentar antes de usar la serie?
- [ ] Cuando se tenga el modelo de predicción, usar estas 4 series como variables predictoras del caudal afluente total al embalse, no como proxy único — ninguna está literalmente en la presa.
