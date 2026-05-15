import tkinter as tk
from tkinter import ttk, messagebox
import math
import copy

# ========================================
# FLEXI CITY - SMART ELECTRICITY LOAD SHIFTING SIMULATOR
# ========================================
# Competition: Urban Circular Hack Helsinki 2025
# Topic: Preparing cities for the increasing demand in electricity
#
# WHAT THIS DOES
#   Simulates a city of 24 flexible electricity loads (EVs, heat pumps,
#   HVAC, fridges, chargers, etc.) and compares two scheduling strategies:
#     BEFORE  Each load runs from the earliest hour of its allowed window
#             (no coordination - "plug in when I get home" behaviour)
#     AFTER   Each load is shifted to hours that minimize a weighted
#             combination of grid load and electricity price
#   Reports peak demand, daily cost, and CO2 emissions for both.
#
# OPTIMIZER
#   - Exhaustive 1% grid search over (flex%, priority%)
#   - Four objectives: peak, cost, CO2, multi-objective (equal-weighted)
#
# MODELLING ASSUMPTIONS
#   - Shifting an asset inside its window does not violate operational
#     or thermal constraints
#   - "No coordination" baseline = start at window opening
#   - CO2 profile reflects Nordic grid mix (renewables + thermal backup)
#   - No inter-day or inter-asset dependencies

NUM_HOURS = 24

# Nordic spot price proxy, cents/kWh, hour-by-hour
PRICE_PER_HOUR = [
    8.70, 8.48, 8.52, 8.61, 8.69, 8.69,
    9.56, 11.58, 12.72, 13.07, 15.65, 17.65,
    16.24, 15.55, 15.12, 16.64, 18.60, 21.53,
    22.68, 20.29, 17.09, 14.09, 12.81, 11.63
]


def generate_base_load(num_hours=NUM_HOURS):
    base = []
    for h in range(num_hours):
        val = 40.0
        if 7 <= h <= 9:
            val += 25.0
        if 17 <= h <= 21:
            val += 35.0
        base.append(val)
    return base


# Lower midday (solar), higher evening (peak fossil fuels), kg/kWh
CO2_PER_HOUR = [
    0.110, 0.105, 0.100, 0.095, 0.090, 0.085,
    0.080, 0.075, 0.065, 0.055, 0.045, 0.040,
    0.038, 0.035, 0.040, 0.050, 0.065, 0.085,
    0.110, 0.125, 0.120, 0.115, 0.115, 0.112,
]

BASE_LOAD = generate_base_load()

ASSETS = [
    {"owner": "City EV fleet",        "appliance": "Fast chargers",         "power_kW": 80.0, "duration_h": 4, "start_hour": 17, "end_hour": 7,  "variable": True,  "enabled": True, "flex_factor": 0.95},
    {"owner": "Office block A",       "appliance": "HVAC pre-cooling",      "power_kW": 30.0, "duration_h": 3, "start_hour": 14, "end_hour": 22, "variable": True,  "enabled": True, "flex_factor": 0.90},
    {"owner": "Supermarket",          "appliance": "Fridge defrost cycles", "power_kW": 20.0, "duration_h": 4, "start_hour": 0,  "end_hour": 24, "variable": False, "enabled": True, "flex_factor": 0.60},
    {"owner": "Residential block",    "appliance": "EV chargers",           "power_kW": 40.0, "duration_h": 6, "start_hour": 18, "end_hour": 7,  "variable": True,  "enabled": True, "flex_factor": 0.90},
    {"owner": "Apartment block 1",    "appliance": "Heat pumps",            "power_kW": 25.0, "duration_h": 5, "start_hour": 5,  "end_hour": 10, "variable": True,  "enabled": True, "flex_factor": 0.80},
    {"owner": "Apartment block 2",    "appliance": "Heat pumps",            "power_kW": 30.0, "duration_h": 5, "start_hour": 5,  "end_hour": 10, "variable": True,  "enabled": True, "flex_factor": 0.80},
    {"owner": "Tram depot",           "appliance": "Night chargers",        "power_kW": 60.0, "duration_h": 3, "start_hour": 0,  "end_hour": 6,  "variable": True,  "enabled": True, "flex_factor": 0.85},
    {"owner": "Metro station",        "appliance": "Ventilation",           "power_kW": 35.0, "duration_h": 4, "start_hour": 10, "end_hour": 22, "variable": True,  "enabled": True, "flex_factor": 0.85},
    {"owner": "Data center X",        "appliance": "Battery charging",      "power_kW": 70.0, "duration_h": 5, "start_hour": 0,  "end_hour": 24, "variable": True,  "enabled": True, "flex_factor": 1.0},
    {"owner": "Public swimming pool", "appliance": "Water heating",         "power_kW": 20.0, "duration_h": 4, "start_hour": 6,  "end_hour": 12, "variable": True,  "enabled": True, "flex_factor": 0.75},
    {"owner": "School A",             "appliance": "Ventilation",           "power_kW": 15.0, "duration_h": 3, "start_hour": 7,  "end_hour": 15, "variable": True,  "enabled": True, "flex_factor": 0.80},
    {"owner": "School B",             "appliance": "Ventilation",           "power_kW": 15.0, "duration_h": 3, "start_hour": 7,  "end_hour": 15, "variable": True,  "enabled": True, "flex_factor": 0.80},
    {"owner": "City hospital",        "appliance": "Laundry machines",      "power_kW": 25.0, "duration_h": 4, "start_hour": 8,  "end_hour": 18, "variable": False, "enabled": True, "flex_factor": 0.70},
    {"owner": "Bakery",               "appliance": "Oven preheat",          "power_kW": 10.0, "duration_h": 2, "start_hour": 3,  "end_hour": 7,  "variable": False, "enabled": True, "flex_factor": 0.50},
    {"owner": "Street lighting",      "appliance": "Early dimming",         "power_kW": 10.0, "duration_h": 4, "start_hour": 18, "end_hour": 24, "variable": True,  "enabled": True, "flex_factor": 1.0},
    {"owner": "Downtown chargers",    "appliance": "Public EV charging",    "power_kW": 50.0, "duration_h": 5, "start_hour": 17, "end_hour": 7,  "variable": True,  "enabled": True, "flex_factor": 0.85},
    {"owner": "University labs",      "appliance": "Freezer defrost",       "power_kW": 8.0,  "duration_h": 3, "start_hour": 1,  "end_hour": 7,  "variable": False, "enabled": True, "flex_factor": 0.55},
    {"owner": "Logistics warehouse",  "appliance": "Pre-chill cooling",     "power_kW": 22.0, "duration_h": 4, "start_hour": 12, "end_hour": 22, "variable": True,  "enabled": True, "flex_factor": 0.85},
    {"owner": "Office block B",       "appliance": "Server backup charging","power_kW": 18.0, "duration_h": 3, "start_hour": 0,  "end_hour": 8,  "variable": True,  "enabled": True, "flex_factor": 1.0},
    {"owner": "City gym",             "appliance": "Sauna heaters",         "power_kW": 12.0, "duration_h": 3, "start_hour": 15, "end_hour": 22, "variable": False, "enabled": True, "flex_factor": 0.65},
    {"owner": "Central library",      "appliance": "HVAC",                  "power_kW": 10.0, "duration_h": 4, "start_hour": 8,  "end_hour": 22, "variable": True,  "enabled": True, "flex_factor": 0.85},
    {"owner": "Small shops",          "appliance": "Refrigeration",         "power_kW": 18.0, "duration_h": 6, "start_hour": 8,  "end_hour": 23, "variable": True,  "enabled": True, "flex_factor": 0.65},
    {"owner": "Residential solar",    "appliance": "Battery charging",      "power_kW": 15.0, "duration_h": 5, "start_hour": 10, "end_hour": 22, "variable": True,  "enabled": True, "flex_factor": 1.0},
    {"owner": "Electric bus depot",   "appliance": "Overnight charging",    "power_kW": 90.0, "duration_h": 6, "start_hour": 22, "end_hour": 8,  "variable": True,  "enabled": True, "flex_factor": 0.95},
]

