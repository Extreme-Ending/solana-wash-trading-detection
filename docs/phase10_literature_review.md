# Phase 10 literature review

## Scope

This review supports the implemented question: reproducible, point-in-time, unsupervised wallet anomaly analysis over a provenance-limited Solana DEX sample. It does not use the literature to infer labels, transplant reported performance, or claim that anomalous wallets are fraudulent.

## Anomaly detection without verified outcomes

Anomaly detection identifies observations that depart from an assumed pattern of normality, but each method embeds different assumptions about what departure means (Chandola et al., 2009). Pimentel et al. (2014) distinguish novelty/one-class settings from ordinary supervised classification and emphasise that limited abnormal examples motivate modelling of a reference distribution. This supports the project's label-free framing, but the current reference cohort is not known to be anomaly-free. The output is therefore a relative score, not a learned normal-versus-fraud boundary.

Evaluation is especially difficult without trusted labels. Campos et al. (2016) show that results depend on datasets, parameter choices and evaluation construction; Goldstein and Uchida (2016) likewise find material differences between global and local detector behaviour. These findings motivate this project's use of multiple detectors, parameter sensitivity, rank agreement and top-budget overlap. They do not make agreement a substitute for correctness. With no ground truth, outcome accuracy remains unknowable.

## Isolation Forest, LOF and robust statistical comparison

Isolation Forest isolates observations through random partitioning rather than directly estimating a density (Liu et al., 2008). Its scalability and ability to produce a continuous ranking make it suitable for the 29-feature wallet snapshots. The implementation nevertheless treats its score as model-specific and unitless; the original paper's benchmark results are not transferred to this dataset.

LOF defines local unusualness relative to neighbourhood density (Breunig et al., 2000). It offers a contrasting local perspective to Isolation Forest's more global isolation mechanism. The weak holdout agreement observed in this project is therefore evidence of detector dependence, not proof that either method is right or wrong.

Median-based robust scale estimates resist extreme values and provide a transparent statistical baseline. Rousseeuw and Croux (1993) describe the robustness properties and limitations of median absolute deviation and alternative scale estimates. The project's robust MAD comparator is useful for checking whether multivariate model rankings align with large marginal deviations; it is not a fraud rule and does not capture relational coordination.

## Financial and blockchain transaction analysis

Financial anomaly detection literature spans statistical, machine-learning and hybrid methods, while repeatedly highlighting scarce labels, class imbalance, changing behaviour and the need for domain-specific validation (Hilal et al., 2022). A financial anomaly may result from legitimate operational or strategic behaviour. Human investigation and calibrated claim boundaries are therefore more defensible than automated accusation in this unlabelled study.

Victor and Weintraud (2021) analyse wash trading on Ethereum limit-order-book DEXs using observable account/trading structures, including self-trades and multi-account patterns. Their work demonstrates why transaction-domain semantics and relational evidence matter. The current Solana table supplies one focal wallet per swap but no independently established counterparty relationship, ownership link or complete order-book trade pair. Their wash-trading criteria cannot be reproduced from the current schema.

Address clustering itself relies on explicit heuristics and transaction evidence that must be validated for the relevant chain and purpose (Victor, 2020). Shared tokens, a shared transaction signature or co-occurrence are insufficient to assert common control. This supports the project's decision to disable graph and collusion features rather than manufacture edges.

## Temporal shift and validation

Gama et al. (2014) show that changing data-generating processes complicate model evaluation and adaptation. Although their survey is centred on evolving supervised systems, the broader lesson applies here: later-wallet feature distributions and observable history can differ from the training reference. The project therefore reports chronological cohorts, feature shift, later entrants and repeated-wallet longitudinal behaviour instead of using a random row split.

The term “concept drift” should be used cautiously because there is no verified target relationship in this study. The evidence directly establishes covariate/coverage shift in observed features and model scores, not drift in a fraud concept.

## Reproducibility and responsible interpretation

Pineau et al. (2021) frame reproducibility as a prerequisite for reliable machine-learning evidence and emphasise code, data and reporting practices. This project implements deterministic scripts, fixed seeds, versioned schemas, dependency metadata and content fingerprints. Those controls establish computational reproducibility in the pinned local environment; they cannot repair missing data-acquisition rights.

