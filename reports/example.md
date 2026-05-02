# Research Report

## Verdict

inconclusive

## Power Boundary

- This report can falsify pre-registered claims, compare local evidence, and expose fragility.
- This report cannot trade, advise, fetch live data, connect brokers, or watch markets.
- This offline research lab helps focus symbols, register hypotheses, run local falsification, and review evidence.
- No live market data is requested or implied; use local CSVs and generated artifacts only.
- No broker or execution actions are available from this terminal layer.
- Type '?' for catalog help, use command aliases, or enter an uppercase ticker-like token such as MSFT.

## Hypothesis

- ID: toy-moving-average-crossover
- Thesis: A toy moving-average crossover may outperform a buy-and-hold baseline on the bundled offline sample.
- Null hypothesis: The toy moving-average crossover has no edge after costs, slippage, and one-bar execution delay.
- Asset universe: AAA, BBB
- Time horizon: daily bars over a tiny educational sample
- Signal definition: Long when the 2-bar moving average is above the 3-bar moving average; flat otherwise.
- Expected failure modes: lookahead leakage, cost sensitivity, failure to beat buy-and-hold baseline, non-reproducible run outputs
- Falsification tests: lookahead column scan, explicit cost realism check, baseline comparison, higher-cost stress run, deterministic rerun fingerprint check
- Pre-registered metrics: strategy_cumulative_return, baseline_cumulative_return, max_drawdown, turnover, total_cost
- Thresholds: {'baseline_comparison': 'strategy_cumulative_return > baseline', 'cost_sensitivity': 'stressed return remains positive', 'reproducibility': 'rerun fingerprints match'}
- Data requirements: local CSV only, date, symbol, OHLCV columns, rows sorted by date then symbol
- Posthoc edit policy: Do not change the hypothesis or thresholds after observing results.

## Dataset

- Source: /Users/clay/Documents/New project 4/examples/toy_prices.csv
- Symbols: AAA, BBB
- Date range: 2024-01-02 to 2024-01-09
- Columns: date, symbol, open, high, low, close, volume
- Content hash: 52635e40771bdd93cb3df91e76808bcdf5cbb67446bebb28c136611068e3ea06
- Warnings: None listed

## Backtest Metrics

- average_exposure: 0.75
- bars: 8
- baseline_cumulative_return: 0.0419350221840562
- max_drawdown: 0.0
- strategy_cumulative_return: 0.03883048242570175
- symbols: ['AAA', 'BBB']
- total_cost: 0.003
- turnover: 0.375
- Fingerprint: 24803bcd372677658d5df1678d8d449753157932c9ec4c8a425a767276dfe0ac
- Trades: 2
- Result warnings: None listed
- Spec: short_window=2, long_window=3, transaction_cost_bps=10, slippage_bps=5, execution_delay_bars=1

## Falsification Gates

### schema columns

- Status: pass
- Severity: info
- Threshold: all required OHLCV columns are present
- Evidence: {'required_columns': ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume'], 'observed_columns': ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume'], 'missing_columns': []}
- Remediation: No evidence gap recorded.

### chronology

- Status: pass
- Severity: info
- Threshold: rows are sorted and unique by date and symbol
- Evidence: {'rows_checked': 12}
- Remediation: No evidence gap recorded.

### lookahead columns

