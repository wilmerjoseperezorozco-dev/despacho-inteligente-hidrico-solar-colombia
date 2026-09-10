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

## 6. Pendiente

- [ ] Coordenada exacta del muro de presa (Google Earth) para re-ejecutar con mayor confianza.
- [ ] Validar el área resultante contra fuente oficial (IDEAM, CORNARE, o ficha técnica de EPM).
- [ ] Simplificar el polígono vectorizado (actualmente tiene el "efecto escalera" propio de vectorizar un ráster de 30 m sin suavizar) antes de usarlo en análisis geoespaciales posteriores.
