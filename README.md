# FlexiCity — Demand-Response Simulator for Urban Energy Districts

Built at **Urban Circular Hack Helsinki 2025** · Python · Tkinter · No external dependencies

FlexiCity is an interactive desktop simulation that models what happens when a city district shifts flexible electricity loads from peak hours to off-peak hours — and quantifies the resulting reduction in grid stress, energy costs, and CO2 emissions.

It simulates 24 real-world urban loads (EV fleets, heat pumps, HVAC, tram depots, hospitals, data centres) scheduled against actual Finnish day-ahead electricity prices and hourly CO2 intensity data.

---

## Problem

Finland's electricity grid faces sharp demand spikes in the morning (07–09h) and evening (17–22h). Most of the loads driving those spikes — EV chargers, heat pumps, HVAC pre-cooling, industrial refrigeration — are temporally flexible. They need to run for a fixed number of hours but do not need to run at any specific hour.

If a fraction of those loads shift by a few hours, the peak drops, grid infrastructure costs fall, and because the grid is cleaner at night and midday, CO2 emissions fall too. FlexiCity lets you explore exactly how much, and under what conditions.

---

## Features

| Feature | Description |
|---|---|
| 3 scenarios | Baseline, Winter weekday (stronger heating demand), 2030 future (2x EV penetration) |
| 24 flexible loads | City EV fleet, tram depot, hospitals, schools, data centres, residential EVs, and more |
| Before/After charts | Side-by-side 24h demand curves showing naive vs. smart scheduling |
| Real price data | Finnish day-ahead market prices (cents/kWh, hourly, 00–23h) |
| Real CO2 data | Hourly grid carbon intensity (tCO2/MWh), varying by renewable generation |
| Grid vs. Price slider | Shift optimisation priority between flattening the grid and minimising cost |
| Flex participation slider | Simulate partial adoption — what if only 40% of loads participate? |
| 4 optimisation modes | Min peak, Min CO2, Balanced (peak + CO2 + cost), Max peak reduction with positive cost and CO2 gains |
| Live stats panel | Peak before/after, cost saving (EUR/day), CO2 saving (tCO2/day and /year) |
| Editable load list | Add, edit, toggle, or delete any load at runtime |

---

## Quick Start

Requirements: Python 3.8 or higher. Tkinter is included in the Python standard library — no pip installs needed.

```bash
git clone https://github.com/KSou799/Urban-Circular-Hack-Helsinki-2025-Helsinki-Finland.git
cd Urban-Circular-Hack-Helsinki-2025-Helsinki-Finland
python flexicity.py
```

On some Linux distributions tkinter is a separate package:

```bash
sudo apt install python3-tk
```

---

## How the Scheduler Works

**Before (baseline):** Every load is scheduled naively. It starts at the first available hour in its allowed time window and runs for its full duration at full power.

**After (smart scheduling):** For each participating load, the algorithm:

1. Removes the load's power contribution from its naive hours
2. Scores every hour in its allowed window using a weighted combination of grid load at that hour (lower is better) and electricity price at that hour (lower is better)
3. Places variable loads in the individually cheapest or cleanest hours
4. Places fixed-block loads (laundry cycles, defrost cycles) in the cheapest or cleanest continuous block

The Grid/Price slider controls the weighting between the two signals. The Flex participation slider scales how much of each load shifts, simulating partial or phased adoption.

---
## Screenshot

![FlexiCity Screenshot](screenshot.png)

*Top graph:* peak demand  
*Bottom graph:* demand flattened via smart scheduling  

---

## Scenarios

| Scenario | Base Load | CO2 Profile | Notable Changes |
|---|---|---|---|
| Baseline | Typical weekday | Finnish average | Reference case |
| Winter weekday | Strong heating spikes at 05–09h and 16–22h | +25–45% evening intensity | Heat pumps x1.8, EVs x1.4, saunas x1.6 |
| 2030 future | +90% overall, large EV wave 16–21h | -35% average, -55% midday (solar) | EVs x2.2, batteries x1.9, general x1.4 |

---

## Repository Structure

```
flexicity.py      # Single-file application — model, scheduler, and UI
README.md
```

---

## Design Decisions and Limitations

- **Units:** Loads are in kW. The base grid load is in MW-scale arbitrary units. The combined demand curve is a relative index suitable for comparison, not an absolute MW figure calibrated to the real Finnish grid.
- **Scheduler:** The optimiser is a greedy weighted heuristic, not a trained model. It is fast, transparent, and sufficient for interactive simulation but does not guarantee a global optimum.
- **Price data:** A single representative day of Finnish day-ahead prices. Live deployment would require Nord Pool API integration.
- **CO2 data:** Synthetic profile based on typical Finnish grid intensity patterns. Live data would come from Fingrid's open API.
- **Inter-asset coordination:** Each load is optimised sequentially, largest first. A production district energy management system would co-optimise all loads simultaneously.

---

## Context

Built in 24 hours at **Urban Circular Hack Helsinki 2025**, a hackathon focused on circular economy solutions for cities.

The Finnish energy context makes demand-response particularly relevant. High electrification rates, a large share of variable renewables, district heating transitioning to heat pumps, and rapid EV adoption combine to create increasingly volatile demand profiles. Shifting even a modest fraction of flexible loads reduces peak infrastructure requirements and unlocks value from cleaner overnight and midday generation.

---

## License

MIT