- Status: pass
- Severity: info
- Threshold: no lowercase column name contains future, target, or forward
- Evidence: {'checked_columns': ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']}
- Remediation: No evidence gap recorded.

### cost realism

- Status: pass
- Severity: info
- Threshold: transaction_cost_bps + slippage_bps > 0 and total_cost present
- Evidence: {'transaction_cost_bps': 10, 'slippage_bps': 5, 'total_cost': 0.003}
- Remediation: No evidence gap recorded.

### baseline comparison

- Status: warn
- Severity: warning
- Threshold: strategy_cumulative_return > baseline_cumulative_return
- Evidence: {'strategy_cumulative_return': 0.03883048242570175, 'baseline_cumulative_return': 0.0419350221840562}
- Remediation: Comparator evidence weakened the claim.

### cost sensitivity

- Status: pass
- Severity: info
- Threshold: stressed strategy_cumulative_return > 0 and deterioration <= 50%
- Evidence: {'original_strategy_cumulative_return': 0.03883048242570175, 'stressed_strategy_cumulative_return': 0.03263529898534534, 'deterioration': 0.006195183440356411}
- Remediation: No evidence gap recorded.

### reproducibility

- Status: pass
- Severity: info
- Threshold: backtest fingerprints match
- Evidence: {'first_fingerprint': '24803bcd372677658d5df1678d8d449753157932c9ec4c8a425a767276dfe0ac', 'second_fingerprint': '24803bcd372677658d5df1678d8d449753157932c9ec4c8a425a767276dfe0ac'}
- Remediation: No evidence gap recorded.

### walk-forward robustness

- Status: warn
- Severity: warning
- Threshold: majority of folds beat the comparator on the same offline bars
- Evidence: {'folds': 3, 'passing_folds': 0, 'pass_ratio': 0.0, 'median_strategy_cumulative_return': 0.011473334169453508, 'median_baseline_cumulative_return': 0.01449275362318847, 'worst_fold_strategy_cumulative_return': 0.009220959746672364, 'fold_metrics': [{'fold': 1, 'train_start': '2024-01-02', 'train_end': '2024-01-04', 'test_start': '2024-01-05', 'test_end': '2024-01-05', 'strategy_cumulative_return': 0.009220959746672364, 'baseline_cumulative_return': 0.012237011592958424}, {'fold': 2, 'train_start': '2024-01-03', 'train_end': '2024-01-05', 'test_start': '2024-01-08', 'test_end': '2024-01-08', 'strategy_cumulative_return': 0.0116145158183103, 'baseline_cumulative_return': 0.014634146341463428}, {'fold': 3, 'train_start': '2024-01-04', 'train_end': '2024-01-08', 'test_start': '2024-01-09', 'test_end': '2024-01-09', 'strategy_cumulative_return': 0.011473334169453508, 'baseline_cumulative_return': 0.01449275362318847}]}
- Remediation: Record more fold evidence or mark the claim as fold-fragile.

### parameter sensitivity

- Status: pass
- Severity: info
- Threshold: nearby parameter cells show broad non-negative evidence
- Evidence: {'cells': [{'short_window': 1, 'long_window': 3, 'strategy_cumulative_return': 0.03883048242570175}, {'short_window': 1, 'long_window': 4, 'strategy_cumulative_return': 0.026275595757706105}, {'short_window': 1, 'long_window': 5, 'strategy_cumulative_return': 0.011473334169453508}, {'short_window': 2, 'long_window': 3, 'strategy_cumulative_return': 0.03883048242570175}, {'short_window': 2, 'long_window': 4, 'strategy_cumulative_return': 0.026275595757706105}, {'short_window': 2, 'long_window': 5, 'strategy_cumulative_return': 0.011473334169453508}, {'short_window': 3, 'long_window': 4, 'strategy_cumulative_return': 0.026275595757706105}, {'short_window': 3, 'long_window': 5, 'strategy_cumulative_return': 0.011473334169453508}], 'selected_strategy_cumulative_return': 0.03883048242570175, 'positive_cells': 8, 'positive_ratio': 1.0, 'median_strategy_cumulative_return': 0.026275595757706105, 'selected_is_isolated_peak': False}
- Remediation: No evidence gap recorded.

### cost grid robustness

- Status: pass
- Severity: info
- Threshold: returns remain positive across at least half of cost grid cells
- Evidence: {'cells': [{'transaction_cost_bps': 0, 'slippage_bps': 0, 'execution_delay_bars': 1, 'strategy_cumulative_return': 0.0419350221840562}, {'transaction_cost_bps': 10, 'slippage_bps': 5, 'execution_delay_bars': 1, 'strategy_cumulative_return': 0.03883048242570175}, {'transaction_cost_bps': 30, 'slippage_bps': 15, 'execution_delay_bars': 1, 'strategy_cumulative_return': 0.03263529898534534}, {'transaction_cost_bps': 30, 'slippage_bps': 15, 'execution_delay_bars': 2, 'strategy_cumulative_return': 0.020162504841163775}], 'surviving_cells': 4, 'survival_ratio': 1.0, 'worst_strategy_cumulative_return': 0.020162504841163775, 'highest_cost_strategy_cumulative_return': 0.020162504841163775}
- Remediation: No evidence gap recorded.

## Evidence Coverage

- schema columns: recorded / pass - This control recorded passing evidence.
- chronology: recorded / pass - This control recorded passing evidence.
- lookahead columns: recorded / pass - This control recorded passing evidence.
- baseline comparison: recorded / warn - This control recorded warning evidence that needs harder review.
- cost realism: recorded / pass - This control recorded passing evidence.
- cost sensitivity: recorded / pass - This control recorded passing evidence.
- reproducibility: recorded / pass - This control recorded passing evidence.
- walk-forward robustness: recorded / warn - This control recorded warning evidence that needs harder review.
- parameter sensitivity: recorded / pass - This control recorded passing evidence.
- cost grid robustness: recorded / pass - This control recorded passing evidence.

## Research Action Queue

- Retest warning evidence against a stricter comparator or robustness control.
- Run next offline test: Record additional offline walk-forward folds.
- Run next offline test: Record wider parameter and cost grids.
## Limitations

- Offline local CSV only; no live data, broker APIs, or order routes were used.
- Toy research configuration; robustness gates record evidence gaps.

## Next Tests

- Record additional offline walk-forward folds.
- Record wider parameter and cost grids.
- Record stronger comparator families before interpreting the claim.

## Safety Note

This is not investment advice. No live trading, live data, broker connection, credentials, order routing, or execution action was performed.
