# FlexiCity – Helsinki Energy Peak Simulator

> Shift flexible electricity loads to flatten Helsinki's evening demand spike — and see the grid, cost, and CO₂ impact in real time.

![FlexiCity Screenshot](screenshot.png)

---

## The Problem

Every evening around 19:00, Helsinki's electricity price nearly **triples**:

| Hour | Price (c/kWh) | What's happening |
|------|--------------|-----------------|
| 02:00 | 8.52 | City asleep |
| 17:00 | 18.60 | Commuters arriving home |
| 18:00 | 21.53 | EVs plugging in, ovens on |
| **19:00** | **22.68** | **Daily peak** |
| 21:00 | 17.09 | Load easing |

This isn't just expensive — it's a growing infrastructure problem. EV adoption and electrified heating mean demand peaks are intensifying. One study projects peak power demand in the greater Helsinki region could rise **179% between 2020 and 2030**. FlexiCity simulates what happens when flexible loads get smarter about *when* they run.

---

## Quick Start

**Requirements:** Python 3.8+. No pip installs — uses only the standard library.

```bash
git clone https://github.com/KSou799/Urban-Circular-Hack-Helsinki-2025-Helsinki-Finland.git
cd Urban-Circular-Hack-Helsinki-2025-Helsinki-Finland
python flexicity.py
```

> On some Linux systems, install tkinter separately: `sudo apt install python3-tk`

---

## What You Can Simulate

**3 grid scenarios**

| Scenario | Description |
|----------|-------------|
| Baseline | Typical Helsinki weekday |
| Winter weekday | Strong heating spikes 05–09h and 16–22h; heat pumps ×1.8, EVs ×1.4 |
| 2030 future | +90% overall load, large EV wave 16–21h, -55% midday CO₂ from solar |

**24 flexible load types** — city EV fleet, tram depot, hospitals, schools, data centres, residential EVs, saunas, and more. Add, edit, toggle, or delete any load at runtime.

**4 optimisation modes**

| Mode | Objective |
|------|-----------|
| Min peak | Flatten the demand curve |
| Min CO₂ | Shift load to cleaner hours |
| Balanced | Weighted combination of peak, CO₂, and cost |
| Max reduction | Maximise peak reduction while keeping cost and CO₂ gains positive |

**Two key sliders**
- **Grid/Price** — shift optimisation priority between grid stability and cost saving
- **Flex participation** — simulate partial adoption (e.g. only 40% of loads join)

**Live stats panel** — peak before/after, EUR/day saved, tCO₂/day and /year avoided

---

## How the Scheduler Works

**Baseline (naïve):** Each load starts at the earliest available hour in its time window and runs at full power for its full duration.

**Smart scheduling:** For each participating load, the algorithm:
1. Removes the load's contribution from its naïve hours
2. Scores every hour in its allowed window using a weighted combination of grid load (lower is better) and spot price (lower is better)
3. Places variable loads in the individually cheapest or cleanest hours
4. Places fixed-block loads (e.g. laundry cycles) in the cheapest or cleanest *continuous* block

The Grid/Price slider controls the weighting. The Flex participation slider scales how much of each load actually shifts.

---

## Data Sources and Limitations

| Data | Source | Limitation |
|------|--------|------------|
| Electricity prices | Helen hourly day-ahead data | Single representative day; live deployment needs Nord Pool API |
| CO₂ intensity | Synthetic Finnish grid profile | Live data available via Fingrid open API |
| Demand units | Relative index (kW loads on MW-scale base) | Not calibrated to absolute Finnish grid figures |

---

## Context

Built in 24 hours at **Urban Circular Hack Helsinki 2025**, a hackathon focused on circular economy solutions for cities.

Finland's energy context makes demand-response particularly relevant: high electrification rates, growing variable renewables, district heating transitioning to heat pumps, and rapid EV uptake combine to produce increasingly volatile demand profiles. Shifting even a modest fraction of flexible loads reduces peak infrastructure requirements and captures value from cleaner overnight and midday generation.

---

## License

MIT
