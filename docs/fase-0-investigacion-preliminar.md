# Fase 0 — Investigación preliminar y selección de alcance

## 1. Motivación

Colombia depende en gran medida del recurso hídrico para su generación eléctrica, lo que expone al sistema a riesgos operativos durante fenómenos de sequía prolongada (El Niño). Al mismo tiempo, el país ya cuenta con infraestructura de generación solar fotovoltaica flotante instalada sobre embalses hidroeléctricos existentes, pero esta opera de forma independiente a la gestión hídrica del embalse.

Este documento resume la investigación preliminar realizada para decidir el alcance de un sistema de inteligencia orientado a resolver ese vacío de coordinación.

## 2. Líneas evaluadas

Se evaluaron cinco líneas de investigación relacionadas con el aprovechamiento energético de Colombia mediante IA:

1. Predicción de caudal basada en microclimas andinos.
2. Coordinación de despacho hídrico-solar en embalses con solar flotante.
3. Inspección automatizada de líneas de transmisión en relieve montañoso.
4. Modelado de pérdidas técnicas y no técnicas en redes de distribución rural.
5. Aprovechamiento de biomasa agrícola y energía geotérmica de origen volcánico.

## 3. Hallazgos por línea

### 3.1 Predicción de caudal (microclimas andinos)
IDEAM realiza modelación hidrológica a escala de cuenca para las principales vertientes del país (Magdalena, Cauca, Amazonas, Atrato, Meta, Arauca, Catatumbo, Patía). Existen antecedentes académicos puntuales de aprendizaje por refuerzo aplicado a predicción de precipitación mensual (caso Boyacá) y de redes neuronales artificiales para completar series de lluvia faltantes en el suroccidente del país. No se encontró evidencia pública de un sistema que traduzca esas predicciones en decisiones de despacho operativo de una central específica.

### 3.2 Coordinación hídrico-solar en embalses
Existen dos pilotos reales en operación:
- **EPM — El Peñol-Guatapé (Antioquia)**: primer piloto de solar flotante en Hispanoamérica, 1.430 m², con meta de escalar hasta el 10% del área del embalse (≈800-1.000 MW).
- **Aquasol — Urrá (Córdoba)**: la planta fotovoltaica flotante más grande de la región, 1,5 MWp, inaugurada en 2023.

Ambos casos son generación **estática**: no existe públicamente un motor de optimización que coordine en tiempo real el despacho hídrico y solar sobre el mismo embalse. Este es el vacío más claro y demostrable de las cinco líneas evaluadas.

### 3.3 Inspección automatizada de líneas de transmisión
ISA ya aplica IA y drones para gestión de riesgo en líneas de alta tensión, con resultados medibles documentados (cero fallas operativas, USD 32 millones de riesgo gestionado), pero el caso reportado corresponde a **ISA Energía Chile**, en alianza con Ecodrones. En Colombia, ISA opera el ecosistema "Gacela" para planeación de infraestructura de transmisión, con ahorros reportados cercanos a USD 150.000 en 2025, pero orientado a planeación y no a inspección física del relieve montañoso. Adaptar el modelo probado en Chile al contexto andino colombiano es un vacío real, con precedente interno de la misma empresa.

### 3.4 Pérdidas en redes de distribución rural
Es la línea con mayor desarrollo académico ya existente en Colombia. Se identificaron trabajos con CatBoost, LightGBM y XGBoost, y un modelo híbrido CNN-LSTM-DNN validado con datos reales de 44.231 usuarios en Aguachica (Cesar), con 74,47% de precisión en la detección de pérdidas no técnicas. Los índices de pérdida reportados en el Caribe colombiano son altos: Aire (32%) y Afinia (28,29%) en zonas de Bolívar, Cesar, Córdoba, Sucre, Magdalena y Atlántico. El riesgo de esta línea es duplicar trabajo académico ya validado; la oportunidad real estaría en extender esos modelos a ramificaciones específicas de red, no en repetir el enfoque general.