for a in ASSETS:
    a.setdefault("flex_factor", 1.0)
    a["before_hours"] = []
    a["after_hours"] = []

DEFAULT_ASSETS = copy.deepcopy(ASSETS)

before_load = BASE_LOAD[:]
after_load = BASE_LOAD[:]
cost_before_flex = 0.0
cost_after_flex = 0.0


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def get_window_hours(start_hour, end_hour):
    sh = int(start_hour)
    eh = int(end_hour)
    if sh < eh:
        return list(range(sh, eh))
    return list(range(sh, NUM_HOURS)) + list(range(0, eh))


def _asset_window(asset):
    sh = clamp(asset["start_hour"], 0, NUM_HOURS - 1)
    eh = clamp(asset["end_hour"], 0, NUM_HOURS)
    if sh == eh:
        return []
    return get_window_hours(sh, eh)


def recalculate_schedules():
    """
    Build BEFORE (naive) and AFTER (smart) load curves and costs.

    BEFORE: every asset runs at the first 'duration_h' hours of its window.
    AFTER:  each asset's participating power (= full_power * participation
            * flex_factor) is moved to the hours with the lowest score,
            where score = grid_weight * normalized_load
                        + price_weight * normalized_price.
    Assets are processed largest-first so big loads place into the
    least-stressed hours; subsequent assets re-score against the updated
    after_load, so they don't pile on top of each other.
    """
    global before_load, after_load, cost_before_flex, cost_after_flex

    participation = flex_var.get() / 100.0
    priority_val = priority_var.get() / 100.0
    price_weight = priority_val
    grid_weight = 1.0 - priority_val

    for a in ASSETS:
        a["before_hours"] = []
        a["after_hours"] = []

    # ---- BEFORE: naive schedule ----
    before_load = BASE_LOAD[:]
    for asset in ASSETS:
        if not asset.get("enabled", True):
            continue
        window_hours = _asset_window(asset)
        if not window_hours:
            continue
        power_full = asset["power_kW"]
        if power_full <= 0:
            continue
        duration = int(clamp(asset["duration_h"], 1, len(window_hours)))
        hours_used = window_hours[:duration]
        for h in hours_used:
            before_load[h] += power_full
        asset["before_hours"] = hours_used

    cost_before_flex = 0.0
    for asset in ASSETS:
        if not asset.get("enabled", True):
            continue
        for h in asset["before_hours"]:
            cost_before_flex += asset["power_kW"] * PRICE_PER_HOUR[h]

    # ---- AFTER: smart schedule ----
    after_load = before_load[:]

    for asset in sorted(
        [a for a in ASSETS if a.get("enabled", True)],
        key=lambda a: -a["power_kW"]
    ):
        power_full = asset["power_kW"]
        if power_full <= 0:
            continue

        flex_factor = asset.get("flex_factor", 1.0)
        participating_power = power_full * participation * flex_factor

        if participation <= 0 or not asset["before_hours"]:
            asset["after_hours"] = asset["before_hours"][:]
            continue

        window_hours = _asset_window(asset)
        if not window_hours:
            asset["after_hours"] = asset["before_hours"][:]
            continue

        duration = int(clamp(asset["duration_h"], 1, len(window_hours)))

        # remove the participating portion from naive hours
        for h in asset["before_hours"]:
            after_load[h] -= participating_power

        # score each hour in the window
        window_loads = [after_load[hh] for hh in window_hours]
        min_load, max_load = min(window_loads), max(window_loads)
        window_prices = [PRICE_PER_HOUR[hh] for hh in window_hours]
        min_price, max_price = min(window_prices), max(window_prices)

        hour_score = {}
        for hh in window_hours:
            load_norm = (after_load[hh] - min_load) / (max_load - min_load) if max_load > min_load else 0.0
            price_norm = (PRICE_PER_HOUR[hh] - min_price) / (max_price - min_price) if max_price > min_price else 0.0
            hour_score[hh] = grid_weight * load_norm + price_weight * price_norm

        chosen_hours = []
        if asset.get("variable", True):
            available = window_hours.copy()
            for _ in range(duration):
                if not available:
                    break
                best_h = min(available, key=lambda h: hour_score[h])
                chosen_hours.append(best_h)
                available.remove(best_h)
        else:
            # fixed: pick best continuous block of length 'duration'
            duration = min(duration, len(window_hours))
            best_block = None
            best_block_score = None
            for i in range(0, len(window_hours) - duration + 1):
                block = window_hours[i:i + duration]
                block_score = sum(hour_score[h] for h in block)
                if best_block_score is None or block_score < best_block_score:
                    best_block_score = block_score
                    best_block = block
            if best_block is not None:
                chosen_hours = best_block

        for h in chosen_hours:
            after_load[h] += participating_power
        asset["after_hours"] = chosen_hours

    cost_after_flex = 0.0
    for asset in ASSETS:
        if not asset.get("enabled", True):
            continue
        power_full = asset["power_kW"]
        flex_factor = asset.get("flex_factor", 1.0)
        participating_power = power_full * participation * flex_factor
        remaining_power = power_full - participating_power
        for h in asset["before_hours"]:
            cost_after_flex += remaining_power * PRICE_PER_HOUR[h]
        for h in asset["after_hours"]:
            cost_after_flex += participating_power * PRICE_PER_HOUR[h]


