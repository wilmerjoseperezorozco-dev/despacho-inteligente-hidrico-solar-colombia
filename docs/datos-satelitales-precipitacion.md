# Datos satelitales de precipitación (CHIRPS / GPM-IMERG) para rellenar huecos de IDEAM en páramo

## 1. Por qué se necesitan

Las estaciones terrestres de IDEAM tienen buena cobertura en valles y zonas pobladas, pero son escasas en páramo y alta montaña — justamente donde nace el caudal que alimenta los embalses andinos. Un modelo de predicción de caudal entrenado solo con estaciones terrestres hereda ese sesgo espacial. Los productos satelitales de precipitación no reemplazan a IDEAM, pero rellenan esos vacíos espaciales con una grilla continua.

## 2. Especificaciones confirmadas (fuente primaria, 2026-09-10)

| | **CHIRPS 2.0** | **GPM IMERG** |
|---|---|---|
| Resolución espacial | 0,05° (~5,5 km) | 0,1° (~11 km) |
| Resolución temporal | Diaria y pentadal (5 días) | Media hora, agregable a 3h/diario/7d/mensual |
| Cobertura temporal | 1981 a casi tiempo real | 2000 a tiempo real (misión GPM) |
| Cobertura geográfica | Cuasi-global, 50°S-50°N | Global |
| Latencia (producto research-grade) | — (dataset histórico, no near-real-time) | Final Run: ~2,5-3,5 meses (recomendado para investigación, incluye calibración con estaciones y ERA-5) |
| Latencia (producto operativo) | N/A | Early Run: ~4h / Late Run: ~12-14h (para uso casi en tiempo real, menor calidad) |
| Acceso | Público, dominio público, sin autenticación (`data.chc.ucsb.edu`, Google Earth Engine, ClimateSERV) | Requiere cuenta gratuita NASA Earthdata Login |
| Limitación documentada por el proveedor | "Los datos satelitales sufren sesgos por terreno complejo, que suelen subestimar la intensidad de eventos de precipitación extrema" | "La precipitación es en general menos certera en terreno montañoso"; "no es una buena fuente para estimar manto de nieve" |

**Fuentes primarias verificadas:** [Climate Hazards Center — CHIRPS](https://www.chc.ucsb.edu/data/chirps), [NASA GPM — IMERG](https://gpm.nasa.gov/data/imerg)

**Nota de honestidad:** busqué específicamente un estudio de validación de CHIRPS/IMERG en cuencas andinas colombianas y no encontré uno confirmable con fuente en vivo en esta sesión. No lo doy por existente — queda como tarea de Fase 1 (sección 6).

## 3. Decisión de uso

- **CHIRPS como fuente principal para entrenamiento histórico**: su cobertura desde 1981 coincide con el horizonte de 10-15 años de series IDEAM que se necesita para entrenar el modelo de caudal, es de dominio público (sin fricción de autenticación) y ya se confirmó operativamente (ver sección 4).
- **IMERG Final Run como fuente de contraste/validación**: mejor resolución temporal (media hora vs. diaria), útil para detectar eventos de precipitación intensa de corta duración que CHIRPS diario puede diluir.
- **IMERG Early/Late Run se reserva para una fase operativa futura** (pronóstico casi en tiempo real), no para esta etapa de investigación histórica.

## 4. Prueba de extremo a extremo (ejecutada y verificada, 2026-09-10)

Se descargó y procesó un archivo real de CHIRPS (15 de junio de 2023) para confirmar que el pipeline funciona antes de documentarlo como plan:

```
Fuente:      https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05/2023/chirps-v2.0.2023.06.15.tif.gz
CRS:         EPSG:4326
Resolución:  0.05° x 0.05° (confirmada, coincide con la especificación)
Recorte:     bbox Guatapé/El Peñol-Nare (-75.3, 5.9, -74.9, 6.4) → grilla de 8x10 píxeles
Resultado:   precipitación entre 4.6 y 19.6 mm/día, media 12.2 mm/día — rango físicamente
             plausible para un día de junio en el oriente antioqueño
```

Esto confirma que el acceso, el formato y el recorte geográfico funcionan tal como se documentan aquí — no es una promesa teórica.

## 5. Corrección de sesgo frente a estaciones IDEAM (obligatoria antes de usar en el modelo)

El propio proveedor de CHIRPS advierte que el dato satelital subestima eventos extremos en terreno complejo. Antes de usar la grilla satelital como insumo del modelo de caudal, se debe corregir contra las estaciones IDEAM disponibles en la cuenca:

1. Extraer la serie CHIRPS/IMERG en el píxel más cercano a cada estación IDEAM con registro histórico.
2. Comparar contra el dato terrestre real de esa estación (no asumir que el satélite es correcto).
3. Aplicar corrección de sesgo por cuantiles (*quantile mapping*) mensual o estacional, estación por estación.
4. Interpolar los factores de corrección hacia las zonas sin estación (páramo) usando la altitud como covariable (la precipitación andina depende fuertemente de la elevación).
5. Solo entonces usar la grilla corregida como insumo del modelo — nunca el dato satelital crudo sin pasar por este control de calidad.

## 6. Tareas pendientes para Fase 1

- [ ] Confirmar si existe literatura de validación CHIRPS/IMERG específica para cuencas andinas colombianas (pendiente, no encontrada hoy).
- [ ] Definir la cuenca aportante exacta de Guatapé/El Peñol-Nare (polígono, no solo bbox rectangular) para recortes precisos.
- [ ] El usuario debe crear su propia cuenta gratuita en [NASA Earthdata](https://urs.earthdata.nasa.gov/) para acceder a IMERG (no se puede automatizar la creación de la cuenta).
- [ ] Ejecutar la descarga histórica completa (10-15 años) una vez definida la cuenca exacta — no se ejecutó en esta sesión por ser una operación de larga duración (miles de solicitudes).

## 7. Scripts asociados

- [`scripts/descargar_chirps.py`](../scripts/descargar_chirps.py) — probado end-to-end, sin autenticación requerida.
- [`scripts/descargar_imerg.py`](../scripts/descargar_imerg.py) — escrito contra la API documentada de NASA GES DISC, **no probado** (requiere credenciales personales del usuario); revisar antes de confiar en él en producción.
