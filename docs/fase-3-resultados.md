# Resultados del motor de despacho hídrico-solar (Fase 3)

Ver `docs/motor-despacho-hidrico-solar.md` para la metodología completa, los supuestos y sus limitaciones — este documento solo reporta los números.

Backtest de información perfecta (oracle, ver limitación §5.1 del documento de metodología), período 2021-2026 (2.069 días, mismo período de prueba de Fase 2), tres escenarios de capacidad solar anclados a precedentes reales.

## 1. Resultado principal: el piso mínimo del embalse casi no se mueve

| Escenario | Capacidad | z — piso mínimo del embalse | Mejora vs. sin solar |
|---|---|---|---|
| Sin solar (línea base) | — | 3.796,8 GWh | — |
| Piloto | 5 MWp | 3.796,8 GWh | +0,0 GWh |
| Intermedio | 152 MWp | 3.797,4 GWh | +0,6 GWh |
| Agresivo | 372 MWp | 3.798,2 GWh | +1,4 GWh |

**Hallazgo honesto:** ninguno de los tres escenarios — ni siquiera el más agresivo, con una capacidad solar superior a la mitad de la Central Guatapé — mueve de forma perceptible el nivel más bajo que toca el embalse en 5,7 años. La razón física: el peor momento del período (el que determina z) lo marca un tramo de aportes muy bajos que dura semanas, y ni 372 MWp de solar generan suficiente energía diaria para compensar un déficit de esa escala frente a un embalse de ~4.500 GWh de capacidad total. **La coordinación hídrico-solar, al menos con capacidades del orden de las ya construidas en el mundo, no es un seguro contra sequías multianuales para un embalse de este tamaño.**

## 2. Donde sí hay un efecto real y medible: el turbinado día a día

Comparando el turbinado total necesario para igualar la generación hidráulica real histórica (demanda más representativa que la sola Obligación de Energía Firme — ver §5.3 más abajo):

| Escenario | Turbinado total sin solar | Turbinado total con solar | Agua turbinada evitada | Reducción |
|---|---|---|---|---|
| Piloto (5 MWp) | 17.931,1 GWh | 17.892,1 GWh | 39,0 GWh | 0,2% |
| Intermedio (152 MWp) | 17.931,1 GWh | 16.817,8 GWh | 1.113,3 GWh | 6,2% |
| Agresivo (372 MWp) | 17.931,1 GWh | 15.289,6 GWh | 2.641,5 GWh | 14,7% |

Con el escenario agresivo, el 14,7% de la energía que hoy turbina la Central Guatapé en 5,7 años podría, en teoría, sustituirse por solar flotante sin dejar de servir la misma demanda — esto sí es un efecto de conservación de recurso hídrico con orden de magnitud relevante, aunque no evite el peor escenario de sequía.

## 3. Aprovechamiento del solar (cuánto de lo generado realmente se usa)

| Escenario | Solar potencial generado | Solar efectivamente usado (= agua evitada) | Aprovechamiento |
|---|---|---|---|
| Piloto | 39,3 GWh | 39,0 GWh | 99,2% |
| Intermedio | 1.194,9 GWh | 1.113,3 GWh | 93,2% |
| Agresivo | 2.923,5 GWh | 2.641,5 GWh | 90,4% |

El escenario agresivo desperdicia (curtailment) cerca del 10% de su generación potencial — ocurre en días de alta irradiancia donde la demanda a cubrir ya es menor que lo que el parque solar podría entregar, y no existe una batería ni una obligación de compra que absorba el excedente en este modelo. Esto es consistente con por qué Portugal (Alqueva) sí incluyó una batería de gestión activa en su proyecto real — el desperdicio por curtailment es un problema conocido en la literatura, no un artefacto de este modelo.

## 4. Sensibilidad a la definición de "demanda a cubrir"

Se probaron dos definiciones (ver `src/motor_despacho.py`, flag `--demanda`):

- **`obligacion`** (Obligación de Energía Firme real de XM, media 4,4 GWh/día): resultó ser una restricción casi nunca activa — los aportes naturales (media 19 GWh/día) casi siempre la superan ampliamente, así que el modelo de "solo cumplir la obligación" no representa el despacho real y subestima drásticamente cuánta hidráulica se turbina en la práctica.
- **`generacion_real`** (igualar la generación hidráulica real histórica, media 9,2 GWh/día): más representativa del despacho efectivo, es la que se reporta como resultado principal arriba.

Curiosamente, el piso mínimo del embalse (z) es prácticamente idéntico bajo ambas definiciones (diferencia menor a 10 GWh) — confirma que el hallazgo de la sección 1 no es sensible a esta elección de modelado, mientras que el ahorro de turbinado (sección 2) sí lo es, y por mucho (14,7% vs. una reducción porcentual mucho mayor si se mide contra la obligación, que es una base mucho más pequeña — ver `data/processed/despacho_resultados_obligacion_resumen.csv` para esos números, no reportados como principales por ser una base de comparación poco realista).

## 5. Un bug real de dos etapas en el propio motor de optimización — vale la pena documentarlo

La primera versión del motor solo maximizaba `z` en una sola etapa. Eso dejó el turbinado total del resto de los días **indeterminado** — CBC devolvía soluciones matemáticamente óptimas en `z` que casi no usaban el solar disponible (ej. escenario agresivo: 2.923 GWh de solar generados, pero apenas ~88 GWh menos de hidráulica turbinada en la primera versión, un desajuste sin sentido físico). Se corrigió con una segunda etapa: fijar `z` en su óptimo y, entre todas las soluciones que lo logran, minimizar el turbinado total — ver el docstring de `resolver_lp()` en `src/motor_despacho.py` para el detalle completo, incluyendo un segundo bug de tolerancia numérica (un margen de 1 kWh es insuficiente para variables del orden de miles de millones de kWh) que apareció al implementar la primera corrección.

## 6. Conclusión de Fase 3 (primera entrega)

El motor de optimización funciona, está calibrado contra datos reales, y da una respuesta honesta y con matices — no la respuesta "el solar lo resuelve todo" que un análisis menos cuidadoso podría haber reportado. La coordinación hídrico-solar en Guatapé, con capacidades del orden de los proyectos reales ya construidos en el mundo, **no protege contra el peor escenario de sequía multianual, pero sí reduce de forma medible el uso cotidiano de agua turbinada** (hasta 14,7% en el escenario más ambicioso), con una pérdida por curtailment de ~10% que ya se sabe, por la literatura y por el caso de Alqueva, que una batería de gestión podría reducir.

Esto dado con información perfecta (oracle) — convertirlo en una política operativa real con pronóstico (no información perfecta) queda para trabajo futuro, como se explica en la metodología.