### 3.5 Biomasa agrícola y geotermia volcánica
UPME ya cuenta con el "Atlas del potencial energético de la biomasa residual en Colombia", con un potencial técnico estimado de 204,8 a 235,3 PJ mediante gasificación. En geotermia, Ecopetrol lidera junto con CHEC y Baker Hughes un proyecto exploratorio activo en el Nevado del Ruiz, con el objetivo de abastecer más de 250.000 familias; existen antecedentes previos de ISAGEN (feasibility study de una central de 50 MW) que no se concretaron. El diagnóstico de recurso en ambas fuentes ya fue realizado por instituciones de gran escala (UPME, Ecopetrol), lo que reduce el margen de una iniciativa independiente para aportar algo no cubierto a corto plazo.

## 4. Priorización

| Prioridad | Línea | Justificación |
|---|---|---|
| 1 | Coordinación de despacho hídrico-solar | Vacío más claro, datos públicos disponibles (IDEAM, XM), infraestructura física ya existente (Guatapé, Urrá) sobre la cual demostrar valor |
| 2 | Inspección de transmisión con visión artificial | Vacío real, con precedente probado dentro de la misma empresa (ISA Chile → Colombia) |
| 3 | Pérdidas en distribución rural | Complementaria; alto riesgo de duplicar trabajo académico si se aborda como línea independiente |
| Observación | Biomasa y geotermia | Diagnóstico de recurso ya cubierto a escala nacional por UPME y Ecopetrol; monitorear, no duplicar |

## 5. Alcance definido para este repositorio

Este repositorio desarrolla exclusivamente la **prioridad 1**: un sistema de investigación que (a) prediga caudal afluente a partir de variables de microclima andino, y (b) optimice el despacho conjunto hídrico-solar sobre un embalse con generación flotante existente, incluyendo el efecto de reducción de evaporación por cobertura fotovoltaica.

Las líneas 2, 3 y 4 quedan documentadas como investigación de respaldo y posibles extensiones futuras, no como alcance actual.

## 6. Profesión de referencia del proyecto

El eje profesional de esta investigación es la **Ingeniería Eléctrica con especialización en Sistemas de Potencia y Energías Renovables**, por ser la disciplina que integra generación, coordinación de recursos y despacho — el machine learning y la hidrología aplicada se emplean como herramientas dentro de ese marco, no como ejes independientes.

## 7. Fuentes consultadas

- IDEAM — Modelación hidrológica: http://pronosticos.ideam.gov.co/web/agua/modelacion-hidrologica
- EPM — Piloto solar flotante El Peñol-Guatapé: https://www.larepublica.co/especiales/colombia-potencia-energetica/epm-desarrolla-en-el-penol-antioquia-el-primer-piloto-de-parque-solar-flotante-en-hispanoamerica-2966396
- Aquasol — Urrá, Córdoba: https://www.smartgridsinfo.es/2018/04/24/instalan-parque-solar-flotante-colombia-esperan-obtener-hasta-15-por-ciento-mas-energia-tierra
- ISA — IA y drones en transición energética: https://lagrannoticia.com/isa-logra-eficiencias-aplicando-ia-y-drones-en-la-transicion-energetica/
- Modelo híbrido CNN-LSTM-DNN, caso Aguachica: https://repository.unad.edu.co/bitstream/handle/10596/79590/alopezchave.pdf
- UPME — Atlas del potencial energético de la biomasa residual: https://www1.upme.gov.co/siame/Documents/Atlas-Biomasa/1_Indice_Generalidades.pdf
- Ecopetrol — Proyecto exploratorio de geotermia, Nevado del Ruiz: https://www.elcolombiano.com/negocios/ecopetrol-proyecto-energia-geotermica-colombia-que-es-y-cuales-son-las-zonas-CM28244251
