# ¿Se necesita una presa nueva, o se puede replicar en una existente? Análisis de otros embalses colombianos

## 1. Respuesta directa

**No se necesita construir una presa nueva.** Ninguno de los precedentes reales de coordinación hídrico-solar investigados en este proyecto — ni a nivel mundial (China, Vietnam, Tailandia, India, Portugal) ni en Colombia (Aquasol en Urrá) — construyó una presa nueva para esto. Todos son parques solares flotantes instalados sobre embalses hidroeléctricos **ya existentes**. Colombia ya tiene ~30 embalses hidroeléctricos operativos (catálogo oficial de XM, verificado en esta investigación) — la vía de menor costo, menor riesgo ambiental/social y mayor velocidad de implementación es adaptar uno de esos embalses, no construir uno nuevo.

Además, construir una presa nueva en Colombia tiene un costo político y social real y documentado: Hidroituango (2018) e El Quimbo tuvieron ambos conflictos ambientales y sociales significativos durante su construcción. Añadir ese costo para una tecnología (solar flotante) que ni siquiera requiere una presa nueva —solo un espejo de agua ya existente— no tendría justificación técnica.

## 2. Inventario real de embalses hidroeléctricos colombianos (verificado vía API de XM)

Confirmado directamente contra el catálogo oficial de XM (`ListadoEmbalses`, `ListadoRecursos` — el mismo mecanismo usado para los datos de Peñol-Guatapé en este proyecto), Colombia tiene 29 embalses activos registrados. Los de mayor relevancia para replicar este framework, con datos verificados de capacidad y superficie:

| Embalse / Central | Río(s) | Capacidad instalada | Embalse (volumen / superficie) | Operador | ¿Solar flotante hoy? |
|---|---|---|---|---|---|
| **Ituango (Hidroituango)** | Cauca | 2.400 MW diseño (600 MW operativo, 2 de 8 turbinas en 2026) | 2.800 hm³, 78 km de longitud | EPM | No |
| **Guavio** | Guavio/Batatas | 1.260 MW (la mayor central en operación del país) | 950 hm³ (presa de enrocado de 243 m) | Enel-Emgesa | No |
| **Chivor** | Batá + Lengupá | 1.000 MW (8×125 MW) | 758 hm³, 1.252 ha (Embalse Esmeralda) | AES Colombia | No |
| **Sogamoso** | Sogamoso | 820 MW | 4.800 hm³, ~7.000 ha (Embalse Topocoro — el de mayor volumen del país) | ISAGEN | No |
| **Betania** | Magdalena/Yaguará | 540,9 MW (~15% de la generación nacional) | 1.974 hm³, >7.000 ha | Enel-Emgesa | No |
| **Porce III** | Porce | 700 MW | — | EPM | No |
| **Peñol-Guatapé** *(caso de estudio de este proyecto)* | Nare + Guatapé | 560 MW | Volumen útil real 1.322-4.544 GWh (energía), superficie sin confirmar (2.262 ha-74 km² según fuente) | EPM | No |
| **Porce II** | Porce | 405 MW | — | EPM | No |
| **El Quimbo** | Magdalena | 400 MW | 1.824 hm³, 8.250 ha | Enel-Emgesa | No |
| **Urrá I** | Sinú | 340 MW | — | Urrá S.A. | **Sí — Aquasol, 1,5 MW (0,44% de la capacidad hidráulica)** |

Fuente primaria: consultas directas a `POST https://servapibi.xm.com.co/Lists` (`ListadoEmbalses`, `ListadoRecursos`) realizadas en esta sesión, más fuentes públicas citadas en la sección de referencias.

## 3. El candidato más claro para replicar el framework: Urrá I (río Sinú, Córdoba)

**Urrá I ya tiene solar flotante real — Aquasol** (1,5 MW, comisionado en junio de 2023, ~5.000 paneles, 2.400 MWh/año), inaugurado como la instalación solar flotante más grande de Sudamérica sobre un embalse hidroeléctrico en su momento. Esto lo hace, por lejos, el candidato de menor fricción para extender este framework:

