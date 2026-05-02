# Agentic Disproof Loop Ledger

This lab optimizes for disproving trading ideas before they can become
stories. The loop below is durable project memory for future agent passes.

1. Pre-register the claim.
2. State the null hypothesis.
3. Define the comparator before running.
4. Define the cost model before running.
5. Define the execution delay before running.
6. Hash the dataset.
7. Validate schema.
8. Validate chronology.
9. Scan for lookahead columns.
10. Treat unknown feature lineage as a failure.
11. Run the baseline.
12. Run the strategy on the same bars as the baseline.
13. Compute the delta against the comparator.
14. Record total costs.
15. Stress transaction costs.
16. Stress slippage.
17. Stress execution delay.
18. Rerun for reproducibility.
19. Compare fingerprints.
20. Flag missing metrics as critical evidence gaps.
21. Sort failures before passes.
22. Put evidence against the claim above raw returns.
23. Use warnings to design the next test.
24. Do not edit thresholds after seeing results.
25. Avoid real tickers in examples.
26. Keep every artifact offline.
27. Keep broker, credential, order, and live-data surfaces out of scope.
28. Never present a result as accepted or validated.
29. Treat non-rejected as not disproved yet.
30. Prefer stronger baselines over more complex signals.
31. Prefer holdout tests over in-sample fit.
32. Prefer walk-forward folds over single-period stories.
33. Prefer parameter sensitivity over best-parameter selection.
34. Prefer cost grids over one cost assumption.
35. Prefer dataset manifests over implicit data memory.
36. Prefer JSON evidence over Markdown-only reports.
37. Prefer dashboards that compare disproof pressure.
38. Track limitations visibly.
39. Track what would change our mind.
40. Track reruns and trial counts.
41. Warn on p-hacking risk.
42. Warn on tiny samples.
43. Warn on isolated parameter peaks.
44. Warn on survivorship assumptions.
45. Warn when universe selection is posthoc.
46. Warn when baselines use different data spans.
47. Warn when returns survive only under cheap costs.
48. Let subagents attack assumptions from independent angles.
49. Commit durable checkpoints before expanding scope.
50. Optimize for truth pressure, not persuasive reports.

## Runner Robustness Loop

1. Registry evidence is the source of the claim.
2. Runner output is the source of the artifact.
3. Markdown and HTML are views over JSON evidence.
4. Dataset paths remain local and explicit.
5. Unsupported execution surfaces fail closed.
6. Missing comparator metrics fail closed.
7. Missing fold metrics fail closed.
8. Missing parameter-grid metrics fail closed.
9. Missing cost-grid metrics fail closed.
10. Walk-forward evidence records fold counts.
11. Walk-forward evidence records comparator results per fold.
12. Fold fragility is a warning, not a story.
13. Parameter grids record neighborhoods, not preferred parameters.
14. Isolated peaks become fragility evidence.
15. Cost grids record several assumptions, not one stress point.
16. Cheap-cost survival does not imply robustness.
17. Reproducibility stays visible through fingerprints.
18. Dataset hash agreement stays visible.
19. The dashboard prioritizes evidence presence over returns.
20. Runner Evidence sorts by disproof score.
21. Return deltas are context, not rankings.
22. Evidence Docket appears before performance tables.
23. Open Evidence Gaps are labeled as records, not commands.
24. Safety copy avoids trade guidance.
25. No broker, credential, order, or live-data terms belong in registry payloads.
26. Toy symbols remain the default examples.
27. Registry fields preserve pre-registration discipline.
28. Runner configs avoid best-parameter selection.
29. Robustness gates can warn without claiming proof.
30. Passing a gate means only that this evidence gap was not recorded.
31. The artifact keeps limitations next to results.
32. The artifact keeps follow-up tests separate from execution.
33. The CLI prints verdicts and file paths, not trade summaries.
34. Dashboards should be static and local by default.
35. Every new gate needs missing-evidence tests.
36. Every new UI section needs safety-language tests.
37. Every runner path should be deterministic for the same inputs.
38. Every generated artifact should be rerenderable from JSON.
39. Every milestone should regenerate reports before review.
40. The lab improves by preserving failed assumptions.