# -------- UI --------

root = tk.Tk()
root.title("FlexiCity - Peak, Price & CO2 Demo (24h)")
root.geometry("1450x900")

APP_FONT = "Segoe UI"
COLOR_SAVING = "#2ca02c"
COLOR_RESET = "#c62828"
COLOR_GRID = "#e8e8e8"
COLOR_BEFORE_LINE = "#d62728"
COLOR_AFTER_LINE = "#1f77b4"
COLOR_PRICE_LINE = "#6b6b6b"

style = ttk.Style()
style.configure("TLabel", font=(APP_FONT, 9))
style.configure("TLabelframe.Label", font=(APP_FONT, 10, "bold"))
style.configure("StatValue.TLabel", font=(APP_FONT, 9, "bold"))
style.configure("Saving.TLabel", font=(APP_FONT, 9, "bold"), foreground=COLOR_SAVING)
style.configure("Loss.TLabel", font=(APP_FONT, 9, "bold"), foreground=COLOR_RESET)
style.configure("TButton", font=(APP_FONT, 9))
style.configure("Optimize.TButton", font=(APP_FONT, 9, "bold"))
style.configure("Reset.TButton", font=(APP_FONT, 9, "bold"), foreground=COLOR_RESET)
style.configure("TCheckbutton", font=(APP_FONT, 9))
style.configure("TEntry", font=(APP_FONT, 9))

root.after_id_flex = None
root.after_id_priority = None
root.after_id_redraw = None

mainframe = ttk.Frame(root, padding=10)
mainframe.grid(row=0, column=0, sticky="nsew")
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

left_frame = ttk.Frame(mainframe)
left_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 15))

right_frame = ttk.Frame(mainframe)
right_frame.grid(row=0, column=1, sticky="nsew")
mainframe.columnconfigure(1, weight=1)
mainframe.rowconfigure(0, weight=1)

# --- Stats ---
stats_frame = ttk.LabelFrame(left_frame, text="Peak, cost & CO2")
stats_frame.grid(row=0, column=0, sticky="new", pady=(0, 5))

peak_before_var = tk.StringVar()
peak_after_var = tk.StringVar()
reduction_var = tk.StringVar()
cost_before_var = tk.StringVar()
cost_after_var = tk.StringVar()
saving_cost_var = tk.StringVar()
co2_var = tk.StringVar()

ttk.Label(stats_frame, text="Peak BEFORE").grid(row=0, column=0, sticky="w", padx=(0, 10))
ttk.Label(stats_frame, textvariable=peak_before_var, style="StatValue.TLabel").grid(row=0, column=1, sticky="w")
ttk.Label(stats_frame, text="Peak AFTER").grid(row=1, column=0, sticky="w", padx=(0, 10))
ttk.Label(stats_frame, textvariable=peak_after_var, style="StatValue.TLabel").grid(row=1, column=1, sticky="w")
ttk.Label(stats_frame, text="Peak reduction").grid(row=2, column=0, sticky="w", padx=(0, 10))
ttk.Label(stats_frame, textvariable=reduction_var, style="Saving.TLabel").grid(row=2, column=1, sticky="w")
ttk.Separator(stats_frame, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)
ttk.Label(stats_frame, text="Cost BEFORE (flex assets)").grid(row=4, column=0, sticky="w", padx=(0, 10))
ttk.Label(stats_frame, textvariable=cost_before_var, style="StatValue.TLabel").grid(row=4, column=1, sticky="w")
ttk.Label(stats_frame, text="Cost AFTER (flex assets)").grid(row=5, column=0, sticky="w", padx=(0, 10))
ttk.Label(stats_frame, textvariable=cost_after_var, style="StatValue.TLabel").grid(row=5, column=1, sticky="w")
ttk.Label(stats_frame, text="Saving").grid(row=6, column=0, sticky="w", padx=(0, 10))
ttk.Label(stats_frame, textvariable=saving_cost_var, style="Saving.TLabel").grid(row=6, column=1, sticky="w")
ttk.Separator(stats_frame, orient="horizontal").grid(row=7, column=0, columnspan=2, sticky="ew", pady=2)
ttk.Label(stats_frame, text="CO2 saving").grid(row=8, column=0, sticky="w", padx=(0, 10))
ttk.Label(stats_frame, textvariable=co2_var, style="Saving.TLabel").grid(row=8, column=1, sticky="w")