- **No hace falta construir ni un solo panel nuevo para el primer piloto de coordinación** — el activo físico ya existe, solo falta la capa de decisión (exactamente el motor de `src/motor_despacho.py`, adaptado a esta cuenca).
- Aquasol representa apenas el **0,44% de los 340 MW de Urrá I** — muy por debajo incluso del precedente más conservador usado en este proyecto (Alqueva, ~2%). Aplicando la misma metodología de anclaje a precedentes reales usada para Guatapé (§4 de `docs/motor-despacho-hidrico-solar.md`), un escenario "intermedio" tipo Da Mi (27,1%) llevaría Urrá a ~92 MWp — 61 veces la capacidad actual de Aquasol.
- El río Sinú tiene una cuenca aportante única y bien documentada (Alto Sinú, Córdoba) — un problema de pronóstico de caudal más simple que el de Guatapé (que requirió consolidar dos ríos, Nare y Guatapé).
- XM publica el embalse Urrá bajo el código `URRA1` en su catálogo — confirmado en esta sesión, el mismo pipeline de descarga (`scripts/descargar_xm_embalse_generacion.py`, `scripts/descargar_xm_aportes_energia.py`) es reutilizable con un cambio de filtro, no un rediseño.

**Recomendación concreta:** Urrá I es el caso natural para una segunda aplicación completa del framework (predicción de caudal + motor de despacho), documentado como próximo paso en el issue correspondiente.

## 4. Otros candidatos, por qué son interesantes y qué los limita

| Embalse | Por qué es un buen candidato | Limitación real |
|---|---|---|
| **Chivor** | Alimentado por dos ríos (Batá + Lengupá) — misma estructura de "dos afluentes" que ya resolvimos en Fase 1 para Guatapé+Nare; capacidad instalada casi 2x la de Guatapé | Sin antecedente de solar flotante — habría que partir de cero en esa capa, no solo extender un piloto existente |
| **Sogamoso (Topocoro)** | El embalse de mayor volumen del país (4.800 hm³) — el mejor candidato para probar si a esa escala el solar sí logra mover el "piso mínimo" (en Guatapé, mucho más pequeño, no lo logró — ver `docs/fase-3-resultados.md` §1) | Un solo embalse pero de una cuenca (Sogamoso) menos estudiada públicamente que Cauca/Magdalena |
| **Guavio** | La central más grande en operación de Colombia (1.260 MW) — mayor demanda a cubrir, mayor margen teórico de sustitución hídrica-solar | Presa de enrocado muy alta (243 m) en zona de páramo — condiciones climáticas (niebla, baja irradiancia relativa) menos favorables para solar que Guatapé o Urrá |
| **Betania / El Quimbo** | Ambos en el río Magdalena, en cascada — permitirían en el futuro un modelo de coordinación multi-embalse (no solo un embalse aislado, como los dos casos ya resueltos) | Mayor complejidad de modelado (interacción entre dos embalses en el mismo río) — no es una extensión trivial del motor actual |
| **Hidroituango** | Cuando esté 100% operativa (2027) será la central más grande de Colombia (2.400 MW); ya tiene monitoreo de presa de vanguardia real (ver §5) | Todavía en puesta en marcha parcial (2 de 8 turbinas) tras la contingencia de 2018 — no es el momento operativo adecuado para superponer un piloto de coordinación energética |

## 5. Lo más avanzado del mundo en ingeniería de presas/FV flotante — hallazgos reales, no genéricos

Investigación verificada contra literatura académica reciente (Ghosh, Goswami, Kumba & Mohammed, *"Unlocking the Potential of Floating Solar Photovoltaics in South America"*, arXiv:2606.12798, 2026 — coautoría Black & Veatch / Vellore Institute of Technology / Federation University) y fuentes primarias de proyectos reales:

