# FlexiCity

**A 24-hour load shifting simulator that reduces a Nordic city's evening electricity peak by 9.6 percent, lowers daily flex-asset energy cost by 10.5 percent, and avoids about 7.3 tonnes of CO2 per year, with no behaviour change from end users.**

`Thermal systems` · `HVAC and heat pumps` · `Refrigeration` · `Energy systems engineering` · `Numerical simulation` · `Multi-objective optimisation` · `Demand-side flexibility` · `Python`

![FlexiCity dashboard showing before and after load curves, comparison and price graphs, and peak, cost and CO2 stats](screenshots/01-overview.png)

Built in two days for Urban Circular Hack Helsinki 2025 (U!REKA European University hackathon). The challenge: how do we prepare cities for the growing demand on the electricity grid?

## Why this exists

Cities across the Nordics are electrifying heating, transport, and refrigeration faster than the grid can be expanded. In Espoo, peak winter consumption rose 46 percent year on year between January 2023 and January 2024, with a further 179 percent projected for the Caruna Espoo network by 2030. New substations, transformers, and generation capacity are slow and capital intensive. Shifting the timing of flexible mechanical and thermal loads is cheaper, faster, and fully reversible.

## The engineering problem

Most large mechanical loads in a building or vehicle fleet do not need to run at a fixed clock time. An EV charges overnight regardless of when it was plugged in. A supermarket defrost cycle can run at 03:00 just as well as at 19:00. A hospital laundry batch can shift a few hours. A heat pump can pre-heat a building ahead of the evening peak. The question is which hour each load should run, given:

- The thermal and operational window of each asset
- The shape of the city's underlying demand curve
- The hourly wholesale electricity price
- The hour-by-hour CO2 intensity of the grid mix

This is a constrained, multi-objective scheduling problem over 24 hourly time steps and roughly two dozen heterogeneous loads.

## My contributions

I led the engineering side of the project, covering the load model, the scheduling algorithm, the optimisation, and the input data.

**Load model.** Parameterised 24 mechanical and electrical assets including residential and bus depot EV chargers, apartment block heat pumps, office HVAC pre-cooling, supermarket and small shop refrigeration, hospital laundry, public swimming pool water heating, metro and school ventilation, and data centre battery charging. Each asset has a rated power (kW), a duty cycle duration (h), an allowed time window, and a flexibility factor that reflects how much of its load can realistically be moved without compromising service.

**Scheduling algorithm.** Designed a naive baseline (every asset starts at the earliest hour of its window, modelling zero coordination) and a smart scheduler. Three engineering decisions in the smart scheduler:

1. Process assets largest first, so big loads claim the least stressed hours before smaller loads pile in.
2. Separate variable loads (energy can be split across non-contiguous hours) from fixed loads (must run as one contiguous block, like an oven preheat or a hospital laundry cycle).
3. Re-score after every placement, both between assets and within a variable asset's own pick, so the algorithm never piles its own load on top of itself.

**Multi-objective optimisation.** Built four objectives (peak demand, daily cost, CO2 emissions, combined) on top of an exhaustive grid search across (flex participation, grid versus price priority), 10,201 schedules per run. Added a no-regression guardrail: any schedule where one of the active metrics loses against the naive baseline is rejected. Without this filter the equal-weighted average would trade a small cost increase for a large peak reduction, which is mathematically sound but breaks the everyone-wins framing the project relies on.

**Input data.** Collected hourly Nord Pool spot prices for the Helsinki bidding zone from the Helen utility website in November 2025. Assembled a Nordic grid CO2 intensity profile (lower midday with solar and hydro, higher evening with thermal backup).

## Results

All numbers below are at the default settings (100 percent flex participation, 50 / 50 grid versus price priority). The four built-in optimisers push every metric further.