# --- Add ---
input_frame = ttk.LabelFrame(left_frame, text="Add flexible load")
input_frame.grid(row=1, column=0, sticky="new", pady=(5, 0))

ttk.Label(input_frame, text="Owner / Name:").grid(row=0, column=0, sticky="w")
entry_owner = ttk.Entry(input_frame, width=25)
entry_owner.grid(row=0, column=1, sticky="w")

ttk.Label(input_frame, text="Appliance:").grid(row=1, column=0, sticky="w")
entry_appliance = ttk.Entry(input_frame, width=25)
entry_appliance.grid(row=1, column=1, sticky="w")

ttk.Label(input_frame, text="Power (kW):").grid(row=2, column=0, sticky="w")
entry_power = ttk.Entry(input_frame, width=10)
entry_power.grid(row=2, column=1, sticky="w")

ttk.Label(input_frame, text="Duration (h):").grid(row=3, column=0, sticky="w")
entry_duration = ttk.Entry(input_frame, width=10)
entry_duration.grid(row=3, column=1, sticky="w")

ttk.Label(input_frame, text="Start hour (0-23):").grid(row=4, column=0, sticky="w")
entry_start = ttk.Entry(input_frame, width=10)
entry_start.grid(row=4, column=1, sticky="w")

ttk.Label(input_frame, text="End hour (0-24):").grid(row=5, column=0, sticky="w")
entry_end = ttk.Entry(input_frame, width=10)
entry_end.grid(row=5, column=1, sticky="w")

var_variable = tk.BooleanVar(value=True)
ttk.Checkbutton(
    input_frame, text="Variable (can be split into separate hours)",
    variable=var_variable
).grid(row=6, column=0, columnspan=2, sticky="w", pady=(5, 0))

var_enabled = tk.BooleanVar(value=True)
ttk.Checkbutton(
    input_frame, text="Enabled (included in simulation)",
    variable=var_enabled
).grid(row=7, column=0, columnspan=2, sticky="w", pady=(2, 0))

ttk.Label(input_frame, text="Flexibility (0-1):").grid(row=8, column=0, sticky="w")
entry_flex = ttk.Entry(input_frame, width=10)
entry_flex.insert(0, "1.0")
entry_flex.grid(row=8, column=1, sticky="w")

def read_form_values():
    owner = entry_owner.get().strip() or "Custom house"
    appliance = entry_appliance.get().strip() or "Appliance"
    power = float(entry_power.get())
    duration = int(entry_duration.get())
    start = int(entry_start.get())
    end = int(entry_end.get())
    flex_factor = float(entry_flex.get())

    if not (0 <= start < NUM_HOURS):
        raise ValueError("Start hour must be between 0 and 23")
    if not (0 <= end <= NUM_HOURS):
        raise ValueError("End hour must be between 0 and 24")
    if start == end:
        raise ValueError("Start and end hour cannot be the same (empty window)")
    if not (0.0 <= flex_factor <= 1.0):
        raise ValueError("Flexibility must be between 0.0 and 1.0")
    if power <= 0:
        raise ValueError("Power must be positive")
    if duration <= 0:
        raise ValueError("Duration must be positive")
    window_length = len(get_window_hours(start, end))
    if duration > window_length:
        raise ValueError(
            f"Duration ({duration}h) exceeds window length ({window_length}h). "
            f"Widen the start-end window or reduce the duration."
        )

    return {
        "owner": owner, "appliance": appliance,
        "power_kW": power, "duration_h": duration,
        "start_hour": start, "end_hour": end,
        "variable": var_variable.get(), "enabled": var_enabled.get(),
        "flex_factor": flex_factor,
        "before_hours": [], "after_hours": [],
    }


def clear_form():
    entry_owner.delete(0, tk.END)
    entry_appliance.delete(0, tk.END)
    entry_power.delete(0, tk.END)
    entry_duration.delete(0, tk.END)
    entry_start.delete(0, tk.END)
    entry_end.delete(0, tk.END)
    entry_flex.delete(0, tk.END)
    entry_flex.insert(0, "1.0")
    var_variable.set(True)
    var_enabled.set(True)


def add_asset():
    try:
        ASSETS.append(read_form_values())
        recalculate_schedules()
        update_stats_and_graph()
        clear_form()
    except ValueError as e:
        messagebox.showerror("Invalid input", str(e))


ttk.Button(input_frame, text="Add new", command=add_asset)\
    .grid(row=9, column=0, columnspan=2, pady=(5, 0), sticky="ew")

# --- Sliders ---
priority_frame = ttk.LabelFrame(left_frame, text="Priority: grid vs price")
priority_frame.grid(row=2, column=0, sticky="new", pady=(5, 0))

priority_var = tk.DoubleVar(value=50.0)
ttk.Label(priority_frame, text="Grid  <-  focus  ->  Price").grid(row=0, column=0, sticky="w")

priority_value_label = ttk.Label(priority_frame, text="Grid 50% / Price 50%")
priority_value_label.grid(row=2, column=0, sticky="w")


