"""Local-only, model-agnostic fairness audit of held-out binary predictions.

No individual records, training data or prediction scores are exposed by MCP.
This module does not train predictive models and does not certify fairness.
"""
from __future__ import annotations

import csv
import math
import random
from pathlib import Path

_ALLOWED_GROUPS = {"raca_cor": {"1", "2", "3", "4", "5", "9"},
                   "sexo": {"M", "F", "I"}}
_MAX_BYTES = 256 * 1024 * 1024
_MAX_ROWS = 2_000_000


def _auc(pairs: list[tuple[float, int]]) -> float:
    """Mann-Whitney AUROC using mean ranks for tied scores."""
    ordered = sorted(pairs)
    npos = sum(label for _, label in ordered)
    nneg = len(ordered) - npos
    if not npos or not nneg:
        raise ValueError("AUROC exige ambas as classes")
    rank_pos = 0.0
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][0] == ordered[i][0]:
            j += 1
        mean_rank = (i + 1 + j) / 2
        rank_pos += mean_rank * sum(label for _, label in ordered[i:j])
        i = j
    return (rank_pos - npos * (npos + 1) / 2) / (npos * nneg)


def _average_precision(pairs: list[tuple[float, int]]) -> float:
    """Non-interpolated average precision with correctly handled ties."""
    pos = sum(y for _, y in pairs)
    if not pos:
        raise ValueError("AP exige positivos")
    ordered = sorted(pairs, reverse=True)
    hits = 0
    result = 0.0
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][0] == ordered[i][0]:
            j += 1
        new_pos = sum(label for _, label in ordered[i:j])
        hits += new_pos
        result += (new_pos / pos) * (hits / j)
        i = j
    return result


def _metrics(pairs: list[tuple[float, int]], threshold: float) -> dict:
    n = len(pairs)
    tp = sum(y == 1 and p >= threshold for p, y in pairs)
    fp = sum(y == 0 and p >= threshold for p, y in pairs)
    fn = sum(y == 1 and p < threshold for p, y in pairs)
    tn = n - tp - fp - fn
    bins = [[0, 0.0, 0.0] for _ in range(10)]
    for p, y in pairs:
        k = min(int(p * 10), 9)
        bins[k][0] += 1
        bins[k][1] += p
        bins[k][2] += y
    ece = sum(abs(sump / count - sumy / count) * count / n
              for count, sump, sumy in bins if count)
    return {
        "n": n,
        "prevalencia_observada": (tp + fn) / n,
        "taxa_predicao_positiva": (tp + fp) / n,
        "sensibilidade_tpr": tp / (tp + fn) if tp + fn else None,
        "fpr": fp / (fp + tn) if fp + tn else None,
        "precisao_ppv": tp / (tp + fp) if tp + fp else None,
        "auroc": _auc(pairs),
        "average_precision": _average_precision(pairs),
        "brier": sum((p - y) ** 2 for p, y in pairs) / n,
        "ece_10_bins": ece,
    }


def _gaps(metrics: dict[str, dict]) -> dict:
    if len(metrics) < 2:
        return {"spd": None, "eod": None, "aaod": None}
    rates = [v["taxa_predicao_positiva"] for v in metrics.values()]
    tprs = [v["sensibilidade_tpr"] for v in metrics.values()]
    pairs = list(metrics.values())
    aaod = max(
        (abs(a["sensibilidade_tpr"] - b["sensibilidade_tpr"]) +
         abs(a["fpr"] - b["fpr"])) / 2
        for i, a in enumerate(pairs) for b in pairs[i + 1:]
    )
    return {"spd": max(rates) - min(rates),
            "eod": max(tprs) - min(tprs),
            "aaod": aaod}


