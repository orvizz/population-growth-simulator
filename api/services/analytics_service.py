"""
AnalyticsService — pure computation module for ecological analytics.

This module has NO database, HTTP, or FastAPI dependencies. It derives
ecological analytics from a population projection matrix (deterministic)
or from a stochastic simulation run.

References
----------
Caswell, H. (2001). Matrix Population Models. Sinauer Associates.
"""
from __future__ import annotations

import math

import numpy as np


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_array(matrix_a: list[list[float | None]]) -> np.ndarray:
    """Convert a nested list (with possible None cells) to a float64 ndarray.

    None values are treated as 0.0, consistent with COMPADRE incomplete
    entries convention used throughout this codebase.
    """
    return np.array(
        [[0.0 if v is None else float(v) for v in row] for row in matrix_a],
        dtype=float,
    )


def _dominant_eigenpair(A: np.ndarray) -> tuple[float, np.ndarray]:
    """Return the dominant (largest real part) eigenvalue and right eigenvector of A.

    Parameters
    ----------
    A : np.ndarray
        Square matrix.

    Returns
    -------
    lambda_1 : float
        Dominant eigenvalue (real part).
    w : np.ndarray
        Corresponding right eigenvector (real part), NOT yet normalised.
    """
    eigenvalues, eigenvectors = np.linalg.eig(A)
    idx = np.argmax(eigenvalues.real)
    lambda_1 = float(eigenvalues[idx].real)
    w = eigenvectors[:, idx].real
    return lambda_1, w


def _left_eigenvector(A: np.ndarray, lambda_1: float) -> np.ndarray:
    """Return the left eigenvector corresponding to lambda_1.

    The left eigenvectors of A are the right eigenvectors of Aᵀ.
    The matching eigenvalue is the one whose real part is closest to lambda_1.

    Parameters
    ----------
    A : np.ndarray
        Square matrix.
    lambda_1 : float
        Target eigenvalue (dominant real eigenvalue of A).

    Returns
    -------
    v : np.ndarray
        Left eigenvector (real part), NOT yet normalised.
    """
    eigenvalues, eigenvectors = np.linalg.eig(A.T)
    # Find the eigenvalue index whose real part is closest to lambda_1
    idx = int(np.argmin(np.abs(eigenvalues.real - lambda_1)))
    v = eigenvectors[:, idx].real
    return v


