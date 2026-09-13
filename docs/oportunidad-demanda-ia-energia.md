# La demanda energética de la IA como ventana de oportunidad para Colombia

## 1. Por qué este documento existe

Este proyecto nació para resolver un problema de coordinación entre generación hídrica y solar flotante en Colombia (ver `README.md` y `docs/fase-0-investigacion-preliminar.md`). Este documento añade una segunda motivación, verificada con fuentes primarias: la demanda eléctrica de la inteligencia artificial está creciendo más rápido que la capacidad de generación firme disponible en el mundo, y Colombia tiene activos reales — hídricos, geográficos y de conectividad — para participar en esa transición sin necesidad de competir donde no tiene escala para hacerlo.

No se trata de una oportunidad especulativa: cada cifra de esta sección viene de una fuente citada y verificada en 2026-09-13.

## 2. El tamaño del problema global

- El consumo eléctrico de centros de datos pasa de **485 TWh (2025) a 950 TWh proyectados (2030)** — cerca del 3% de la demanda eléctrica mundial. El consumo de los centros de datos **enfocados en IA se triplica** en ese periodo, más rápido que el resto del sector. [IEA — Energy demand from AI](https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai)
- El cuello de botella no es solo generación: cadenas de suministro de turbinas de gas y transformadores, y sobre todo **colas de conexión a la red y permisos**, están limitando el despliegue más que la disponibilidad teórica de energía.

## 3. La energía no es el único límite — el otro es el hardware

Es importante no presentar esto como si la energía fuera la única restricción de la IA. En 2026 el cuello de botella de cómputo se movió de la fabricación de GPUs a la memoria de alto ancho de banda (HBM):

- SK Hynix y Micron reportan **toda su producción de HBM de 2026 vendida por adelantado**.
- TSMC reporta su capacidad de empaquetado avanzado (CoWoS) "muy ajustada" hasta bien entrado 2026.
- La demanda de HBM creció **5 veces entre 2023 y 2026**; la escasez podría extenderse hasta 2027-2028.

