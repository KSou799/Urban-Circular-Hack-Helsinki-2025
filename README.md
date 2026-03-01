# FlexiCity – Urban Energy Demand-Flexibility Simulator

> **Urban Circular Hack Helsinki 2025** — AI-driven simulation to reduce electricity demand spikes in Finland by analysing peak energy usage patterns and promoting off-peak device charging.

---

## Overview

FlexiCity is an interactive desktop simulator that models a city district's electrical demand over 24 hours. It visualises the impact of **demand-side flexibility (DSF)** — the idea that shifting flexible loads (EV chargers, heat pumps, HVAC, etc.) away from peak hours can flatten the grid demand curve, cut energy costs, and reduce carbon emissions.

The tool was built in a single hackathon sprint to serve as a **demo and decision-support tool** for city planners, energy operators, and building managers exploring demand-response programmes.

---

## Features

- **Three energy scenarios** – Baseline weekday, Winter weekday, and a 2030 future electrification scenario
- **24 pre-configured city assets** – EV fleets, tram depots, heat pumps, hospitals, schools, data centres, and more
- **Smart scheduler** – shifts flexible loads to low-price / low-load hours using a weighted scoring function
- **Flex participation slider** – simulate any adoption rate from 0 % (everyone naive) to 100 % (full DSF)
- **Grid vs price priority slider** – tune whether the scheduler optimises for grid stability or cost savings
- **Real-time charts** – four live canvas graphs: before, after, comparison overlay, and spot-price curve
- **Live KPIs** – peak demand reduction, energy cost saving in €, and daily/annual CO₂ saving in tCO₂
- **Four auto-optimisation modes**:
  - Minimum peak demand
  - Minimum CO₂ (plus balanced peak+CO₂ report)
  - Ideal balance across peak, cost, emissions, flex rate, and grid/price priority
  - Maximum peak reduction while guaranteeing both a cost saving and a CO₂ saving
- **Add / edit / toggle / delete assets** at runtime — no code changes needed
- **Variable vs fixed scheduling** – variable loads can be split across non-contiguous hours; fixed loads require a continuous block

---

## Screenshots

> *Run the app to see the live dashboard.*

---

## Getting Started

### Requirements

- Python 3.8 or later
- `tkinter` (included in the standard library on Windows and macOS; on Linux install `python3-tk`)

No external packages required.

### Installation

```bash
git clone https://github.com/KSou799/Urban-Circular-Hack-Helsinki-2025-Helsinki-Finland.git
cd Urban-Circular-Hack-Helsinki-2025-Helsinki-Finland
```

### Run

```bash
python flexicity.py
```

---

## How It Works

### Scheduling model

For each asset the simulator computes two schedules:

| Schedule | Logic |
|----------|-------|
| **BEFORE** | Naïve first-fit: run for the required duration at the earliest hours in the allowed window (full power). |
| **AFTER** | Smart: a fraction *p* (flex participation) of the load's power is moved to the best-scoring hours; (1−*p*) stays in the original naive hours. |

Hour scores are computed inside each asset's allowed time window:

```
score(h) = grid_weight × normalised_load(h)
         + price_weight × normalised_price(h)
```

A lower score means a better hour to run the load. Large assets are scheduled first so they shape the residual curve before smaller assets are placed.

### Scenarios

| Scenario | Grid | CO₂ | Asset scaling |
|----------|------|-----|---------------|
| **Baseline** | Typical weekday (morning + evening peaks) | Standard Finnish intensity profile | As configured |
| **Winter weekday** | Heavy heating in morning (05–09) and evening (16–22) | +25 % overall, +45 % at evening peak | Heat pumps ×1.8, EVs ×1.4, Saunas ×1.6, rest ×1.2 |
| **2030 future** | 90 % higher overall demand + massive EV evening wave | 35 % cleaner overall, 55 % cleaner at solar peak | EVs ×2.2, heat pumps & batteries ×1.9, rest ×1.4 |

### Data sources

- **Spot prices** – real hourly Finnish electricity spot prices (cents/kWh)
- **CO₂ intensity** – based on Finnish grid carbon intensity data (tCO₂/MWh), scaled for each scenario

---

## Project Structure

```
flexicity.py          # Single-file application (model + simulation + UI)
README.md
```

The code is organised into clear sections:

1. **Constants** – price and CO₂ arrays
2. **Load-profile generators** – baseline, winter, and 2030 profiles
3. **Asset definitions** – 24 district assets with their operating parameters
4. **Core simulation** – `recalculate_schedules()` computes BEFORE and AFTER curves
5. **Scenario management** – `apply_scenario()` switches profiles and rescales assets
6. **Optimisation routines** – four grid-search optimisers
7. **UI** – tkinter window, panels, sliders, listbox, and canvas graphs

---

## Using the App

1. **Select a scenario** from the dropdown at the top-left.
2. **Adjust the sliders**:
   - *Flex participation* — what fraction of assets participate in smart scheduling.
   - *Grid vs price priority* — whether the scheduler prioritises low-grid-load hours or low-price hours.
3. **Read the KPIs** in the "Peak, cost & CO₂" panel.
4. **Click an asset** in the list to see its before/after scheduled hours.
5. **Add or edit assets** using the form below the list.
6. **Use the auto-optimise buttons** to find the best slider settings automatically.

---

## Contributing

This project was built under hackathon time pressure. Contributions are welcome:

- Replacing the hard-coded load profiles with live Fingrid API data
- Adding matplotlib charts for richer visualisation
- Packaging as a standalone executable
- Adding a CSV export of results

Open an issue or submit a pull request!

---

## Team

Developed at **Urban Circular Hack Helsinki 2025**, Helsinki, Finland.

---

## License

MIT — free to use, modify, and distribute.