def on_priority_change(v=None):
    price_w = priority_var.get() / 100.0
    grid_w = 1.0 - price_w
    priority_value_label.config(text=f"Grid {grid_w*100:.0f}% / Price {price_w*100:.0f}%")
    recalculate_schedules()
    update_stats_and_graph()


def on_priority_change_debounced(v):
    if root.after_id_priority:
        root.after_cancel(root.after_id_priority)
    root.after_id_priority = root.after(200, on_priority_change)


scale_priority = ttk.Scale(
    priority_frame, from_=0, to=100, orient="horizontal",
    variable=priority_var, command=on_priority_change_debounced
)
scale_priority.grid(row=1, column=0, sticky="ew")
priority_frame.columnconfigure(0, weight=1)

flex_frame = ttk.LabelFrame(left_frame, text="Flex participation")
flex_frame.grid(row=3, column=0, sticky="new", pady=(5, 0))

flex_var = tk.DoubleVar(value=100.0)
flex_value_label = ttk.Label(flex_frame, text="Flexible users: 100%")
flex_value_label.grid(row=0, column=0, columnspan=2, sticky="w")


def on_flex_change(v=None):
    flex_value_label.config(text=f"Flexible users: {flex_var.get():.0f}%")
    recalculate_schedules()
    update_stats_and_graph()


def on_flex_change_debounced(v):
    if root.after_id_flex:
        root.after_cancel(root.after_id_flex)
    root.after_id_flex = root.after(200, on_flex_change)


scale_flex = ttk.Scale(
    flex_frame, from_=0, to=100, orient="horizontal",
    variable=flex_var, command=on_flex_change_debounced
)
scale_flex.grid(row=1, column=0, columnspan=2, sticky="ew")
flex_frame.columnconfigure(0, weight=1)
flex_frame.columnconfigure(1, weight=1)


def _cancel_pending_slider_callbacks():
    """Drop any deferred recalcs queued by var.set() on the ttk.Scales.
    Without this, an explicit synchronous recalc is followed ~200ms later
    by a duplicate recalc + redraw kicked off by the slider's command."""
    if root.after_id_flex:
        root.after_cancel(root.after_id_flex)
        root.after_id_flex = None
    if root.after_id_priority:
        root.after_cancel(root.after_id_priority)
        root.after_id_priority = None


def apply_optimization_result(best_flex, best_priority):
    """Push optimal sliders back to UI and refresh everything once."""
    flex_var.set(best_flex)
    priority_var.set(best_priority)
    flex_value_label.config(text=f"Flexible users: {best_flex:.0f}%")
    price_w = best_priority / 100.0
    grid_w = 1.0 - price_w
    priority_value_label.config(text=f"Grid {grid_w*100:.0f}% / Price {price_w*100:.0f}%")
    _cancel_pending_slider_callbacks()
    recalculate_schedules()
    update_stats_and_graph()


# ---- OPTIMIZER ----

def _grid_search_minimize(objective_fn):
    """Exhaustive 1% grid search over (flex%, priority%) minimizing objective_fn().
    objective_fn() may return a scalar or a tuple - tuples are compared lex,
    which lets callers add tiebreakers (e.g. minimize peak, then cost)."""
    root.config(cursor="wait")
    root.update_idletasks()
    try:
        best_flex = 0
        best_priority = 0
        best_obj = None
        for flex in range(0, 101):
            for priority in range(0, 101):
                flex_var.set(flex)
                priority_var.set(priority)
                recalculate_schedules()
                obj = objective_fn()
                if best_obj is None or obj < best_obj:
                    best_obj = obj
                    best_flex = flex
                    best_priority = priority
        return best_flex, best_priority, best_obj
    finally:
        root.config(cursor="")


def find_optimal_settings_fast():
    """Minimize peak demand. Ties are broken by cost so we don't gratuitously
    pick an expensive schedule when a cheaper one achieves the same peak."""
    best_flex, best_priority, best_obj = _grid_search_minimize(
        lambda: (max(after_load), cost_after_flex)
    )
    best_peak = best_obj[0]
    apply_optimization_result(best_flex, best_priority)
    peak_before = max(before_load)
    reduction_pct = (peak_before - best_peak) / peak_before * 100 if peak_before > 0 else 0.0
    messagebox.showinfo(
        "Peak optimization",
        f"Best peak: {best_peak:.1f} units (was {peak_before:.1f} units)\n"
        f"Peak reduction: {reduction_pct:.1f}%\n"
        f"Flex: {best_flex}% | Grid/Price: {100-best_priority}%/{best_priority}%"
    )


def find_optimal_settings_cost():
    """Minimize total daily electricity cost. Ties broken by peak."""
    best_flex, best_priority, best_obj = _grid_search_minimize(
        lambda: (cost_after_flex, max(after_load))
    )
    best_cost = best_obj[0]
    apply_optimization_result(best_flex, best_priority)
    cost_before_eur = cost_before_flex / 100.0
    cost_after_eur = best_cost / 100.0
    saving_pct = (cost_before_eur - cost_after_eur) / cost_before_eur * 100 if cost_before_eur > 0 else 0.0
    messagebox.showinfo(
        "Cost optimization",
        f"Best cost: {cost_after_eur:.2f} EUR (was {cost_before_eur:.2f} EUR)\n"
        f"Saving: {saving_pct:.1f}%\n"
        f"Flex: {best_flex}% | Grid/Price: {100-best_priority}%/{best_priority}%"
    )


