# FlexiCity

**Smart electricity load-shifting simulator — shaves a Nordic city's evening peak by 9.6 %, cuts daily flex-asset electricity cost by 10.5 %, and avoids ~7.3 tonnes of CO₂ per year, with zero behaviour change from end users.**

`Energy systems` · `Peak load management` · `HVAC & heat pumps` · `Demand-side flexibility` · `Numerical simulation` · `Multi-objective optimisation` · `Python`

![FlexiCity dashboard showing before/after load curves, comparison and price graphs, and peak/cost/CO₂ stats](screenshots/01-overview.png)

A 24-hour interactive simulator built in two days for **Urban Circular Hack Helsinki 2025** (U!REKA European University hackathon).
Challenge: *How might we prepare cities for the increasing demand in electricity?*

---

## Headline results

> **−9.6 %** peak demand &nbsp;·&nbsp; **−10.5 %** daily cost &nbsp;·&nbsp; **~7.3 tCO₂/year** avoided

| | Before | After | Saving |
|---|---|---|---|
| Peak demand | 306.0 kW | 276.5 kW | **−29.5 kW (−9.6 %)** |
| Daily cost (flex assets) | €432.57 | €387.21 | **−€45.36 (−10.5 %)** |
| CO₂ emissions | — | — | **−20 kg/day · ~7.3 tCO₂/year** |

![Peak, cost and CO₂ stats panel](screenshots/02-stats.png)

*At balanced default settings — 100 % flex participation, 50/50 grid-vs-price priority. The four built-in optimisers push every metric further.*

---

## My contributions

I led the engineering side of this project — the algorithm, the city model, and the data.

- **Scheduling algorithm.** Designed the BEFORE / AFTER comparison model and implemented the smart scheduler. Key engineering choices: process assets **largest-first** so big loads claim the least-stressed hours, **re-score the after-curve after each placement** so smaller loads don't pile on top, and **separate *variable* loads** (can split across non-contiguous hours) from ***fixed* loads** (must run as one contiguous block).
- **Multi-objective optimisation.** Built four optimisers (peak · cost · CO₂ · combined) on top of an exhaustive 1 % × 1 % grid search across (flex %, priority %) — **10,201 schedules per run**. Added a **no-regression guardrail**: any schedule where *any* metric loses against the naive baseline is rejected, so the "everyone wins" framing stays honest.
- **City model.** Parameterised 24 heterogeneous flexible loads — EV fleets, heat pumps, HVAC pre-cooling, supermarket refrigeration, hospital laundry, tram and bus depots, data centres, ventilation, water heating, public chargers — each with realistic power (kW), duration (h), allowed time window, and flexibility factor.
- **Data inputs.** Collected hourly Nord Pool spot prices from the Helen website in **November 2025**; assembled the Nordic-grid hourly CO₂ intensity profile (clean midday from solar / hydro / nuclear, dirty evening from thermal backup).

---

## What this project demonstrates

- **Energy-systems engineering** — hourly time-discretised model of a city with 24 heterogeneous loads spanning HVAC, refrigeration, EV charging, and heat pumps.
- **Engineering judgement under trade-offs** — grid stress vs. wholesale price, participation vs. flexibility, peak vs. cost vs. CO₂. Every tension is exposed as a knob the user can move, not buried in code.
- **End-to-end delivery** — working interactive GUI, four live charts, slider-driven what-if exploration, custom-asset entry form. **Pure Python 3 standard library, zero external dependencies, runs in one second.**

---

## The problem

The Helsinki capital region is electrifying fast — heat pumps, EVs, electric buses, induction kitchens, data centres — all at once. Peak electricity consumption in Espoo rose **+46 %** between January 2023 and January 2024, with **+179 %** projected for the Caruna Espoo grid area by 2030 *(Caruna)*. Building more grid is slow, expensive, and carbon-intensive. **Shifting flexible loads in time** is the cheapest, fastest alternative.

## The idea

