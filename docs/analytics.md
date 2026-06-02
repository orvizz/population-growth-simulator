# Analytics Reference

This document describes every metric computed by `AnalyticsService` and `QuasiExtinctionService`, including the mathematical formula, notation, implementation notes, and reliability caveats.

All computation lives in `api/services/analytics_service.py` (pure math, no DB or HTTP). The quasi-extinction core computation lives in `api/services/quasi_extinction_service.py` (`_compute_quasi_extinction`).

---

## 1. Deterministic Analytics

Computed by `compute_deterministic_analytics(matrix_a, stage_names)`.

Applied to a single Leslie/Lefkovitch matrix **A** of size n×n.

### 1.1 Dominant Eigenvalue (λ₁)

**Symbol:** `lambda_1`  
**Type:** `float`  
**Formula:** largest real part among all eigenvalues of **A**

```
eigenvalues, right_vecs = np.linalg.eig(A)
idx = argmax(Re(eigenvalues))
λ₁ = Re(eigenvalues[idx])
```

**Interpretation:**  
- λ₁ > 1 → population growing long-term  
- λ₁ < 1 → population declining long-term  
- λ₁ = 1 → population at equilibrium  

Only the real part is used; imaginary parts arise from complex eigenvalues (common in cyclic populations) and are discarded.

---

### 1.2 Stable Stage Distribution (w)

**Symbol:** `stable_stage_distribution`  
**Type:** `list[float]` of length n, sums to 1  
**Formula:** right eigenvector of λ₁, normalised to unit sum

```
w = Re(right_vecs[:, idx])   # real part of eigenvector for λ₁
w = w / sum(w)               # normalise so Σwᵢ = 1
```

**Interpretation:** proportional stage composition at demographic equilibrium — if the population grows with matrix **A** indefinitely, the ratio of stage sizes converges to **w**.

---

### 1.3 Reproductive Value (v)

**Symbol:** `reproductive_value`  
**Type:** `list[float]` of length n, first element = 1  
**Formula:** left eigenvector of λ₁, normalised so v[0] = 1

```
eigenvalues_T, left_vecs = np.linalg.eig(A.T)
idx_T = argmax(Re(eigenvalues_T))   # same eigenvalue, different vector
v = Re(left_vecs[:, idx_T])
v = v / v[0]                        # normalise so v₀ = 1
```

**Interpretation:** relative contribution of each stage to future population growth. An individual in stage i contributes v[i] times as much to long-run population as an individual in stage 0 (the reference stage).

---

### 1.4 Sensitivities (S)

**Symbol:** `sensitivities`  
**Type:** `list[list[float]]`, shape n×n  
**Formula:**

```
sᵢⱼ = (vᵢ · wⱼ) / (vᵀ · w)
```

where `·` denotes element-wise multiplication in the outer product numerator, and `vᵀ · w` is the standard dot product (scalar denominator).

**Interpretation:** absolute sensitivity of λ₁ to a unit change in matrix element aᵢⱼ. A high s₂₁ means that slightly changing the survival/growth rate from stage 1 to stage 2 strongly affects the population growth rate.

---

### 1.5 Elasticities (E)

**Symbol:** `elasticities`  
**Type:** `list[list[float]]`, shape n×n  
**Property:** Σᵢⱼ eᵢⱼ = 1 (always)  
**Formula:**

```
eᵢⱼ = (aᵢⱼ / λ₁) · sᵢⱼ
```

**Interpretation:** proportional sensitivity — the fraction by which λ₁ changes per proportional change in aᵢⱼ. Unlike sensitivities, elasticities are scale-free and sum to exactly 1, making them directly comparable across transitions and species. The element with the highest elasticity identifies the "most important" life-history transition for population viability.

---

### 1.6 Reliability Flag

**Symbol:** `analytics_reliable`  
**Type:** `bool`  
**Logic:** `True` if λ₁ > 1e-10, `False` otherwise.

A near-zero dominant eigenvalue indicates a degenerate or all-zero matrix. In this case, eigenvectors are numerically ill-defined and the analytics should not be trusted. Set to `False` in that situation.

---

## 2. Stochastic Analytics

Computed by `compute_stochastic_analytics(matrices_snapshot, matrix_sequence, result_history, stage_names)`.

Applied to a stochastic simulation with k matrices and T time steps.

**Inputs:**  
- `matrices_snapshot`: list of k matrices, each n×n  
- `matrix_sequence`: list of T integer indices (which matrix was chosen at each step)  
- `result_history`: list of T+1 population vectors (v(0), v(1), …, v(T))  

---

### 2.1 Stochastic Growth Rate (λ_s)

**Symbol:** `lambda_s`  
**Type:** `float`  
**Formula:**

```
λ_s = exp( (1/T) · Σₜ₌₁ᵀ log( ‖v(t)‖ / ‖v(t-1)‖ ) )
```

where `‖·‖` is the Euclidean norm (L2 norm), and only steps where both norms are positive are included.

**Interpretation:** the geometric mean per-step growth factor of the population norm. λ_s > 1 → population grows stochastically; λ_s < 1 → population goes quasi-extinct.

