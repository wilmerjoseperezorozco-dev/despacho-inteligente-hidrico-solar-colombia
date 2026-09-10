# Arquitectura del sistema, métricas y benchmarking internacional

## 1. Arquitectura propuesta (6 capas)

```
[IDEAM/XM/telemetría embalse] → [Feature store] → [Modelo de caudal] → [Simulador de embalse]
                                                          ↓
                                              [Motor de optimización de despacho]
                                                          ↓
                                [Recomendación al operador — sin control automático directo]
                                                          ↓
                                          [Monitoreo de drift + reentrenamiento]
```

**Decisión de diseño:** en esta etapa el sistema **recomienda, no controla** el embalse. XM centraliza el despacho real del SIN mediante la función de costos de oportunidad del recurso hídrico; cualquier propuesta debe integrarse a esa lógica de mercado, no reemplazarla ni automatizar directamente un activo crítico sin años de validación previa.

1. **Ingesta**: series IDEAM (caudal, precipitación, temperatura por estación), SIMEM/XM (generación, precios de bolsa, aportes hídricos por central), telemetría o irradiancia satelital del piloto solar.
2. **Feature store**: series versionadas, con manejo explícito de huecos (frecuentes en estaciones IDEAM rurales/de páramo).
3. **Modelo de caudal**: línea base de persistencia climatológica + modelo ML (Gradient Boosting / LSTM) sobre variables de microclima, horizontes 24h / 7 días / 30 días.
4. **Simulador de embalse**: balance hídrico (entrada − salida − evaporación = Δvolumen) para hacer *backtesting* sin tocar el activo real.
5. **Motor de optimización**: v1 con reglas + programación lineal (explicable); v2 con programación estocástica o control predictivo (MPC).
6. **Monitoreo**: detección de *drift* del modelo y reentrenamiento programado.

## 2. Métricas

| Categoría | Métrica |
|---|---|
| Pronóstico de caudal | NSE (Nash-Sutcliffe), KGE (Kling-Gupta), RMSE, MAE, PBIAS |
| Riesgo operativo | Probabilidad de nivel crítico, días de anticipación de alerta, falsos positivos/negativos |
| Energético | MWh de energía firme entregada vs. línea base sin coordinación; energía solar aprovechada vs. vertida |
| Hídrico | m³ de evaporación evitada (modelo tipo Penman, cobertura vs. superficie descubierta) |
| Económico | Valor de energía firme adicional a precio de bolsa (XM); costo evitado de respaldo térmico |
| Sistema | Latencia del pipeline, tiempo de cómputo del optimizador, disponibilidad de datos |

## 3. Plan ejecutable — Fase 1

1. Fijar embalse de referencia (Guatapé/El Peñol, por el piloto EPM ya documentado) y delimitar cuenca aportante.
2. Descargar series históricas (10-15 años) de IDEAM (caudal, precipitación, temperatura, nivel) y SIMEM/XM (generación, precios, aportes hídricos).
3. EDA y documentación honesta de calidad/huecos de datos.
4. Modelo baseline de persistencia climatológica.
5. Modelo ML con validación *walk-forward* (no split aleatorio en series de tiempo).
6. Simulador de balance hídrico del embalse.
7. Motor de optimización v1 (reglas + programación lineal).
8. Backtesting contra operación histórica real observada.
9. Documentación y comparación honesta contra la línea base.

## 4. Líneas de investigación adicionales

- Datos satelitales de precipitación (CHIRPS, GPM/IMERG) para complementar huecos de estaciones IDEAM en páramo.
- Validación local del efecto de sombreado sobre evaporación en clima tropical andino (la literatura disponible es de climas distintos: EE.UU., India, China).
- Despacho multi-embalse, coherente con la operación centralizada real de XM.
- Riesgo climático de largo plazo (retroceso de páramos/glaciares) como variable adicional.
- Marco regulatorio CREG para remuneración de energía firme híbrida.

## 5. Benchmarking internacional — verificado con fuente en vivo (2026-09-10)