Most large city loads don't need to run *right now*. An EV plugged in at 18:00 just needs to be full by morning. A supermarket's defrost cycle doesn't care whether it runs at 19:00 or 03:00. A data centre's battery backup can charge whenever.

| Strategy | Behaviour |
|---|---|
| **Before** *(naive)* | Every asset starts at the earliest hour of its allowed window — "plug in when I get home". |
| **After** *(smart)* | Each asset is shifted inside its window to the hours that minimise `grid_weight · load + price_weight · price`. |

![Before vs After comparison overlay](screenshots/03-comparison.png)

*Red is the naive baseline, dashed blue is the smart schedule. The optimiser visibly clips the evening peak (17–21) and refills the cheap, clean midday valley.*

![Hourly Nord Pool price curve](screenshots/04-price.png)

*Hourly Nord Pool spot prices for the Helsinki bidding zone, recorded from the Helen website in November 2025 — the driver behind the cost saving and a clue to where the scheduler is moving load.*

---

## How the smart scheduler works

1. Each asset has a *participating power* = `power × participation_slider × flex_factor`. The non-participating portion stays at the naive time.
2. Assets are processed **largest-first** so big loads claim the least-stressed hours.
3. For each asset, every hour in its window gets a score:
   ```
   score = grid_weight · normalised_load + price_weight · normalised_price
   ```
   Variable loads pick the lowest-scoring hours individually; fixed loads pick the best contiguous block.
4. After each placement the after-curve is updated, so smaller loads re-score against the new state and don't pile on top.

Slider changes are debounced at 200 ms so the four canvases feel live without re-rendering on every pixel of drag.

---

## Why it matters

The **Climate-Neutral Espoo 2030** roadmap already lists demand-side response as a key step on its electricity-based heat decarbonisation path. As the grid's bottleneck moves from *production* to *peak transmission capacity*, flattening peaks becomes the cheapest carbon-and-cost lever the city has — **no new substations, no new turbines, no new permits.** Scale FlexiCity from 24 fictional assets to a real city of hundreds of thousands of EVs, heat pumps, and HVAC systems, and the same percentages translate into megawatts of avoided peak and kilotonnes of CO₂ per year.

---

## Modelling assumptions & limitations

- One-day horizon; no inter-day storage, no inter-asset dependencies, no weather forecast.
- Shifting an asset inside its allowed window is assumed thermally and operationally safe.
- "No coordination" baseline = every asset starts at its earliest allowed hour.
- Nord Pool prices are a one-day snapshot from the Helen website (Nov 2025), not a live feed.
- Single shared bus — no distribution-network or substation-level modelling.

**Next steps:** live data feeds (Nord Pool & Fingrid), multi-day horizon with EV state-of-charge carryover and heat-pump pre-heating, MILP solver for global optimality, distribution-network modelling, forecast-uncertainty handling, tariff-aware EUR figures.

---

## Run it

Python 3.x with `tkinter` (bundled with most installs). No external dependencies.

```bash
python Flexi_City.py
```

**Using the program:** move *Flex participation* and *Priority* to explore; hit any of the four optimiser buttons to find the best (flex, priority) combination for that objective; add your own loads with the *Add flexible load* form; *Reset to defaults* clears everything.

---

## Built for

**Urban Circular Hack Helsinki 2025** — U!REKA European University hackathon
HXRC Arabia Campus, 24–25 November 2025
Partners: Metropolia UAS, City of Helsinki, City of Espoo, City of Vantaa, Helsinki-Uusimaa Regional Council

## Team 7

- Robert Winiarczyk
- Dimitrios Pontikakis Batana
- Ailikuti Tayier

## Sources

- *Towards Climate-Neutral Espoo 2030*, Elina Wanne, City of Espoo (peak power figures via Caruna)
- *Energy Solutions as part of Strategic Urban Planning*, Alpo Tani, City of Helsinki
- Hourly Nord Pool spot prices, recorded from the Helen website, November 2025
- Fingrid hourly CO₂ intensity (Nordic mix proxy)

## License

MIT