def audit_predictions(path: str | Path, *, group: str, threshold: float = 0.5,
                      min_group: int = 50, bootstrap: int = 0,
                      seed: int = 42, cohort: str = "nao_informada") -> dict:
    """Evaluate *held-out* label/score/group CSV; never return record-level data.

    The caller must guarantee outcome maturity, no leakage, and appropriate
    sampling. Bootstrap is individual-row IID; it is not cluster-aware.
    """
    if group not in _ALLOWED_GROUPS:
        raise ValueError("Grupo permitido: raca_cor ou sexo")
    if not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError("Limiar deve estar estritamente entre 0 e 1")
    if not isinstance(min_group, int) or isinstance(min_group, bool) or not 50 <= min_group <= 10000:
        raise ValueError("min_group deve estar entre 50 e 10000")
    if not isinstance(bootstrap, int) or isinstance(bootstrap, bool) or not 0 <= bootstrap <= 1000:
        raise ValueError("bootstrap deve estar entre 0 e 1000")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed deve ser um inteiro")
    if not isinstance(cohort, str) or len(cohort) > 120:
        raise ValueError("Coorte inválida")
    csv_path = Path(path).expanduser().resolve(strict=True)
    if csv_path.suffix.lower() != ".csv" or csv_path.stat().st_size > _MAX_BYTES:
        raise ValueError("CSV inválido ou maior que 256 MiB")
    groups: dict[str, list[tuple[float, int]]] = {}
    rows = 0
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"y_true", "y_score", group}.issubset(reader.fieldnames):
            raise ValueError(f"Colunas obrigatórias: y_true,y_score,{group}")
        for record in reader:
            rows += 1
            if rows > _MAX_ROWS:
                raise ValueError("Arquivo ultrapassou o limite de linhas da auditoria")
            label = (record["y_true"] or "").strip()
            g = (record[group] or "").strip().upper()
            if label not in {"0", "1"} or g not in _ALLOWED_GROUPS[group]:
                raise ValueError("Rótulo binário ou grupo não reconhecido")
            try:
                score = float(record["y_score"])
            except (TypeError, ValueError) as exc:
                raise ValueError("Pontuação de risco inválida") from exc
            if not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError("Pontuação de risco deve estar entre 0 e 1")
            groups.setdefault(g, []).append((score, int(label)))
    eligible: dict[str, list[tuple[float, int]]] = {}
    for g, pairs in groups.items():
        positives = sum(y for _, y in pairs)
        if len(pairs) >= min_group and positives >= 10 and len(pairs) - positives >= 10:
            eligible[g] = pairs
    metrics = {g: _metrics(pairs, threshold) for g, pairs in sorted(eligible.items())}
    gaps = _gaps(metrics)
    intervals = None
    if bootstrap and len(eligible) >= 2:
        rng = random.Random(seed)
        replicate_gaps = {"spd": [], "eod": [], "aaod": []}
        for _ in range(bootstrap):
            sampled = {}
            for g, pairs in eligible.items():
                draw = [pairs[rng.randrange(len(pairs))] for _ in pairs]
                ys = sum(y for _, y in draw)
                if not ys or ys == len(draw):
                    sampled = {}
                    break
                sampled[g] = _metrics(draw, threshold)
            if len(sampled) != len(eligible):
                continue
            for key, value in _gaps(sampled).items():
                replicate_gaps[key].append(value)
        intervals = {}
        for key, values in replicate_gaps.items():
            values.sort()
            if not values:
                intervals[key] = None
            else:
                intervals[key] = {
                    "inferior_2_5pct": values[int((len(values)-1)*0.025)],
                    "superior_97_5pct": values[int((len(values)-1)*0.975)],
                    "replicacoes_validas": len(values),
                }
    return {
        "tipo": "auditoria_local_exploratoria_de_equidade",
        "grupo": group, "coorte_de_teste_informada": cohort,
        "limiar_classificacao": threshold, "n_registros_avaliados": rows,
        "grupos_elegiveis": metrics,
        "n_grupos_insuficientes": len(groups) - len(eligible),
        "disparidades": gaps, "bootstrap_iid_percentil": intervals,
        "definicoes": {
            "spd": "Maior diferença absoluta entre taxas de predição positiva dos grupos.",
            "eod": "Maior diferença absoluta entre taxas de verdadeiros positivos.",
            "aaod": "Maior média de diferenças absolutas de TPR/FPR entre pares de grupos.",
            "average_precision": "Área PR não interpolada por contribuição de recall.",
            "ece_10_bins": "Erro de calibração esperado em dez faixas iguais de probabilidade.",
        },
        "limites": [
            "Execução SOMENTE local: nunca publicar CSV de predições individuais nem saída administrativa sem revisão.",
            "Exige predições fora da amostra; não prova ausência de vazamento temporal ou de pacientes.",
            "Bootstrap IID não corrige dependência por paciente, unidade ou tempo.",
            "Diferenças entre grupos não estabelecem causalidade; reportar IC e população elegível.",
            "Exclusão de grupos com baixa amostra impede conclusão de equidade nesses grupos.",
        ],
    }
