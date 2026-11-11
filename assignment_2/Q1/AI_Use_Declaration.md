# AI Tool Use Declaration - AI4015 Assignment Beta, Q1 (Roll no. 23K-0001)

## What Claude did

| Purpose | What Claude did |
|---|---|
| Section 1 research | Ran web searches and collected prices, context windows, licences, benchmarks and rate limits for 12 models, with source URLs. Cells that could not be confirmed are marked NV (not verified). |
| Code | Wrote measure_tool_latency.py (timing script). |

## What I did myself (with help from Claude)

- I derived R, D, Q, N, p, H, B, T from my roll number.

- I completed the Section 2 calculations (token volume, API cost with/without caching, peak load, KV-cache memory, GPU sizing, break-even, latency model) and the cost plot, with help from Claude.

- I wrote the report text and tables, with help from Claude, and updated them with my measured timing data and config.json screenshot.

- I ran measure_tool_latency.py on my machine on 8 and 9 November 2026 (UTC dates in the log): 50 OpenAQ, 100 Open-Meteo, 50 heat-index and 50 knowledge-base timings. The raw log is submitted as timing_log.csv.

- I took the config.json screenshot from the Hugging Face model page of Mistral-Small-3.2-24B-Instruct-2506 (included in the report as Figure 2 and submitted as config_screenshot.PNG).

## Known limitations (disclosed)

- Cells marked NV in the Section 1 table are unverified.
- Assumed values, listed on the Assumptions sheet: Claude Haiku 5.5 TTFT (0.6 s), prefill speed (20,000 tok/s), minimum cacheable prefixes for some providers, and the cache-write convention.
- Some tool-use benchmark figures (gpt-oss tau-bench) were recalled from the model card and not re-verified.