def find_optimal_settings_co2():
    """Minimize total daily CO2 emissions. Ties broken by cost."""
    best_flex, best_priority, best_obj = _grid_search_minimize(
        lambda: (sum(after_load[h] * CO2_PER_HOUR[h] for h in range(NUM_HOURS)),
                 cost_after_flex)
    )
    best_co2 = best_obj[0]
    apply_optimization_result(best_flex, best_priority)
    co2_before = sum(before_load[h] * CO2_PER_HOUR[h] for h in range(NUM_HOURS))
    reduction_pct = (co2_before - best_co2) / co2_before * 100 if co2_before > 0 else 0.0
    messagebox.showinfo(
        "CO2 optimization",
        f"Best CO2: {best_co2:.1f} kg/day (was {co2_before:.1f} kg/day)\n"
        f"Reduction: {reduction_pct:.1f}%\n"
        f"Flex: {best_flex}% | Grid/Price: {100-best_priority}%/{best_priority}%"
    )


def find_optimal_settings_multi():
    """
    Find (flex, priority) where every metric with a positive baseline (peak,
    cost, CO2) improves compared to naive, then minimize their average.

    Each active metric is normalized so 1.0 = naive baseline. Schedules
    where any active metric exceeds 1.0 are rejected (return inf). Without
    this filter, an equal-weighted average will gladly trade a 0.2% cost
    rise for a 29% peak reduction, contradicting the "everyone wins" pitch.

    Metrics with zero baseline (cost when no flex assets are enabled) are
    excluded - we don't fabricate improvement on them by computing 0/1=0
    and pretending that's a 100% saving.

    If no schedule improves all active metrics, the user's slider position
    is left untouched: clobbering it with (0, 0) just to print a "no
    improvement" message is worse than doing nothing.
    """
    recalculate_schedules()
    peak_norm = max(before_load)
    cost_norm = cost_before_flex
    co2_norm = sum(before_load[h] * CO2_PER_HOUR[h] for h in range(NUM_HOURS))

    active = []
    if peak_norm > 0:
        active.append("peak")
    if cost_norm > 0:
        active.append("cost")
    if co2_norm > 0:
        active.append("co2")

    if not active:
        messagebox.showinfo(
            "Multi-objective optimization",
            "Nothing to optimize: no enabled flexible loads with positive baseline."
        )
        return

    eps = 1e-6

    def objective():
        parts = []
        if "peak" in active:
            v = max(after_load) / peak_norm
            if v > 1.0 + eps:
                return float("inf")
            parts.append(v)
        if "cost" in active:
            v = cost_after_flex / cost_norm
            if v > 1.0 + eps:
                return float("inf")
            parts.append(v)
        if "co2" in active:
            v = sum(after_load[h] * CO2_PER_HOUR[h] for h in range(NUM_HOURS)) / co2_norm
            if v > 1.0 + eps:
                return float("inf")
            parts.append(v)
        return sum(parts) / len(parts)

    best_flex, best_priority, best_obj = _grid_search_minimize(objective)

    if best_obj is None or best_obj >= 1.0 - 1e-9:
        messagebox.showinfo(
            "Multi-objective optimization",
            f"No (flex, priority) setting improves all "
            f"{len(active)} active metrics at once.\n"
            "Asset windows may be too tight to give the scheduler room to move.\n"
            "Try 'Optimize peak' or 'Optimize cost' for single-metric tuning."
        )
        return

    apply_optimization_result(best_flex, best_priority)
    # Globals now reflect the best (flex, priority); compute the breakdown.
    peak_pct = (peak_norm - max(after_load)) / peak_norm * 100 if peak_norm > 0 else 0.0
    cost_pct = (cost_before_flex - cost_after_flex) / cost_before_flex * 100 if cost_before_flex > 0 else 0.0
    co2_after = sum(after_load[h] * CO2_PER_HOUR[h] for h in range(NUM_HOURS))
    co2_pct = (co2_norm - co2_after) / co2_norm * 100 if co2_norm > 0 else 0.0

    messagebox.showinfo(
        "Multi-objective optimization",
        f"Combined score: {best_obj:.3f} (1.000 = no flex improvement)\n"
        f"Reductions - Peak: {peak_pct:.1f}% | Cost: {cost_pct:.1f}% | CO2: {co2_pct:.1f}%\n"
        f"Flex: {best_flex}% | Grid/Price: {100-best_priority}%/{best_priority}%"
    )


def reset_to_defaults():
    """Restore ASSETS list, sliders, and the input form to startup state."""
    ASSETS.clear()
    ASSETS.extend(copy.deepcopy(DEFAULT_ASSETS))
    flex_var.set(100.0)
    priority_var.set(50.0)
    flex_value_label.config(text="Flexible users: 100%")
    priority_value_label.config(text="Grid 50% / Price 50%")
    clear_form()
    _cancel_pending_slider_callbacks()
    recalculate_schedules()
    update_stats_and_graph()


optimize_frame = ttk.LabelFrame(left_frame, text="Optimize")
optimize_frame.grid(row=4, column=0, sticky="new", pady=(5, 0))
optimize_frame.columnconfigure(0, weight=1)

ttk.Button(optimize_frame, text="Optimize peak",
           command=find_optimal_settings_fast, style="Optimize.TButton")\
    .grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
ttk.Button(optimize_frame, text="Optimize cost",
           command=find_optimal_settings_cost, style="Optimize.TButton")\
    .grid(row=1, column=0, sticky="ew", padx=4, pady=2)
ttk.Button(optimize_frame, text="Optimize CO2",
           command=find_optimal_settings_co2, style="Optimize.TButton")\
    .grid(row=2, column=0, sticky="ew", padx=4, pady=2)
ttk.Button(optimize_frame, text="Optimize all (peak + cost + CO2)",
           command=find_optimal_settings_multi, style="Optimize.TButton")\
    .grid(row=3, column=0, sticky="ew", padx=4, pady=(2, 4))

ttk.Button(left_frame, text="Reset to defaults",
           command=reset_to_defaults, style="Reset.TButton")\
    .grid(row=5, column=0, sticky="ew", pady=(5, 0))

