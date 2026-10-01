# How to label `labelled_headlines.csv`

22 real headlines (collected 30 Sep 2026). Fill the six `label_*` columns for each row **from the headline text
only** (don't open the article - the AI sees only the headline too). Leave nothing out; when a row is not relevant,
fill only `label_relevant = no`. Save as CSV (UTF-8). Then run the report (bottom).

| Column | Allowed values | How to decide |
|---|---|---|
| `label_relevant` | `yes` / `no` | `yes` if the headline is about airline fuel costs, fuel or crude prices, hedging, fares or surcharges, capacity, profit guidance, airspace or other disruption for at least one of the three groups - or about jet fuel / crude prices in general. Otherwise `no`. |
| `label_airlines` | `lufthansa`, `afklm`, `iag` - several separated by `;` | Which **groups** the headline concerns. Subsidiaries count: SWISS, Austrian, Brussels, ITA, Eurowings -> `lufthansa`; Air France, KLM, Transavia -> `afklm`; British Airways, Iberia, Aer Lingus, Vueling, LEVEL -> `iag`. **Industry-wide** headlines (jet fuel or oil prices, airspace for European carriers) concern **all three**: `lufthansa;afklm;iag` (changed 1 Oct 2026, D8b). Leave empty only when the headline is not relevant. |
| `label_driver` | one of the 8 below | The **main** topic. |
| `label_direction` | `cost_up`, `cost_down`, `unclear` | Effect on the airline's **costs** (not profit, not share price). Use `unclear` when the headline does not say. |
| `label_severity` | `1`, `2`, `3` | 1 minor (routine), 2 notable, 3 major for the airlines' costs or profits (e.g. a profit warning, a large fuel cost hit). |
| `label_impact` | `airline:impact` pairs separated by `;` - impact = `positive`, `negative` or `neutral` | For **each** airline in `label_airlines`: is the headline likely good (`positive`) or bad (`negative`) for **that airline's earnings** - through fuel cost, the jet premium, hedging, pass-through, capacity, guidance or disruption? `neutral` when unclear. Judge from the airline's own view; a competitor's problem is **not** positive for another airline (don't add knock-on effects). Example: `lufthansa:negative;afklm:negative;iag:negative` for "Jet fuel hits two-year high". |

**Drivers** (each maps to a step of the page):

| Value | Use for | Example | Step |
|---|---|---|---|
| `fuel_price` | crude oil or jet fuel price moves | "Jet fuel hits two-year high" | 1 |
| `jet_premium` | jet premium over crude, refining margins, refinery outages, jet fuel supply | "Refinery outage widens jet fuel crack" | 2 |
| `hedging` | fuel hedges, hedge ratios, hedging gains or losses | "Lufthansa raises 2027 fuel hedge to 50%" | 3 |
| `capacity` | flights, seats, routes or fleet added or cut | "KLM cuts winter flights" | 4 |
| `pass_through` | fares, fuel surcharges, ticket prices, passing costs to passengers | "British Airways adds fuel surcharge" | 5 |
| `guidance` | profit outlook, earnings, cost guidance | "IAG keeps full-year margin target" | 6 |
| `disruption` | airspace closures, strikes, outages, groundings | "Pilots strike at Air France" | 7 |
| `other` | anything else | | - |

If two drivers fit, pick the one the headline leads with (e.g. "Lufthansa warns fuel bill will top EUR 1.5bn" ->
`guidance`, because it is a company outlook statement; "Jet fuel jumps 8% as refineries shut" -> `jet_premium`).

## Run the agreement report

```bash
.venv/bin/python scripts/evaluate_tagger.py
```

It needs `ANTHROPIC_API_KEY` in `.streamlit/secrets.toml` (read, never printed). It first checks your labels against
the allowed values and stops with a list if any are off. Then one API call (Claude Haiku, a few cents at most) tags
all 22 headlines and prints agreement per field (relevant, airlines, driver, direction, severity, impact), agreement by
driver, and how many quotes were found word for word. Tags are saved to `data/labelled_headlines_tags.json`.