Rudin (2019) argues for interpretable approaches in high-stakes settings rather than relying uncritically on post-hoc explanations of opaque systems. The current dashboard therefore reports actual features against training-reference medians/IQRs and labels them as descriptive context, not causal attribution or SHAP explanation. No adverse decision should be made from the anomaly ranking.

## Lecturer-lab alignment, kept separate

The lecturer's [`AML_Book-Data`](https://github.com/NUELBUNDI/AML_Book-Data) repository is a course reference, not peer-reviewed literature. Its `notebook/lab2_solution.ipynb` audit, cleaning, feature-lineage and scoring-time patterns are adapted in the implementation. The project replaces the lab's supervised metric path with label-free diagnostics because copying target-dependent evaluation would be scientifically invalid.

## Synthesis

The literature supports a cautious comparative anomaly study when outcomes are missing, but it does not validate the current detector as a wash-trading system. The academically supportable contribution is the integration of strict point-in-time wallet features, contrasting global/local/robust rankings, temporal and coverage diagnostics, reproducibility evidence and a fail-closed review interface. Independent labels, direct relational evidence and lawful data provenance remain necessary for stronger claims.

## References

Breunig, M. M., Kriegel, H.-P., Ng, R. T., & Sander, J. (2000). LOF: Identifying density-based local outliers. In *Proceedings of the 2000 ACM SIGMOD International Conference on Management of Data* (pp. 93–104). Association for Computing Machinery. https://doi.org/10.1145/342009.335388

Campos, G. O., Zimek, A., Sander, J., Campello, R. J. G. B., Micenková, B., Schubert, E., Assent, I., & Houle, M. E. (2016). On the evaluation of unsupervised outlier detection: Measures, datasets, and an empirical study. *Data Mining and Knowledge Discovery, 30*(4), 891–927. https://doi.org/10.1007/s10618-015-0444-8

Chandola, V., Banerjee, A., & Kumar, V. (2009). Anomaly detection: A survey. *ACM Computing Surveys, 41*(3), Article 15. https://doi.org/10.1145/1541880.1541882

Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M., & Bouchachia, A. (2014). A survey on concept drift adaptation. *ACM Computing Surveys, 46*(4), Article 44. https://doi.org/10.1145/2523813

Goldstein, M., & Uchida, S. (2016). A comparative evaluation of unsupervised anomaly detection algorithms for multivariate data. *PLOS ONE, 11*(4), e0152173. https://doi.org/10.1371/journal.pone.0152173

Hilal, W., Gadsden, S. A., & Yawney, J. (2022). Financial fraud: A review of anomaly detection techniques and recent advances. *Expert Systems with Applications, 193*, 116429. https://doi.org/10.1016/j.eswa.2021.116429

Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation forest. In *2008 Eighth IEEE International Conference on Data Mining* (pp. 413–422). IEEE. https://doi.org/10.1109/ICDM.2008.17

Pimentel, M. A. F., Clifton, D. A., Clifton, L., & Tarassenko, L. (2014). A review of novelty detection. *Signal Processing, 99*, 215–249. https://doi.org/10.1016/j.sigpro.2013.12.026

Pineau, J., Vincent-Lamarre, P., Sinha, K., Larivière, V., Beygelzimer, A., d'Alché-Buc, F., Fox, E., & Larochelle, H. (2021). Improving reproducibility in machine learning research: A report from the NeurIPS 2019 reproducibility program. *Journal of Machine Learning Research, 22*(164), 1–20. https://www.jmlr.org/papers/v22/20-303.html

Rousseeuw, P. J., & Croux, C. (1993). Alternatives to the median absolute deviation. *Journal of the American Statistical Association, 88*(424), 1273–1283. https://doi.org/10.1080/01621459.1993.10476408

Rudin, C. (2019). Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead. *Nature Machine Intelligence, 1*, 206–215. https://doi.org/10.1038/s42256-019-0048-x

Victor, F. (2020). Address clustering heuristics for Ethereum. In J. Bonneau & N. Heninger (Eds.), *Financial cryptography and data security* (Lecture Notes in Computer Science, Vol. 12059, pp. 617–633). Springer. https://doi.org/10.1007/978-3-030-51280-4_33

Victor, F., & Weintraud, A. M. (2021). Detecting and quantifying wash trading on decentralized cryptocurrency exchanges. In *Proceedings of the Web Conference 2021* (pp. 23–32). Association for Computing Machinery. https://doi.org/10.1145/3442381.3449824
