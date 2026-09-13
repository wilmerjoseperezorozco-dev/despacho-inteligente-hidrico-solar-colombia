"""
Métricas estándar de hidrología para evaluar pronósticos de caudal.

No se usa RMSE/MAE genéricos como única referencia: NSE y KGE son el
estándar del campo porque penalizan explícitamente el desempeño en picos
de caudal, que es lo que más importa para prevenir vaciados críticos o
crecidas (ver docs/arquitectura-y-benchmarking.md, sección de métricas).
"""

import numpy as np


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    """Nash-Sutcliffe Efficiency. 1 = perfecto, 0 = tan bueno como predecir la media, <0 = peor que la media."""
    obs, sim = np.asarray(obs, dtype=float), np.asarray(sim, dtype=float)
    return 1 - np.sum((obs - sim) ** 2) / np.sum((obs - obs.mean()) ** 2)


def kge(obs: np.ndarray, sim: np.ndarray) -> dict:
    """Kling-Gupta Efficiency y sus tres componentes (correlación, variabilidad, sesgo)."""
    obs, sim = np.asarray(obs, dtype=float), np.asarray(sim, dtype=float)
    r = np.corrcoef(obs, sim)[0, 1]
    alpha = sim.std() / obs.std()
    beta = sim.mean() / obs.mean()
    valor = 1 - np.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2)
    return {"kge": valor, "r": r, "alpha_variabilidad": alpha, "beta_sesgo": beta}


def pbias(obs: np.ndarray, sim: np.ndarray) -> float:
    """Sesgo porcentual. Positivo = el modelo sobreestima, negativo = subestima."""
    obs, sim = np.asarray(obs, dtype=float), np.asarray(sim, dtype=float)
    return 100 * np.sum(sim - obs) / np.sum(obs)


def rmse(obs: np.ndarray, sim: np.ndarray) -> float:
    obs, sim = np.asarray(obs, dtype=float), np.asarray(sim, dtype=float)
    return float(np.sqrt(np.mean((obs - sim) ** 2)))


def mae(obs: np.ndarray, sim: np.ndarray) -> float:
    obs, sim = np.asarray(obs, dtype=float), np.asarray(sim, dtype=float)
    return float(np.mean(np.abs(obs - sim)))


def resumen_metricas(obs: np.ndarray, sim: np.ndarray) -> dict:
    resultado_kge = kge(obs, sim)
    return {
        "nse": round(float(nse(obs, sim)), 4),
        "kge": round(float(resultado_kge["kge"]), 4),
        "kge_r": round(float(resultado_kge["r"]), 4),
        "kge_alpha_variabilidad": round(float(resultado_kge["alpha_variabilidad"]), 4),
        "kge_beta_sesgo": round(float(resultado_kge["beta_sesgo"]), 4),
        "rmse_m3s": round(rmse(obs, sim), 4),
        "mae_m3s": round(mae(obs, sim), 4),
        "pbias_pct": round(float(pbias(obs, sim)), 2),
    }