# --- Graphs ---
before_frame = ttk.LabelFrame(right_frame, text="Before - dumb scheduling")
before_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 5))

after_frame = ttk.LabelFrame(right_frame, text="After - smart scheduling")
after_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(5, 5))

bottom_frame = ttk.Frame(right_frame)
bottom_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(5, 0))

right_frame.rowconfigure(0, weight=1)
right_frame.rowconfigure(1, weight=1)
right_frame.rowconfigure(2, weight=1)
right_frame.columnconfigure(0, weight=1)
right_frame.columnconfigure(1, weight=1)

bottom_frame.rowconfigure(0, weight=1)
bottom_frame.columnconfigure(0, weight=3)
bottom_frame.columnconfigure(1, weight=2)

combined_frame = ttk.LabelFrame(bottom_frame, text="Comparison")
combined_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

price_frame = ttk.LabelFrame(bottom_frame, text="Price curve (cents/kWh)")
price_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

canvas_before = tk.Canvas(before_frame, width=700, height=220, bg="white")
canvas_before.grid(row=0, column=0, sticky="nsew")
before_frame.rowconfigure(0, weight=1)
before_frame.columnconfigure(0, weight=1)

canvas_after = tk.Canvas(after_frame, width=700, height=220, bg="white")
canvas_after.grid(row=0, column=0, sticky="nsew")
after_frame.rowconfigure(0, weight=1)
after_frame.columnconfigure(0, weight=1)

canvas_combined = tk.Canvas(combined_frame, width=700, height=220, bg="white")
canvas_combined.grid(row=0, column=0, sticky="nsew")
combined_frame.rowconfigure(0, weight=1)
combined_frame.columnconfigure(0, weight=1)

canvas_price = tk.Canvas(price_frame, width=500, height=220, bg="white")
canvas_price.grid(row=0, column=0, sticky="nsew")
price_frame.rowconfigure(0, weight=1)
price_frame.columnconfigure(0, weight=1)


def _canvas_size(canvas):
    """Actual rendered size (winfo_*) falls back to configured size at start-up."""
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w < 50:
        w = int(canvas["width"])
    if h < 50:
        h = int(canvas["height"])
    return w, h


def get_y_scaling_params():
    """Y-axis upper bound rounded up to the next multiple of 25."""
    max_val_data = max(max(before_load), max(after_load))
    if max_val_data <= 0:
        return 25
    return max(25, 25 * math.ceil(max_val_data / 25.0))


def draw_single_graph(canvas, load, title, line_color=COLOR_BEFORE_LINE):
    canvas.delete("all")
    w, h = _canvas_size(canvas)
    margin = 40
    usable_height = h - 2 * margin
    if usable_height <= 0:
        return

    max_tick = get_y_scaling_params()
    x_span = w - 2 * margin
    x_step = x_span / 24.0

    for y_val in range(25, max_tick + 1, 25):
        y = h - margin - (y_val / max_tick) * usable_height
        canvas.create_line(margin, y, w - margin, y, fill=COLOR_GRID)

    canvas.create_line(margin, h - margin, w - margin, h - margin)
    canvas.create_line(margin, margin, margin, h - margin)
    canvas.create_text(w / 2, margin / 2, text=title, font=(APP_FONT, 11, "bold"))

    for hour_label in range(0, 25):
        x = margin + hour_label * x_step
        canvas.create_line(x, h - margin, x, h - margin + 5)
        canvas.create_text(x, h - margin + 15, text=str(hour_label), font=(APP_FONT, 8))

    for y_val in range(0, max_tick + 1, 25):
        y = h - margin - (y_val / max_tick) * usable_height
        canvas.create_line(margin - 5, y, margin, y)
        canvas.create_text(margin - 30, y, text=str(y_val), font=(APP_FONT, 8))

    pts = []
    for k in range(0, 25):
        idx = k % NUM_HOURS
        x = margin + k * x_step
        y = h - margin - (load[idx] / max_tick) * usable_height
        pts.extend([x, y])
    canvas.create_line(*pts, fill=line_color, width=2)


def draw_combined_graph():
    canvas = canvas_combined
    canvas.delete("all")
    w, h = _canvas_size(canvas)
    margin = 40
    usable_height = h - 2 * margin
    if usable_height <= 0:
        return

    max_tick = get_y_scaling_params()
    x_span = w - 2 * margin
    x_step = x_span / 24.0

    for y_val in range(25, max_tick + 1, 25):
        y = h - margin - (y_val / max_tick) * usable_height
        canvas.create_line(margin, y, w - margin, y, fill=COLOR_GRID)

    canvas.create_line(margin, h - margin, w - margin, h - margin)
    canvas.create_line(margin, margin, margin, h - margin)
    canvas.create_text(w / 2, margin / 2, text="Comparison", font=(APP_FONT, 11, "bold"))

    for hour_label in range(0, 25):
        x = margin + hour_label * x_step
        canvas.create_line(x, h - margin, x, h - margin + 5)
        canvas.create_text(x, h - margin + 15, text=str(hour_label), font=(APP_FONT, 8))

    for y_val in range(0, max_tick + 1, 25):
        y = h - margin - (y_val / max_tick) * usable_height
        canvas.create_line(margin - 5, y, margin, y)
        canvas.create_text(margin - 30, y, text=str(y_val), font=(APP_FONT, 8))

    def to_pts(load):
        pts = []
        for k in range(0, 25):
            idx = k % NUM_HOURS
            x = margin + k * x_step
            y = h - margin - (load[idx] / max_tick) * usable_height
            pts.extend([x, y])
        return pts

    canvas.create_line(*to_pts(before_load), fill=COLOR_BEFORE_LINE, width=2)
    canvas.create_line(*to_pts(after_load), fill=COLOR_AFTER_LINE, width=2, dash=(4, 2))

    legend_y1 = margin / 2
    legend_y2 = legend_y1 + 20
    legend_x_line = w - 200
    legend_x_text = legend_x_line + 40

    canvas.create_line(legend_x_line, legend_y1, legend_x_line + 30, legend_y1,
                       fill=COLOR_BEFORE_LINE, width=2)
    canvas.create_text(legend_x_text, legend_y1, text="Before",
                       anchor="w", font=(APP_FONT, 9))
    canvas.create_line(legend_x_line, legend_y2, legend_x_line + 30, legend_y2,
                       fill=COLOR_AFTER_LINE, width=2, dash=(4, 2))
    canvas.create_text(legend_x_text, legend_y2, text="After",
                       anchor="w", font=(APP_FONT, 9))