Fuente: [Bloomberg — AI-driven memory chip shortage](https://www.bloomberg.com/graphics/2026-ai-boom-memory-chip-shortage/)

**Implicación para Colombia:** el país no tiene ni tendrá en el corto plazo influencia sobre la cadena de semiconductores. Sí puede tener influencia real sobre un insumo distinto y propio: energía limpia firme. Esa es la ventana concreta, no la única variable de la ecuación.

## 4. El contexto de ritmo y prudencia — por qué esto no es solo "correr más rápido"

Quienes lideran el desarrollo de frontera de IA están, en 2026, pidiendo explícitamente lo contrario de una carrera desenfrenada:

- **Dario Amodei (CEO de Anthropic)** publicó dos ensayos en 2026: *"The Adolescence of Technology"* (enero), advirtiendo que la civilización enfrenta "riesgos a nivel civilizatorio" por una IA superhumana posiblemente desde 2027; y *"We Must Pace the Frontier"* (septiembre), donde propone explícitamente **desacelerar** el desarrollo mediante evaluadores externos incrustados, coordinación entre laboratorios de frontera en democracias, y acuerdos internacionales — combinado con control de exportación de chips para proteger la ventaja de los países democráticos. [Fortune](https://www.fortune.com/2026/01/27/anthropic-ceo-dario-amodei-essay-warning-ai-adolescence-test-humanity-risks-remedies) / [Kingy AI](https://kingy.ai/blog/dario-amodei-ai-slowdown-open-models/)
- **Bill Gates** publicó en agosto de 2026 un ensayo donde afirma que "con el curso y la velocidad actuales, hay una probabilidad muy alta de un resultado neto negativo", identifica el riesgo de bioterrorismo asistido por IA como 50 veces más preocupante que una pandemia natural, y declara que —por primera vez en su vida— desea que una tecnología avance más despacio. [Axios](https://www.axios.com/2026/08/26/bill-gates-sounds-the-alarm-on-an-ai-transition)

**Nota de contexto (no central a este documento):** la fricción social que genera este ritmo ya es visible incluso en matemáticas puras — el 8 de septiembre de 2026, OpenAI reportó que un modelo interno resolvió un problema de existencia de singularidad para las ecuaciones de Navier-Stokes usando ~10.000 agentes de IA en 88 horas, lo que generó una disputa de crédito con matemáticos (Tristan Buckmaster, NYU, y Levent Alpöge, afiliado a Anthropic) que ya tenían avances privados no publicados sobre el mismo problema. [Axios](https://www.axios.com/2026/09/08/openai-math-solution-navier-stokes-credit) Se cita aquí solo como evidencia de que el ritmo de avance está generando fricciones institucionales reales y documentadas, no como parte del análisis energético.

**Implicación para este proyecto:** la recomendación de diseño ya adoptada en `docs/arquitectura-y-benchmarking.md` — que el sistema *recomiende* despacho, sin controlar el embalse automáticamente — es coherente con este mismo principio de avanzar por fases verificando cada paso, no solo una decisión técnica conservadora aislada.

## 5. Los números de Colombia

| Dato | Cifra (2026) | Fuente |
|---|---|---|
| Capacidad instalada total | 22.849 MW (58% hídrica = 13.232 MW; térmica 6.241 MW; solar 3.335 MW; eólica solo 41 MW) | [La República](https://www.larepublica.co/economia/xm-revelo-que-han-ingresado-321-mw-al-sistema-electrico-de-4-475-mw-esperados-para-2026-4424867) |
| Demanda proyectada 2026 | 92.900 GWh/año ≈ 10.600 MW promedio continuo | XM/UPME (vía prensa especializada) |
| Rezago de ejecución 2026 | Se esperaban 4.475 MW nuevos; solo entraron 291-321 MW | [Portafolio — XM alerta rezago](https://www.portafolio.co/energia/solo-han-entrado-291-mw-xm-alerta-fuerte-rezago-en-nuevos-proyectos-electricos-en-2026-ante-fenomeno-de-el-nino-493494) |

**Comparación con la escala real de infraestructura de IA:** el campus Anthropic-Amazon en New Carlisle (Indiana, proyecto "Rainier") opera con **~910 MW** — uno de los centros de datos de IA más grandes del mundo hoy. [Epoch AI](https://epoch.ai/graphs/largest-ai-data-centers-by-power-capacity)

**Lectura correcta de esta comparación:** Colombia, en capacidad bruta instalada, tiene margen teórico (22,8 GW instalados vs. ~13 GW de pico de demanda) para un campus de ese tamaño. La restricción real no es "no hay energía" — es que esa capacidad no está firme ni disponible en un solo punto de la red por limitaciones de transmisión, y que la capacidad nueva no está entrando al ritmo comprometido. El diagnóstico correcto es un problema de **transmisión y ejecución**, no de generación total. Esto conecta directamente con la línea 3 de investigación identificada en `docs/fase-0-investigacion-preliminar.md` (inspección automatizada de líneas de transmisión en relieve montañoso).

## 6. El precedente más comparable: Paraguay

Un país mucho más pequeño que Colombia, con un solo activo hídrico (su mitad de Itaipú, 7.000 MW), ya vivió esta transición:

- Atrajo más de 60 sitios de minería/IA en 3 años y más de USD 1.100 millones de inversión, gracias a electricidad limpia y barata.
- **Ya está topando con los mismos límites que enfrentaría Colombia**: capacidad de red de transmisión de solo ~5 GW, ausencia de marco regulatorio específico, necesidad de renegociar el tratado de Itaipú, y precios en alza (de 0,03 a 0,037-0,05 USD/kWh).

Fuente: [BNamericas — Paraguay's AI and crypto data center push](https://www.bnamericas.com/en/features/clean-energy-high-hopes-paraguays-big-ai-and-crypto-data-center-push)

**Lección:** tener el recurso hídrico no basta. El cuello de botella que aparece después siempre es transmisión y marco regulatorio — el mismo que ya identificamos como línea de investigación complementaria de este proyecto.

## 7. La pieza que conecta esto directamente con el sistema que ya se está construyendo

Los grandes compradores de energía para IA no buscan "renovable cualquiera" — buscan específicamente **"clean firm power"**: energía limpia pero firme, no intermitente. Google firmó en 2026 un acuerdo histórico de **3 GW de hidroeléctrica con Brookfield** (20 años, 670 MW iniciales), explícitamente porque el solar/eólico intermitente no alcanza para su meta de energía libre de carbono las 24 horas del día para 2030.

Fuente: [DCD — Google and Microsoft back 24/7 carbon-free energy](https://www.datacenterdynamics.com/en/news/google-and-microsoft-back-247-carbon-free-energy-marketplace/)

**Esto es exactamente lo que el sistema de despacho hídrico-solar de este repositorio está diseñado para producir**: energía hídrica firme, predecible, con evaporación optimizada mediante cobertura fotovoltaica flotante. La pieza técnica ya estaba en construcción antes de identificar este caso de uso — este documento no cambia el alcance técnico, le da un comprador y una narrativa de urgencia más fuerte.

## 8. Colombia ya tiene tracción real — a la escala correcta

Colombia ya está en el radar como hub regional de centros de datos — no de clústeres de entrenamiento de frontera de varios GW, que no son una meta realista a corto plazo, sino de colocación e inferencia regional:

- Mercado de data centers: USD 442 millones (2024) → USD 1.160 millones proyectados (2030), ~17,5% anual.
- 12 cables submarinos y salida a dos océanos — ventaja geográfica real.
- ODATA/Aligned invirtiendo USD 1.300 millones en dos centros de datos en Bogotá (operativos a fines de 2026); Internexa (ISA) ya opera uno en zona franca bogotana; tres cables submarinos nuevos en desarrollo.

Fuente: [Telesemana](https://www.telesemana.com/blog/2026/02/04/colombia-tiene-una-ubicacion-geografica-privilegiada-para-la-instalacion-de-data-centers-cuenta-con-12-cables-submarinos-y-salida-a-dos-oceanos/), [ACIS](https://www.acis.org.co/blog/noticias-2/data-centers-impulsan-una-nueva-ola-de-inversion-y-posicionan-a-colombia-como-hub-digital-en-america-latina-5721)

## 9. Oportunidad recomendada (dos capas, ninguna especulativa)

1. **Hub regional de inferencia/colocación** (decenas a cientos de MW, no GW) — aprovechando cables submarinos y energía limpia. Ya está ocurriendo; el rol de este proyecto es reforzar la confiabilidad energética que ese hub necesita.
2. **Exportador/certificador de energía limpia firme** — el mismo tipo de PPA de 20 años que Google firmó por hidroeléctricas en EE. UU. es replicable en Colombia *si* existe un sistema de despacho verificable y medible — que es exactamente lo que este repositorio está construyendo.

**Lo que explícitamente no se recomienda:** posicionar a Colombia para hospedar clústeres de entrenamiento de frontera de varios GW (tipo Stargate, Colossus, Hyperion). Esa escala requiere compromisos nacionales y años de ventaja que no son realistas en el horizonte de este proyecto.

## 10. Próximos pasos

- [ ] Profundizar la línea 3 de investigación (inspección de transmisión) ahora que hay un caso de uso económico explícito, no solo el argumento de mantenimiento en relieve montañoso.
- [ ] Investigar el marco regulatorio colombiano actual para PPAs de energía renovable firme de largo plazo (CREG) — si existe un vehículo legal comparable al usado por Google-Brookfield.
- [ ] Monitorear la evolución de Paraguay como caso de aprendizaje temprano (qué cuellos de botella regulatorios aparecen primero).
- [ ] Mantener el foco técnico del repositorio en el despacho hídrico-solar — este documento es contexto estratégico, no un cambio de alcance del Fase 1 en curso.
