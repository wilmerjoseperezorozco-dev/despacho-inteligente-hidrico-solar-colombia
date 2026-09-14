# Modelo de picos: clasificación de crecida + magnitud condicional

Responde a [issue #3](https://github.com/wilmerjoseperezorozco-dev/despacho-inteligente-hidrico-solar-colombia/issues/3). Ver también `docs/bug-q-hoy-faltante.md` — el bug ahí descrito se encontró precisamente al construir este modelo, y ya está corregido en los resultados de este documento.

## 1. Diseño

Implementado en [`src/modelo_picos_caudal.py`](../src/modelo_picos_caudal.py), enfoque tipo "hurdle" (umbral) en dos etapas, en vez de una regresión directa:

1. **Clasificador binario**: ¿el cambio de caudal de hoy a mañana será un evento de crecida? Umbral = percentil 90 de `|Δcaudal|` calculado **solo con datos de entrenamiento** (nunca se calcula sobre el test, para no filtrar información del futuro a la definición del propio evento).
2. **Regresor de magnitud**, entrenado únicamente sobre los días de evento del entrenamiento, con `log1p` del objetivo (igual justificación que en `docs/experimento-log-nare.md`).

Predicción final: si el clasificador predice evento, se usa el regresor de magnitud; si no, se usa persistencia simple (`Q(t+1)=Q(t)`).

## 2. Resultados reales — no supera a la regresión simple, sí mejora sobre persistencia en los eventos

**Guatapé** (período de prueba 2021-2026, 1.942 días, 233 de ellos eventos reales):

| Evaluación | Persistencia | Modelo de picos |
|---|---|---|
| NSE, todo el período | -0,04 | 0,132 |
| NSE, solo días de evento real | -1,85 | **-1,07** |
| RMSE, solo días de evento real (m³/s) | 59,84 | **50,96** |

**Nare** (mismo período, solo 57 eventos reales en test — la tasa de eventos cayó de 10% en train a 2,9% en test, señal de que el umbral fijo no generaliza bien a un período con menos crecidas):

| Evaluación | Persistencia | Modelo de picos |
|---|---|---|
| NSE, todo el período | 0,815 | 0,805 |
| NSE, solo días de evento real | -1,02 | -0,96 |

**Comparación clave — el modelo de picos NO supera a la regresión GBM simple ya corregida** (`docs/bug-q-hoy-faltante.md`): en Guatapé, NSE de todo el período es 0,132 (picos) frente a 0,272 (GBM regresión directa). La complejidad adicional del enfoque de dos etapas no se traduce en una mejora neta.

## 3. Por qué no ayuda más — el clasificador es el cuello de botella

| Río | Precisión | Recall | F1 |
|---|---|---|---|
| Guatapé | 0,714 | 0,279 | 0,401 |
| Nare | 0,333 | 0,070 | 0,116 |

El clasificador detecta correctamente menos de un tercio de los eventos reales de crecida (recall bajo en ambos ríos, especialmente Nare). Esto significa que, en la mayoría de los días que sí eran eventos, el modelo de picos termina usando persistencia de todas formas — el regresor de magnitud especializado, aunque mejor que persistencia cuando sí se activa, se activa muy pocas veces.

## 4. Conclusión honesta

El diseño de "hurdle" logra su objetivo parcial — mejora sobre persistencia específicamente en los días más difíciles (crecidas reales) para Guatapé — pero el recall bajo del clasificador limita ese beneficio, y en conjunto no supera a la regresión directa ya corregida. **No se recomienda adoptar este enfoque en su forma actual.** La limitación de fondo (los árboles de decisión no extrapolan más allá del rango de entrenamiento) tampoco se resuelve del todo: el PBIAS en los días de evento sigue siendo fuertemente negativo (-35% en Guatapé), es decir, sigue subestimando las crecidas más extremas incluso cuando el clasificador sí las detecta.

## 5. Pendiente

- [ ] Mejorar el recall del clasificador antes de reconsiderar este enfoque — probar un umbral de decisión distinto a 0,5 (dado que HistGradientBoostingClassifier expone probabilidades), o balancear las clases explícitamente durante el entrenamiento.
- [ ] Evaluar si un umbral de evento definido de forma adaptativa (ej. percentil móvil, no fijo desde el entrenamiento) mejora la generalización — el hallazgo de que la tasa de eventos de Nare cae de 10% a 2,9% entre train y test sugiere que un umbral fijo no es robusto a cambios de régimen hidrológico (ver el ciclo húmedo/seco 2021-2026 documentado en `docs/dataset-extendido-2000-2026.md`).
- [ ] Considerar un enfoque de cuantiles (regresión cuantílica) en vez de clasificación binaria + regresión, como alternativa que podría capturar mejor la incertidumbre de los eventos extremos sin depender de un umbral fijo.
