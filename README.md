# GTA VI Twitch Concurrent Viewers Forecaster

[![Status](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01)
[![Rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/stevewhy404/gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01)
[![Reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/stevewhy404/gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01)

An empirical release-day shape forecaster for the Grand Theft Auto VI Twitch viewership category (`gta6-twitch-ccu-forecast-01` bounty on [make.fun](https://make.fun/bounty/gta6-twitch-ccu-forecast-01)).

## Approach

- **Log-Scale Modeling**: Operates in log space to forecast hourly ratios relative to hour 1 ($\ln(y_h / p_1)$).
- **Comparable Learning**: Extracts release-day hourly trajectories from 37 past major game launches in the case data to learn the median empirical shape of release-day viewership curves.
- **Robust Spread Estimation**: Computes robust dispersion (mean absolute deviation) around the median shape to calibrate quantile spreads ($\tau \in [0.05, 0.25, 0.5, 0.75, 0.95]$) rather than relying on a naive random walk.
- **Constraints & Determinism**: Enforces non-decreasing quantiles, positive viewer counts, and strict determinism under Python 3.13 standard library.