def _compute_sensitivities(v: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Sensitivity matrix  sᵢⱼ = (vᵢ · wⱼ) / (vᵀ · w).

    Parameters
    ----------
    v : np.ndarray
        Left eigenvector (reproductive value), normalised so v[0] = 1.
    w : np.ndarray
        Right eigenvector (stable stage distribution), normalised to sum 1.

    Returns
    -------
    S : np.ndarray
        n×n sensitivity matrix.
    """
    denom = float(v @ w)
    if abs(denom) < 1e-14:
        return np.zeros((len(v), len(w)))
    # Outer product: S[i,j] = v[i] * w[j] / denom
    S = np.outer(v, w) / denom
    return S


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_deterministic_analytics(
    matrix_a: list[list[float | None]],
    stage_names: list[str] | None = None,
) -> dict:
    """Compute ecological analytics for a deterministic Leslie/Lefkovitch matrix.

    Parameters
    ----------
    matrix_a : list[list[float | None]]
        n×n transition matrix. None cells are treated as 0.0.
    stage_names : list[str] | None
        Optional stage labels; passed through to the result dict unchanged.

    Returns
    -------
    dict with keys:
        lambda_1 : float
            Dominant real eigenvalue of A. Represents the long-run deterministic
            finite population growth rate (λ > 1 = growth, λ < 1 = decline).
        stable_stage_distribution : list[float]
            Right eigenvector **w** of λ₁, normalised so Σwᵢ = 1 and all
            values are non-negative (sign ambiguity resolved by taking |·|).
            Gives the proportional stage composition at stable equilibrium.
        reproductive_value : list[float]
            Left eigenvector **v** of λ₁, normalised so v[0] = 1 and all
            values are non-negative. Gives the relative contribution of each
            stage class to future population growth.
        sensitivities : list[list[float]]
            sᵢⱼ = (vᵢ · wⱼ) / (**v**ᵀ · **w**).
            Absolute sensitivity of λ₁ to a small perturbation in element aᵢⱼ.
        elasticities : list[list[float]]
            eᵢⱼ = (aᵢⱼ / λ₁) · sᵢⱼ.
            Proportional sensitivity. For a non-negative irreducible matrix the
            sum of all elasticities equals 1. Useful for comparing the relative
            importance of life-history transitions.
        analytics_reliable : bool
            Always True for deterministic analytics.
        stage_names : list[str] | None
            Pass-through of the input argument.
    """
    A = _to_array(matrix_a)
    n = A.shape[0]

    lambda_1, w_raw = _dominant_eigenpair(A)
    v_raw = _left_eigenvector(A, lambda_1)

    # --- stable stage distribution: |w| normalised to sum 1 ---------------
    w_abs = np.abs(w_raw)
    w_sum = w_abs.sum()
    if w_sum < 1e-14:
        stable_stage = [0.0] * n
    else:
        w_norm = w_abs / w_sum
        stable_stage = w_norm.tolist()

    # --- reproductive value: |v| normalised so first element = 1 ----------
    v_abs = np.abs(v_raw)
    if abs(v_abs[0]) < 1e-14:
        repro_value = [0.0] * n
        v_norm = v_abs  # fallback; sensitivities will be zeroed by lambda check
    else:
        v_norm = v_abs / v_abs[0]
        repro_value = v_norm.tolist()

    # --- sensitivities & elasticities --------------------------------------
    if abs(lambda_1) < 1e-10:
        # Degenerate matrix — analytics not meaningful
        sensitivities = [[0.0] * n for _ in range(n)]
        elasticities = [[0.0] * n for _ in range(n)]
        analytics_reliable = False
    else:
        # Use normalised vectors for the sensitivity formula
        w_for_sens = np.array(stable_stage, dtype=float)
        v_for_sens = v_norm
        S = _compute_sensitivities(v_for_sens, w_for_sens)
        E = (A / lambda_1) * S  # element-wise: eᵢⱼ = (aᵢⱼ / λ₁) · sᵢⱼ
        sensitivities = S.tolist()
        elasticities = E.tolist()
        analytics_reliable = True

    return {
        "lambda_1": lambda_1,
        "stable_stage_distribution": stable_stage,
        "reproductive_value": repro_value,
        "sensitivities": sensitivities,
        "elasticities": elasticities,
        "analytics_reliable": analytics_reliable,
        "stage_names": stage_names,
    }


def compute_stochastic_analytics(
    matrices_snapshot: list[list[list[float | None]]],
    matrix_sequence: list[int],
    result_history: list[list[float]],
    stage_names: list[str] | None = None,
    n_steps_threshold: int = 20,
) -> dict:
    """Compute ecological analytics for a stochastic simulation run.

    Parameters
    ----------
    matrices_snapshot : list[list[list[float | None]]]
        The k matrices used in the simulation. Each matrix is an n×n nested
        list with possible None cells.
    matrix_sequence : list[int]
        Index (into matrices_snapshot) of the matrix chosen at each time step.
        Length equals n_steps (the number of transitions, NOT population states).
    result_history : list[list[float]]
        Population vector at each time point, including the initial vector.
        Length equals n_steps + 1.
    stage_names : list[str] | None
        Optional stage labels; passed through unchanged.
    n_steps_threshold : int
        Minimum number of steps required for reliable stochastic analytics.
        Default is 20.

    Returns
    -------
    dict with keys:
        lambda_s : float
            Stochastic long-run growth rate.
            Computed as exp( (1/T) · Σₜ log(‖v(t+1)‖ / ‖v(t)‖) )
            where T = number of valid transitions (steps where both norms > 0).
            Represents the long-run multiplicative growth factor per time step.
        mean_matrix : list[list[float]]
            Ā = Σₖ (nₖ / T) · Aₖ where nₖ = number of times matrix k was
            chosen and T = total steps. This is the frequency-weighted average
            transition matrix over the observed run.
        lambda_1_of_mean : float
            Dominant real eigenvalue of Ā. Provides a deterministic
            approximation to λs under the mean-field assumption.
        elasticities_of_mean : list[list[float]]
            Elasticities of Ā, computed with the same formula as for the
            deterministic case. Shows the proportional importance of each
            element in the mean environment.
        stable_stage_distribution_of_mean : list[list[float]]
            Right eigenvector of Ā normalised to sum 1, giving the equilibrium
            stage distribution under the mean-environment approximation.
        analytics_reliable : bool
            True iff len(matrix_sequence) >= n_steps_threshold.
        stage_names : list[str] | None
            Pass-through of the input argument.
    """
    T = len(matrix_sequence)
    arrays = [_to_array(m) for m in matrices_snapshot]
    n = arrays[0].shape[0] if arrays else 0

    # --- stochastic growth rate λ_s ----------------------------------------
    # λ_s = exp( (1/T) Σₜ log(‖v(t+1)‖ / ‖v(t)‖) )
    # Skip steps where either norm is zero to avoid log(0).
    log_growth_sum = 0.0
    valid_steps = 0
    for t in range(T):
        norm_t = math.sqrt(sum(x * x for x in result_history[t]))
        norm_t1 = math.sqrt(sum(x * x for x in result_history[t + 1]))
        if norm_t > 0 and norm_t1 > 0:
            log_growth_sum += math.log(norm_t1 / norm_t)
            valid_steps += 1

    if valid_steps > 0:
        lambda_s = math.exp(log_growth_sum / valid_steps)
    else:
        lambda_s = 0.0

    # --- frequency-weighted mean matrix Ā ------------------------------------
    counts = [0] * len(arrays)
    for idx in matrix_sequence:
        counts[idx] += 1

    mean_A = np.zeros((n, n), dtype=float)
    if T > 0:
        for k, arr in enumerate(arrays):
            mean_A += (counts[k] / T) * arr

    # --- analytics of the mean matrix ----------------------------------------
    det_analytics = compute_deterministic_analytics(mean_A.tolist(), stage_names=stage_names)

    analytics_reliable = T >= n_steps_threshold

    return {
        "lambda_s": lambda_s,
        "mean_matrix": mean_A.tolist(),
        "lambda_1_of_mean": det_analytics["lambda_1"],
        "elasticities_of_mean": det_analytics["elasticities"],
        "stable_stage_distribution_of_mean": det_analytics["stable_stage_distribution"],
        "analytics_reliable": analytics_reliable,
        "stage_names": stage_names,
    }
