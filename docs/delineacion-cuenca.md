# Delineación de la cuenca aportante — metodología, prueba real y hallazgo

## 1. Por qué no se usó un polígono dibujado a mano en Google Earth

Google Earth permite ver el terreno y el embalse con mucho detalle, pero trazar a mano el límite real de una cuenca hidrográfica requiere seguir divisorias de aguas (líneas de cresta) que no siempre son visibles a simple vista en una imagen satelital — es un ejercicio propenso a error incluso para alguien con experiencia en SIG. En cambio, Google Earth **sí es la herramienta correcta para una cosa muy concreta**: identificar con precisión un punto (por ejemplo, el muro de la presa), usando clic derecho sobre la imagen para obtener sus coordenadas exactas.

Por eso el enfoque adoptado aquí es **delineación automática por computador**: a partir de un único punto de desfogue (coordenada del embalse/presa) y un modelo digital de elevación (DEM), un algoritmo hidrológico calcula la cuenca real siguiendo la topografía — sin depender de que alguien trace límites a mano.

## 2. Metodología

1. Descargar el DEM SRTM de 30 m (dominio público, sin autenticación) alrededor del punto de interés — fuente: AWS Terrain Tiles / Mapzen.
2. Rellenar depresiones y resolver zonas planas del DEM (paso estándar de preprocesamiento hidrológico).
3. Calcular dirección de flujo (algoritmo D8) y acumulación de flujo por celda.
4. Ajustar el punto de desfogue a la celda de mayor acumulación de flujo dentro de un radio de búsqueda (esto corrige imprecisiones del punto de entrada — ver hallazgo abajo).
5. Delinear la cuenca (`catchment`) a partir de ese punto ajustado.
6. Vectorizar la máscara resultante a un polígono GeoJSON.

Implementado en [`scripts/delinear_cuenca.py`](../scripts/delinear_cuenca.py).

## 3. Prueba real y hallazgo (2026-09-10) — se documenta el error, no solo el resultado final

**Primer intento:** se usó como punto de desfogue la coordenada de "Embalse El Peñol" obtenida de OpenStreetMap (-75.1799709, 6.2855878) sin ajuste de búsqueda.
**Resultado:** área de cuenca de **2,0 km²** — un valor absurdamente pequeño para la cuenca aportante de un embalse hidroeléctrico grande.
**Diagnóstico:** el punto de OpenStreetMap es una etiqueta de localidad, no el cauce principal del río Nare ni el muro de la presa; el algoritmo de ajuste (`snap_to_mask`) lo desplazó a un tributario menor cercano en vez de al cauce principal.

**Corrección aplicada:** en lugar de ajustar al punto más cercano que supere un umbral de acumulación, se buscó la celda de **mayor acumulación de flujo dentro de un radio de ~2 km** alrededor del punto original — esto encuentra el cauce principal aunque el punto de entrada esté impreciso.
**Resultado corregido:** área de cuenca de **~1.048-1.210 km²** (dos corridas con ventanas de DEM ligeramente distintas), un orden de magnitud físicamente plausible para el sistema Peñol-Guatapé.

**Conclusión honesta:** el método funciona, pero el resultado sigue siendo **preliminar** — no se validó contra un área de cuenca oficial (IDEAM, CORNARE o EPM) porque no se encontró ese dato publicado en esta sesión. No se debe usar este polígono como definitivo sin esa validación.

## 4. Qué se necesita de Google Earth (lo único que realmente hace falta)

No se necesita un polígono dibujado a mano. Se necesita **un solo punto preciso**:

1. Abrir Google Earth y ubicar el muro de la presa de Guatapé o El Peñol (la estructura física, no el centro del lago).
2. Clic derecho sobre ese punto exacto → copiar las coordenadas (latitud, longitud).
3. Enviar esa coordenada para volver a correr `delinear_cuenca.py` con un punto de desfogue confiable, en vez del punto aproximado de OpenStreetMap usado en esta prueba.

