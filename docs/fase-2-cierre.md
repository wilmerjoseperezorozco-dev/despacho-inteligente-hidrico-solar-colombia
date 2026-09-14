# Cierre de Fase 2 — Modelo de predicción de caudal

## 1. Objetivo de la fase (cumplido)

Entrenar y validar un modelo de predicción de caudal a un día para el embalse Peñol-Guatapé, usando datos históricos reales, con validación honesta (walk-forward, métricas hidrológicas estándar) y documentación explícita de cualquier resultado negativo o limitación encontrada en el camino.

## 2. Modelo final y métricas vigentes

Dataset: 9.740 días (2000-2026, 100% de cobertura). Período de prueba: 2021-2026 (~1.942-1.947 días, walk-forward con reentrenamiento cada 30 días).

| Río | Modelo | NSE | KGE | PBIAS |
|---|---|---|---|---|
| Guatapé | Persistencia | -0,04 | 0,48 | 0,1% |
| **Guatapé** | **Gradient Boosting (final)** | **0,272-0,273** | 0,32 | ~0-1% |
| Nare | Persistencia | 0,815 | 0,91 | 0,1% |
| **Nare** | **Gradient Boosting + log1p (final)** | **0,833** | 0,82 | 1,2% |

**Nare supera a la persistencia** — el primer y único caso en todo el proyecto donde el modelo de aprendizaje automático le gana de forma clara al baseline más simple. **Guatapé mejora sustancialmente** sobre una persistencia que ni siquiera supera la media (NSE negativo), confirmando la hipótesis original: los ríos con pulsos de crecida abruptos se benefician más de un modelo con predictores adicionales.

Script de referencia: [`src/modelo_gbm_regularizado.py`](../src/modelo_gbm_regularizado.py) (sin flags adicionales para Guatapé; `--log-objetivo` para Nare).

## 3. Últimas verificaciones antes de cerrar

**Riotex, verificación final**: con el bug de `q_hoy` ya corregido, se repitió el experimento de excluir la estación IDEAM Riotex de Guatapé (que había sido revertido una vez al extender el dataset). Resultado: NSE 0,2733 sin Riotex vs. 0,2716 con Riotex — diferencia despreciable. **Conclusión definitiva: Riotex es una variable neutral para este modelo**, ni ayuda ni perjudica de forma significativa. Se mantiene en el modelo por simplicidad (evitar una rama de código adicional sin beneficio real).

## 4. Todo lo que se probó y no funcionó (tan importante como lo que sí)

| Intento | Resultado | Por qué se documenta |
|---|---|---|
| Gradient Boosting v1 (hiperparámetros manuales) | Sobreajuste real (gap >0,3) | Motivó atacar el problema con herramientas correctas, no ajuste a ojo |
| Regularización L2 + validación cruzada temporal, dataset corto | Ninguna configuración bajó el gap de 0,3 | Reveló que el problema era volumen de datos, no configuración |
| Remover Riotex (dataset corto) | Mejora de +70% | Luego no se replicó — lección sobre no generalizar de una muestra pequeña |
| Transformación log1p en Nare | Mejora real pero parcial | Terminó siendo clave una vez corregido el bug de `q_hoy` |
| Modelo de picos (clasificación + magnitud) | No superó la regresión simple | Cerrado como *not planned* (issue #3), causa (bajo recall) documentada |

## 5. Limitación conocida que se traslada a Fase 3, no bloquea el cierre

**Corrección de sesgo satelital de CHIRPS ([issue #5](https://github.com/wilmerjoseperezorozco-dev/despacho-inteligente-hidrico-solar-colombia/issues/5))**: sigue sin implementarse. Al revisarlo para este cierre, se confirma que es más laborioso de lo que parecía inicialmente — IDEAM no publica un producto diario curado de precipitación (`docs/datos-ideam-caudal.md`), así que aplicar un ajuste de cuantiles real requeriría primero construir un pipeline nuevo para agregar el acumulado crudo de 10 minutos de las estaciones automáticas a series diarias, antes de poder comparar contra CHIRPS. Esto es trabajo adicional real, no un ajuste rápido — se decide **no bloquear el cierre de Fase 2 por esto**: el modelo actual es honesto sobre su limitación (documentada desde `docs/datos-satelitales-precipitacion.md`), y la corrección de sesgo es una mejora de calidad de datos que puede abordarse en paralelo a Fase 3, no un prerrequisito para avanzar.

## 6. Conclusión

Fase 2 se da por **completada**. El modelo no es perfecto ni está listo para uso operativo — tiene una limitación estructural conocida (no extrapola picos extremos) y una fuente de datos sin corrección de sesgo — pero está validado con honestidad, documentado con cada decisión y cada error real encontrado en el camino, y en al menos un río supera de forma demostrable al mejor baseline disponible. Es una base sólida para que Fase 3 (motor de optimización de despacho) tenga una señal de entrada confiable.
