# FlexiCity
![FlexiCity dashboard showing before/after load curves, comparison and price graphs, and peak/cost/CO₂ stats](docs/screenshot.png)
**Shift flexible electricity loads to flatten Helsinki's evening demand spike, and see the grid, cost, and CO₂ impact in real time.**

A 24-hour interactive simulator built for **Urban Circular Hack Helsinki 2025** (U!REKA European University hackathon), for the challenge:

> *How might we prepare cities for the increasing demand in electricity?*

---

## The problem

The Helsinki capital region is electrifying fast. Heat pumps, EVs, data centres, electric buses, and induction kitchens are all coming online at the same time, and the grid is feeling it:

- **+46 %** rise in monthly peak electricity consumption in Espoo between January 2023 and January 2024 *(Caruna)*
- **+179 %** projected rise in peak power demand in the Caruna Espoo grid area by 2030 *(Caruna)*
- As district heating decarbonises, transport and consumer electricity become the dominant emission sources in the city *(Climate-Neutral Espoo 2030)*

Building more grid is slow, expensive, and carbon-intensive in itself. A cheaper and faster option is to shift flexible loads in time, so the city uses the grid it already has more evenly.

## The idea

Most large electricity loads in a city don't actually need to run *right now*. An EV plugged in at 18:00 doesn't need to charge between 18:00 and 22:00, it just needs to be full by morning. A supermarket's defrost cycle doesn't care whether it runs at 19:00 or 03:00. A data centre's battery backup can charge whenever.

**FlexiCity** simulates about 24 flexible loads across a city (EV fleets, heat pumps, office HVAC, supermarket refrigeration, tram and bus depots, data centres, public chargers, schools, hospitals, swimming pools) and compares two scheduling strategies side by side:

| Strategy | Behaviour |
|---|---|
| **Before** *(dumb)* | Every asset starts at the earliest hour of its allowed window. The "plug in when I get home" default. |
| **After** *(smart)* | Each asset is shifted inside its allowed window to the hours that minimise a weighted blend of grid load and electricity price. |

Two sliders let the user explore tradeoffs live:

- **Flex participation**: what % of each load can the operator actually shift?
- **Grid vs. Price priority**: should the optimiser flatten the demand curve, or chase the cheapest hours?

There's also a built-in simulated-annealing optimiser. It uses multi-restart and tracks the current and best-seen state separately, so it doesn't lose the optimum when it accepts a temporarily-worse move. Hit the button and it finds the slider combo that gives the lowest peak.

## What you see

Four live graphs:

1. **Before**: naive load curve over 24 h
2. **After**: smart-scheduled load curve over 24 h
3. **Comparison**: both overlaid
4. **Price curve**: Nordic spot-price proxy (cents/kWh)

And six headline numbers, updated as you move the sliders:

- Peak demand **before** / **after**, and the reduction (units & %)
- Daily electricity cost **before** / **after** (EUR)
- **CO₂ saving** (kg/day, %, and annualised tCO₂/year)

The CO₂ profile follows the Nordic grid mix: cleaner midday (solar and hydro), dirtier evening (peak thermal backup). So shifting load away from the evening spike isn't only cheaper, it's also lower-carbon.

## Why it matters for Helsinki & Espoo

The **Climate-Neutral Espoo 2030** roadmap already lists "demand side response (smart steering of district heating)" as a key step on its electricity-based heat decarbonisation path. Helsinki's Helen is shifting more and more onto Nordic carbon-free electricity, which is hourly-variable in both price and emissions intensity.

As the grid's bottleneck moves from *production* to *peak transmission capacity*, flattening peaks becomes the cheapest carbon-and-cost lever the city has, and it needs no new substations, no new turbines, no new permits.

FlexiCity is a visual decision-support prototype for that conversation. A planner, building owner, or fleet operator can see in seconds what their flexibility is worth in MW shaved, EUR saved, and CO₂ avoided.

## Quick start

Requires Python 3.x with `tkinter` (bundled with most Python installs). No external dependencies. The GUI, graphing, and optimiser are all standard library.

```bash
python Flexi_City.py
```

### Using the Program

1. Move **Flex participation** to set how much of each load the city can actually shift (0 = nobody participates, 100 = full city-wide flexibility).
2. Move **Priority** toward *Grid* to flatten the curve, or toward *Price* to chase cheap hours.
3. Click **Optimize peak (FAST)** to let simulated annealing find the best slider combo automatically.
4. Add your own loads (a new EV charger, a sauna, a public swimming pool) through the **Add flexible load** form to test what-if scenarios.

## Architecture in one paragraph

`recalculate_schedules()` builds both load curves. For the naive baseline it stacks each asset's full power at the first `duration_h` hours of its window. For the smart schedule it processes assets largest-first, scores every hour in each asset's allowed window by

```
score = grid_weight * normalized_load + price_weight * normalized_price
```

and places the asset at the lowest-scoring hours. Because the score re-reads the *updated* after-curve each iteration, large loads don't pile on top of each other. Variable assets can be split across non-contiguous hours; fixed assets are placed as the best contiguous block. Slider changes are debounced at 200 ms so the four canvases feel live without re-rendering on every pixel of drag.

## Modelling assumptions

To keep the prototype honest about what it isn't:

- Shifting an asset inside its allowed window does not break operational or thermal constraints (a heat pump keeps the building warm, a fridge keeps its food cold).
- "No coordination" baseline = every asset starts at the opening of its window. This is a reasonable stand-in for current "plug in when I get home" behaviour.
- The hourly CO₂ profile reflects a Nordic grid mix: lower midday (solar / hydro / nuclear), higher evening (thermal backup).
- One-day horizon. No inter-day storage, no inter-asset dependencies, no weather forecast.
- Prices are a Nordic spot-price proxy, not a live Nord Pool feed.
- Single shared bus, with no distribution-network modelling and no substation-level congestion.

## Limitations & what we'd build next

- **Multi-day horizon**: heat pump pre-heating, EV state-of-charge carryover, weekly weather effects.
- **Real data feeds**: Nord Pool spot price and Fingrid hourly CO₂ intensity instead of proxies.
- **Uncertainty**: the current optimiser assumes the schedule executes perfectly. A real one needs to handle forecast error.
- **Tariff structures**: capacity charges and dynamic transmission tariffs are what make the EUR figure real for a building owner.
- **Distribution-network modelling**: peak relief is only useful if it lands at the *right* substation. The current single-bus model is too coarse.
- **Operator UX**: today the app is a planner's sandbox. The next step is a per-asset agent that negotiates with a market.

## Built for

**Urban Circular Hack Helsinki 2025**, U!REKA European University hackathon.
HXRC Arabia Campus, 24–25 November 2025.
Partners: Metropolia UAS, City of Helsinki, City of Espoo, City of Vantaa, Helsinki-Uusimaa Regional Council.

Chosen challenge: *How might we prepare cities for the increasing demand in electricity?*

## Sources

- *Towards Climate-Neutral Espoo 2030*, by Elina Wanne, City of Espoo (peak power figures via Caruna)
- *Energy Solutions as part of Strategic Urban Planning*, by Alpo Tani, City of Helsinki
- Nord Pool day-ahead spot price patterns (proxy)
- Fingrid hourly CO₂ intensity (Nordic mix proxy)

## Team 7

-Robert Winiarczyk
-Dimitris
-Alkut

## License

MIT