def draw_price_graph():
    canvas = canvas_price
    canvas.delete("all")
    w, h = _canvas_size(canvas)
    margin = 40
    usable_height = h - 2 * margin
    if usable_height <= 0:
        return

    min_price_scale = 0.0
    max_price_scale = 25.0
    price_range = max_price_scale - min_price_scale
    x_span = w - 2 * margin
    x_step = x_span / 24.0

    for price_val in range(5, 26, 5):
        frac = (price_val - min_price_scale) / price_range
        y = h - margin - frac * usable_height
        canvas.create_line(margin, y, w - margin, y, fill=COLOR_GRID)

    canvas.create_line(margin, h - margin, w - margin, h - margin)
    canvas.create_line(margin, margin, margin, h - margin)
    canvas.create_text(w / 2, margin / 2, text="Price (cents/kWh)",
                       font=(APP_FONT, 11, "bold"))

    for hour_label in range(0, 25):
        x = margin + hour_label * x_step
        canvas.create_line(x, h - margin, x, h - margin + 5)
        canvas.create_text(x, h - margin + 15, text=str(hour_label), font=(APP_FONT, 8))

    for price_val in range(0, 26, 5):
        frac = (price_val - min_price_scale) / price_range
        y = h - margin - frac * usable_height
        canvas.create_line(margin - 5, y, margin, y)
        canvas.create_text(margin - 10, y, text=str(price_val),
                           font=(APP_FONT, 8), anchor="e")

    pts_price = []
    for k in range(0, 25):
        idx = k % NUM_HOURS
        pv = max(min_price_scale, min(max_price_scale, PRICE_PER_HOUR[idx]))
        norm = (pv - min_price_scale) / price_range
        x = margin + k * x_step
        y = h - margin - norm * usable_height
        pts_price.extend([x, y])
    canvas.create_line(*pts_price, fill=COLOR_PRICE_LINE, width=2)


def draw_graphs():
    draw_single_graph(canvas_before, before_load,
                      "Total demand BEFORE flexibility", COLOR_BEFORE_LINE)
    draw_single_graph(canvas_after, after_load,
                      "Total demand AFTER flexibility", COLOR_AFTER_LINE)
    draw_combined_graph()
    draw_price_graph()


def update_stats_and_graph():
    peak_b = max(before_load)
    peak_a = max(after_load)
    reduction = peak_b - peak_a
    reduction_pct = (reduction / peak_b * 100) if peak_b > 0 else 0.0

    peak_before_var.set(f"{peak_b:.1f} units")
    peak_after_var.set(f"{peak_a:.1f} units")
    reduction_var.set(f"{reduction:.1f} units ({reduction_pct:.1f}%)")

    cost_b_eur = cost_before_flex / 100.0
    cost_a_eur = cost_after_flex / 100.0
    saving_eur = cost_b_eur - cost_a_eur
    saving_pct = (saving_eur / cost_b_eur * 100) if cost_b_eur > 0 else 0.0

    cost_before_var.set(f"{cost_b_eur:.2f} EUR")
    cost_after_var.set(f"{cost_a_eur:.2f} EUR")
    saving_cost_var.set(f"{saving_eur:.2f} EUR ({saving_pct:.1f}%)")

    # CO2_PER_HOUR is in kg/kWh; load is in kW; 1h interval -> emissions in kg.
    # Saving % is over asset-only emissions so it's comparable to cost % (also
    # asset-only). Using city-total emissions as the denominator would dilute
    # the saving with the un-shiftable BASE_LOAD portion and understate it.
    asset_emissions_before = sum(
        (before_load[h] - BASE_LOAD[h]) * CO2_PER_HOUR[h] for h in range(NUM_HOURS)
    )
    asset_emissions_after = sum(
        (after_load[h] - BASE_LOAD[h]) * CO2_PER_HOUR[h] for h in range(NUM_HOURS)
    )
    saving_kg_day = asset_emissions_before - asset_emissions_after
    saving_pct_co2 = (
        saving_kg_day / asset_emissions_before * 100
        if asset_emissions_before > 0 else 0.0
    )
    saving_t_year = saving_kg_day * 365.0 / 1000.0
    co2_var.set(
        f"{saving_kg_day:.1f} kg/day ({saving_pct_co2:.1f}%) "
        f"~ {saving_t_year:.1f} tCO2/year"
    )

    draw_graphs()


# Redraw graphs when canvases are resized.
# Debounced because each of the 4 canvases fires <Configure> on every
# window resize tick - without coalescing we'd redraw ~16 times per tick.
def _on_canvas_configure(event):
    if root.after_id_redraw:
        root.after_cancel(root.after_id_redraw)
    root.after_id_redraw = root.after(50, draw_graphs)


for c in (canvas_before, canvas_after, canvas_combined, canvas_price):
    c.bind("<Configure>", _on_canvas_configure)


recalculate_schedules()
update_stats_and_graph()

root.mainloop()