Alternativa si no se encuentra el muro exacto: la coordenada del vertedero (spillway) o de la casa de máquinas también sirve como punto de referencia cercano.

## 5. Archivo generado

[`data/processed/cuencas/cuenca_preliminar_guatape-el_penol.geojson`](../data/processed/cuencas/cuenca_preliminar_guatape-el_penol.geojson) — polígono preliminar, marcado explícitamente como `"estado": "PRELIMINAR"` en sus propiedades. No usar como definitivo.

## 6. Actualización — coordenada real del muro de presa (2026-09-10)

El usuario aportó la coordenada exacta de la **Presa Santa Rita** (6°15'40"N 75°11'24"O = 6.2611, -75.1900) — la estructura física real que embalsa el río Nare para formar el sistema Peñol-Guatapé. Se verificó de forma independiente que esta coordenada **coincide exactamente con la que usa el infobox de Wikipedia para "Embalse Peñol-Guatapé"**, lo que confirma que es el punto de referencia correcto y no una aproximación.

**Re-ejecución con este punto:** área resultante de **1.071,7 km²**.

**Validación cruzada (tres corridas independientes, mismo orden de magnitud):**

| Corrida | Punto de entrada | Área resultante |
|---|---|---|
| 1 | Etiqueta OSM "Embalse El Peñol", ventana de búsqueda estrecha | 1.047,6 km² |
| 2 | Misma etiqueta OSM, script consolidado (ventana DEM más amplia) | 1.209,9 km² |
| 3 | **Presa Santa Rita (coordenada real, verificada)** | **1.071,7 km²** |

**Cifra externa encontrada (no confirmada en documento primario):** una búsqueda indicó que el "área tributaria del embalse Peñol-Guatapé" reportada por CORNARE es de **1.210 km²** — casi idéntica a la corrida 2. Se intentó verificar esto directamente en dos documentos primarios de CORNARE (Plan de Manejo DRMI Embalse Peñol-Guatapé y Descripción General de la Cuenca del Río Nare), pero **ambos PDF están detrás de una verificación anti-bot que impidió leer el contenido real** — no se pudo confirmar la cita textual. Se reporta esta cifra como *coincidencia con fuente secundaria*, no como validación oficial cerrada.

**Nota adicional sin resolver:** la capacidad total del embalse aparece con dos valores distintos según la fuente — 1.070.021.000 m³ (Wikipedia) vs. 1.240 hm³ tras la segunda etapa de elevación de Santa Rita en 1979-1980 (tesis UNAL). No se concilió esta diferencia; puede deberse a distintas fechas de medición o a si se incluye o no el embalse Playas del mismo complejo.

**Conclusión:** el rango 1.050-1.210 km² tiene ahora tres soportes independientes (tres corridas + una cifra secundaria de CORNARE) que convergen. Se sube el nivel de confianza de "preliminar sin contraste" a "preliminar con consistencia interna y externa", pero se mantiene la etiqueta `PRELIMINAR` en el GeoJSON hasta poder leer el documento primario de CORNARE directamente (no vía buscador).

## 7. Pendiente

- [x] ~~Coordenada exacta del muro de presa~~ — aportada por el usuario (Presa Santa Rita) y verificada de forma independiente.
- [ ] Leer directamente el PDF de CORNARE (Plan de Manejo DRMI o descripción de cuenca del río Nare) para confirmar la cifra de 1.210 km² sin depender del resumen del buscador — requiere sortear la verificación anti-bot (podría intentarse con otra herramienta o descarga manual).
- [ ] Conciliar la discrepancia de capacidad del embalse (1.070 vs. 1.240 hm³).
- [ ] Simplificar el polígono vectorizado (efecto "escalera" de vectorizar un ráster de 30 m sin suavizar) antes de usarlo en análisis geoespaciales posteriores.