**Note:** λ_s is estimated from a single realisation of the stochastic process. It converges to the true stochastic growth rate (Tuljapurkar's λ_s) as T → ∞. For short simulations (T < 20), the estimate is noisy and `analytics_reliable` is set to `False`.

---

### 2.2 Mean Matrix (Ā)

**Symbol:** `mean_matrix`  
**Type:** `list[list[float]]`, shape n×n  
**Formula:**

```
Ā = Σₖ (nₖ / T) · Aₖ
```

where nₖ is the number of times matrix k was chosen in `matrix_sequence` and T is the total number of steps.

**Interpretation:** frequency-weighted average of the k matrices over the realised trajectory. This is not the simple arithmetic mean — it weights each matrix by how often it was actually used.

---

### 2.3 Dominant Eigenvalue of Mean Matrix (λ₁(Ā))

**Symbol:** `lambda_1_of_mean`  
**Type:** `float`  
**Formula:** same eigenvalue computation as §1.1, applied to Ā

**Interpretation:** deterministic approximation of the stochastic growth rate. In the small-variance limit, λ₁(Ā) ≈ λ_s + O(σ²).

---

### 2.4 Elasticities of Mean Matrix

**Symbol:** `elasticities_of_mean`  
**Type:** `list[list[float]]`, shape n×n  
**Formula:** same elasticity computation as §1.5, applied to Ā

**Interpretation:** proportional importance of each transition in the mean environment. Identifies which life-history transitions matter most when averaging over stochastic variation.

---

### 2.5 Stable Stage Distribution of Mean Matrix

**Symbol:** `stable_stage_distribution_of_mean`  
**Type:** `list[float]`, sums to 1  
**Formula:** same as §1.2, applied to Ā

---

### 2.6 Reliability Flag

**Symbol:** `analytics_reliable`  
**Type:** `bool`  
**Logic:** `True` if T ≥ 20 AND at least one valid log-growth step exists; `False` otherwise.

---

## 3. Quasi-Extinction Probability

Computed by `_compute_quasi_extinction(params, matrices_snapshot)` (module-level function in `quasi_extinction_service.py`).

### 3.1 Algorithm

For each of `n_runs` Monte Carlo runs:
1. Initialise population vector `v = initial_vector`
2. For each step t = 1 … n_steps:
   a. Uniformly sample a matrix index `i ~ Uniform{0, …, k-1}`
   b. Update `v = A_i @ v`
   c. If `sum(v) < extinction_threshold` at this step, record `extinct_at = t` (first crossing)
3. Record final population and per-run λ_s

Reproducibility is guaranteed: a master RNG (`np.random.default_rng(random_seed)`) generates per-run child seeds so each run is independent and the full set is deterministic given the same seed.

---

### 3.2 Output Fields

| Key | Type | Formula / Description |
|---|---|---|
| `n_runs` | int | Total Monte Carlo runs executed |
| `n_extinct` | int | Runs where total pop < threshold at some step |
| `quasi_extinction_probability` | float ∈ [0, 1] | `n_extinct / n_runs` |
| `extinction_threshold` | float | Threshold used (copied from input) |
| `time_to_extinction_distribution` | dict[str, int] | `{step: count}` for runs that went extinct; keys are string-encoded step numbers; only covers extinct runs |
| `mean_final_population` | float | Mean of `sum(v(T))` across all runs |
| `std_final_population` | float | Std dev of `sum(v(T))` across all runs |
| `lambda_s_distribution` | list[float] | Per-run λ_s estimate (length = `n_runs`) |

---

### 3.3 Per-run λ_s Estimation

```
λ_s^(r) = exp( (1/valid_steps) · Σₜ log(‖v(t)‖ / ‖v(t-1)‖) )
```

If `valid_steps == 0` (all norms are zero — population immediately extinct), λ_s^(r) = 0.

---

### 3.4 None → 0.0 Convention

COMPADRE matrices sometimes have `None` cells (missing/unknown transitions). Throughout the analytics and quasi-extinction code, `None` values are coerced to `0.0` before any numpy computation:

```python
[[0.0 if v is None else float(v) for v in row] for row in matrix]
```

This is consistent with the COMPADRE convention that unknown transitions are treated as absent (zero contribution).

---

## 4. Export / Import Format

Simulations exported via `GET /v1/simulations/{id}/export` include all analytics in `format_version: "2"`:

```json
{
  "format_version": "2",
  "matrices_snapshot": [[[ ... ]]],
  "matrix_sequence": [0, 1, 0, 0, 1, ...],
  "analytics": {
    "lambda_1": 1.23,
    "stable_stage_distribution": [0.4, 0.6],
    ...
  },
  ...
}
```

Legacy exports (`format_version: "1"`) have `null` for all three new fields. Both formats are accepted by `POST /v1/simulations/import`.

---

## 5. Caveats and Known Limitations

- **Single trajectory estimate:** λ_s is estimated from one stochastic trajectory. For accurate estimates, use `n_steps ≥ 50` and run multiple quasi-extinction simulations.
- **Imaginary eigenvalues:** For matrices with complex dominant eigenvalues (e.g., strong two-stage oscillations), only the real part is used. This may give counter-intuitive results for highly oscillatory systems.
- **Zero-matrix degenerate case:** An all-zero matrix yields λ₁ = 0, `analytics_reliable = False`, and division-by-zero in sensitivities/elasticities — these are set to zero matrices.
- **COMPADRE None cells:** Set to 0.0 (absent transition). If a matrix has many unknown cells, analytical results should be interpreted cautiously.
- **Quasi-extinction threshold:** The threshold applies to the *sum* of all stage populations. Stage-specific extinction thresholds are not currently supported.