| País / Proyecto | Fuente | Estado de verificación | Datos confirmados |
|---|---|---|---|
| China — Longyangxia (Qinghai, río Amarillo) | Wikipedia (fetch directo) | ✅ Confirmado | Hidro 1.280 MW + solar 850 MWp (320 MWp en 2013 + 530 MWp en 2015). Único caso con **coordinación automática real**: el solar está acoplado a una turbina hidroeléctrica que regula la salida para equilibrar la generación solar variable antes de despachar a la red |
| Vietnam — Da Mi (Binh Thuan, EVN) | Wikipedia (fetch directo) | ✅ Confirmado | 47,5 MWp flotante (2019) sobre embalse hidroeléctrico |
| India — Omkareshwar (Narmada, NHDC) | Wikipedia (fetch directo, embalse) + fuente secundaria (capacidad solar) | ✅ Embalse confirmado (525 MW hidro) / ⚠️ Capacidad solar (90 MWp, 2024) de fuente secundaria, confianza media | Parque solar existe, referenciado desde la página del embalse |
| Portugal — Alqueva (EDP) | Múltiples fuentes (EDP, prensa especializada) | ✅ Confirmado | 5 MW / ~12.000 paneles / 7,5 GWh-año + batería 1 MW / 2 MWh integrada — único caso con batería de gestión activa |
| India — NTPC Ramagundam/Kayamkulam/Simhadri | Wikipedia | ✅ Existen, pero **no aplican como precedente** | Son flotantes sobre embalses de enfriamiento de plantas **térmicas**, no hidroeléctricas |
| Brasil — Sobradinho/Balbina | Búsqueda en vivo + Wikipedia de la represa | ❌ **No confirmado** | Sobradinho (1.050 MW, CHESF) existe como hidroeléctrica, pero ninguna fuente consultada menciona un piloto solar flotante asociado. Se descarta como referente hasta poder confirmarlo con una fuente concreta |

### Hallazgo clave
La mayoría de los casos globales de "solar flotante + hidro" son decisiones de **ubicación** (aprovechar el espejo de agua ya existente), igual que Guatapé y Urrá en Colombia — no sistemas de **coordinación de despacho en tiempo real**. De los casos confirmados, solo Longyangxia (acoplamiento físico solar-turbina) y Alqueva (batería de gestión activa) tienen una capa real de coordinación. Esto respalda que el vacío identificado para Colombia es real y poco común incluso a nivel internacional.

## 6. Literatura académica — confirmada con fuente en vivo

- [Short-term stochastic optimization of a hydro-wind-photovoltaic hybrid system under multiple uncertainties](https://www.researchgate.net/publication/341036170_Short-term_stochastic_optimization_of_a_hydro-wind-photovoltaic_hybrid_system_under_multiple_uncertainties)
- [Short-term stochastic multi-objective optimization scheduling of wind-solar-hydro hybrid system considering source-load uncertainties](https://www.sciencedirect.com/science/article/abs/pii/S0306261924011644) (2024)
- [Research on short-term optimal scheduling of hydro-wind-solar multi-energy power system based on deep reinforcement learning](https://www.researchgate.net/publication/366522223_Research_on_short-term_optimal_scheduling_of_hydro-wind-solar_multi-energy_power_system_based_on_deep_reinforcement_learning)
- [Multi-Task Deep Reinforcement Learning with Scenario Clustering for Real-Time Scheduling of Wind-Solar-Hydro Complementary Generation Systems](https://ietresearch.onlinelibrary.wiley.com/doi/abs/10.1049/rpg2.70070) (2025)
- [Optimal Scheduling of Hydro-Wind-Photovoltaic Complementary System Based on Reinforcement Learning-Proximal Policy Optimization](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/tje2.70087) (2025)

**Nota de alcance:** casi toda esta literatura trabaja sistemas hidro-eólico-solar (3 fuentes), no hidro-solar puro como el caso colombiano de este repositorio. Es una simplificación válida como punto de partida, pero debe quedar explícita como diferencia de alcance al comparar resultados.
