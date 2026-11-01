# Predictive fairness protocol — tuberculosis loss to follow-up (research preview)

**Status:** protocol and *offline metrics audit* only. No trained model, no validated cohort, and no claims of official surveillance indicators. The SINAN MCP does not expose individual records through MCP. The existing seven-variable SQLite projection is **insufficient** for training an appropriate prediction model.

## Primary research question

For patients starting tuberculosis treatment, do models estimating loss to follow-up (LTFU) exhibit clinically consequential differences in discrimination, calibration and classification errors across sex and race/color groups and across pre-pandemic, pandemic and post-pandemic periods?

An audit cannot establish that race/sex *cause* unfairness. Labels and missing data may themselves reflect unequal access to care. Group labels must be used with appropriate community and institutional review.

## Study population and prediction moment

- Define the **diagnosis/treatment-entry cohort** from year-specific official SINAN-TB dictionaries and Ministry guidance; do not use `ano_do_arquivo` as diagnosis year.
- Candidate period: diagnosis years **2015–2023**, with **2024** only if outcome maturation and data version permit. This is a design proposal, not a validated endpoint.
- Establish eligibility, retreatment, transfer, duplicate notifications, changes in definitions and the unit of analysis **before** model fitting.
- Define time zero at treatment initiation (or an explicitly justified alternative). If the model is intended for prediction **at treatment initiation**, only use fields known by that instant. Avoid `SITUA_ENCE`, dates of closure and future treatment results in predictors.
- Labels require verification of `SITUA_ENCE` coding, transfers and outcome maturity. A recorded closure code of abandonment is not automatically the scientific definition of LTFU.
- Build an audit log of raw-source provenance, dictionary version, missingness, deduplication, cohort flow and outcome maturation. Keep patient-level extracts local under approved access control.

## Proposed temporal split (never randomize across time)

| Diagnosis year | Role |
|---|---|
| 2015–2018 | Development/training |
| 2019 | Hyperparameter tuning, selection and decision-threshold tuning |
| 2020–2021 | COVID-era temporal stress test |
| 2022–2023 | Final held-out temporal evaluation and fairness audit |
| 2024 | Optional later validation after checking outcome maturation |

Evaluate regional/domain shift, seasonality and changing case mix. If one patient contributes repeated episodes, protect against person-level train/test leakage and report how duplicated episodes were handled. Lock the exact split before examining final test outcomes.

## Models and metrics

Compare logistic regression, Random Forest, LightGBM and MLP **only after** valid predictors and patient-level eligibility are established. Include a transparent baseline, handle missingness within training folds only, tune all hyperparameters on training/validation partitions and set decision thresholds without looking at test outcomes.

For the overall population and each sufficiently supported subpopulation, report AUROC, average precision (AUPRC summary), calibration curve/Brier/ECE, prevalence, sensitivity, FPR, PPV and model uncertainty. Confidence intervals require resampling that respects clustering and temporal dependence where applicable.

- **SPD gap:** maximum difference in positive prediction rates across eligible groups. It is sensitive to underlying risk prevalence and is not sufficient alone.
- **EOD gap:** maximum difference in sensitivity/TPR across eligible groups.
- **AAOD gap:** maximum pairwise average of absolute TPR and FPR differences.
- Compare metrics before and after mitigation (e.g., reweighing, reductions and threshold adjustments) while reporting utility and calibration tradeoffs. A lower parity gap does not necessarily mean better care.

Always predeclare reference/group coding (including 9 = ignored race/color); explain which groups cannot be reliably evaluated. Report subgroup sizes locally for methodological review, not via public MCP. Avoid setting thresholds chosen separately on the final test cohorts.

## Offline audit CLI (no MCP endpoints)

Write a **private** CSV containing held-out model outputs with columns
`y_true,y_score,raca_cor` or `y_true,y_score,sexo`. Here, `y_true=1` means LTFU according to the *validated* cohort label and `y_score` is its predicted probability; scores must be within [0,1]. This CSV does not ship with the repository.

```powershell
py -3.11 -m sinan_mcp auditar-equidade .\predicoes_teste.csv --grupo raca_cor --coorte 2022-2023 --limiar 0.5 --bootstrap 200 --semente 42
py -3.11 -m sinan_mcp auditar-equidade .\predicoes_teste.csv --grupo sexo --coorte 2022-2023 --limiar 0.5
```

The command ignores all columns other than label, score and the permitted group and rejects invalid/missing labels, scores and group codes. By default, groups need at least 50 records and at least ten positive and ten negative outcomes. These are conservative **auditing thresholds**, not a valid sample-size or privacy proof.

Output is **local administrative data**, not a ChatGPT tool. The bootstrap currently treats rows as IID and should not be used to claim definitive inference when patients, facilities or timepoints are correlated. For a paper, implement cluster-aware resampling and confidence intervals in the restricted research pipeline.

## Governance and release checklist

Do not enable the real-data MCP gate until the data steward approves the exposure, user roles are defined, the operational deployment is reviewed, and an independent privacy assessment addresses cross-query and auxiliary-data attacks. The secure tunnel authenticates transport, **not** epidemiologic or statistical disclosure safety.

Research outputs require versioned code, fixed random seeds, cohort extraction checks, preserved training/test split manifests, data-dictionary citations, and appropriate scientific review before publication.

## Reference starting points

- [Brazilian Ministry of Health — Tuberculosis](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/t/tuberculose)
- [SINAN — Tuberculosis](https://portalsinan.saude.gov.br/tuberculose)
- [WHO Tuberculosis](https://www.who.int/teams/global-tuberculosis-programme)
- [Fairlearn — assessment](https://fairlearn.org/main/user_guide/assessment/index.html)