- **Coordinación automática real hidro-solar (el estado del arte más cercano a lo que construimos en Fase 3):** la planta de **Sirindhorn (Tailandia)**, 45 MWp sobre el embalse de la represa Sirindhorn, tiene un **sistema de control híbrido que cambia automáticamente entre solar e hidráulica según la demanda de red y el clima**, con batería 3 MW/3 MWh integrada — el precedente real más parecido al motor de despacho de este proyecto, más avanzado que Longyangxia (que solo acopla físicamente, sin lógica de decisión automática).
- **Almacenamiento para resolver el curtailment** (el problema real que este proyecto encontró en Fase 3 — hasta 10-19% de la generación solar simulada se pierde sin batería): Tengeh (Singapur, 1,5 MW/3 MWh) y Sirindhorn (3 MW/3 MWh) confirman que esta es una solución ya probada, no especulativa.
- **Paneles bifaciales** (aprovechan la reflexión del agua para mayor rendimiento): usados en Dezhou Dingzhuang (China, 320 MW) y en el propio proyecto colombiano YurbaQua (Turbaco, Bolívar, 2,8 MWp, inaugurado octubre 2025) — tecnología ya disponible y usada en Colombia, aunque todavía no en un embalse hidroeléctrico.
- **Anclaje/mooring para niveles de agua variables:** el rediseño de Cirata (Indonesia) tras daño por tormenta —pasó a 12 puntos de anclaje por bloque— es una lección real y documentada de por qué el diseño de anclaje debe sobredimensionarse para embalses con variación estacional de nivel significativa, como son la mayoría de los embalses colombianos de regulación multianual.
- **Diseño sismo-resistente:** la planta de Yamakura (Japón) es la primera instalación FV flotante certificada para sismo del país, diseñada para vientos de hasta 180 km/h — referencia directa aplicable a Colombia, país con amenaza sísmica significativa en buena parte de su territorio andino.
- **Arquitectura eléctrica de referencia:** subestación colectora a 138/34,5 kV, transformadores secos (no de aceite, por seguridad ambiental cerca del embalse) de 3-4 MVA, cable submarino según la guía IEEE 1120-2004, cumplimiento de armónicos IEEE 519/2800 — el mismo estándar aplicable a cualquier expansión real en Colombia.
- **Compartir infraestructura de transmisión con la central hidráulica existente** (Da Mi comparte la línea de 220 kV con la hidroeléctrica) es, según la literatura revisada, la ventaja económica más consistente de los sistemas híbridos — reduce significativamente el costo de conexión a red frente a un parque solar aislado.

**Dato de contexto que refuerza por qué Colombia es un buen lugar para esto:** la misma investigación (arXiv:2606.12798, Tabla 2) encuentra que Suramérica tiene el **mayor potencial normalizado de generación FV flotante del mundo** — 38,26 TWh por millón de acres de espejo de agua disponible, más del doble que Asia (18,15) y más del triple que África (11,59) — pese a tener el desarrollo comercial más bajo de las tres regiones. Es una oportunidad real, no solo retórica.

## 6. Ingeniería de presa propiamente dicha: lo más avanzado que ya existe en Colombia

Vale la pena señalar que Colombia **ya tiene** un ejemplo real de instrumentación de presa de vanguardia — no relacionado con solar, pero relevante para cualquier extensión futura de "presa inteligente": Hidroituango, tras la contingencia de 2018, opera con un Centro de Monitoreo que reporta en tiempo real a un Puesto de Mando Unificado, con GPS y acelerómetros del Servicio Geológico Colombiano, automatización de instrumentación geotécnica, piezómetros y un radar tipo LiDAR en el túnel vial. Es, en la práctica, el precedente colombiano más cercano a los sistemas de monitoreo distribuido por fibra óptica que la literatura internacional describe como frontera tecnológica para detección de fugas en presas de materiales sueltos — aunque no se confirmó que Hidroituango use específicamente fibra óptica distribuida todavía.

## 7. Conclusión

1. **No se necesita una presa nueva.** Colombia tiene embalses hidroeléctricos de sobra, varios de ellos multianuales y de gran escala, sin ningún proyecto de coordinación hídrico-solar en tiempo real.
2. **Urrá I es el candidato de menor fricción** para una segunda implementación completa del framework — ya tiene el activo solar (Aquasol), solo le falta la capa de decisión.
3. **Chivor y Sogamoso son los candidatos más interesantes para preguntas de investigación distintas**: Chivor por su estructura de dos ríos (ya resuelta en este proyecto), Sogamoso por ser el embalse de mayor volumen del país (para probar si a esa escala el hallazgo de Fase 3 —que el solar no mueve el piso mínimo del embalse— se sostiene o cambia).
4. **El estado del arte mundial ya resuelve el problema de curtailment que encontramos en Fase 3** (batería 3 MW/3 MWh en Sirindhorn y Tengeh) — es la mejora más concreta y ya probada que se podría incorporar al motor de despacho en una siguiente iteración.