| Metric            | Before naive | After smart | Saving         |
|-------------------|--------------|-------------|----------------|
| Peak demand       | 306.0 kW     | 276.5 kW    | 29.5 kW (9.6%) |
| Daily energy cost | €432.57      | €387.21     | €45.36 (10.5%) |

CO2 saving on flex assets: about 20 kg per day, roughly 7.3 tonnes of CO2 avoided per year.

![Peak, cost and CO2 stats panel](screenshots/02-stats.png)

The smart schedule visibly clips the evening peak between 17:00 and 21:00 and refills the cheaper, cleaner midday valley.

![Before and after comparison overlay](screenshots/03-comparison.png)

![Hourly Nord Pool price curve](screenshots/04-price.png)

## What this project demonstrates

- **Thermal and energy systems modelling.** Time-discretised, hour by hour, with realistic asset operational constraints (thermal windows, duty cycle length, batch versus distributable energy).
- **Engineering judgement under trade-offs.** Peak versus cost versus CO2, participation versus flexibility, grid stress versus wholesale price. Every tension is exposed as a slider the user can move, not hidden in code.
- **Numerical methods.** Exhaustive grid search with multi-criteria scoring, normalised objective composition, and tie-breaking on a secondary metric to avoid degenerate optima.
- **End-to-end delivery.** Working interactive GUI, four live charts, slider-driven what-if exploration, custom asset entry form, four optimiser buttons. Pure Python 3 standard library, zero external dependencies, runs from a single command.

## How the smart scheduler works

1. Each asset has a participating power equal to `power_kW * participation_slider * flex_factor`. The non-participating portion stays at the asset's naive time so the model never claims more flexibility than the asset can deliver.
2. Assets are processed in decreasing order of rated power.
3. Each hour in the asset's allowed window receives a score:
   ```
   score = grid_weight * normalised_load + price_weight * normalised_price
   ```
4. Variable assets pick the lowest-scoring hours one at a time, re-scoring against the updated demand curve after every pick. Fixed assets pick the lowest-scoring contiguous block of the required duration.
5. After the asset is placed, the city demand curve is updated so the next asset sees the new state.

Slider input is debounced at 200 ms so all four canvases stay responsive without redrawing on every pixel of drag.

## Modelling assumptions and limitations

- One day horizon. No inter-day storage and no EV state-of-charge carryover between days.
- Shifting an asset inside its allowed window is assumed to be thermally and operationally safe.
- The naive baseline assumes zero coordination, with every asset starting at the earliest hour it is allowed to run.
- Nord Pool prices are a one-day snapshot from November 2025, not a live feed.
- Single shared bus. No distribution network or substation-level modelling.

Natural next steps include live price and CO2 feeds, a multi-day horizon with EV state-of-charge carryover and heat pump pre-heating, a MILP solver for global optimality, distribution-network modelling, and uncertainty quantification on the demand and price forecasts.

## Run it

Python 3 with `tkinter` (bundled with most installs). No external dependencies.

```bash
python Flexi_City.py
```

Move the flex participation and grid versus price priority sliders to explore. Press any of the four optimiser buttons to find the best (flex, priority) setting for that objective. Use the add flexible load form to add custom assets, or press reset to defaults to clear.

## Built for

Urban Circular Hack Helsinki 2025, U!REKA European University hackathon.
HXRC Arabia Campus, 24 to 25 November 2025.
Partners: Metropolia UAS, City of Helsinki, City of Espoo, City of Vantaa, Helsinki-Uusimaa Regional Council.

## Team 7

- Robert Winiarczyk
- Dimitrios Pontikakis Batana
- Ailikuti Tayier

## Sources

- *Towards Climate-Neutral Espoo 2030*, Elina Wanne, City of Espoo (peak power figures via Caruna)
- *Energy Solutions as part of Strategic Urban Planning*, Alpo Tani, City of Helsinki
- Hourly Nord Pool spot prices, recorded from the Helen utility website, November 2025
- Fingrid hourly CO2 intensity, Nordic mix proxy

## License

MIT
