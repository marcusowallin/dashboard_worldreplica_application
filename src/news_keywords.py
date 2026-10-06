"""Cheap, deterministic news filtering before any AI call (decision 1 Oct 2026, D8b).

Matching rule (a headline passes if ANY of these holds):
  1. it names one of the three groups or a subsidiary (AIRLINE_TERMS), or
  2. it contains an aviation-fuel term (FUEL_STRONG) - industry-wide by definition, or
  3. it contains a general market / cost / disruption term (GENERAL_TERMS) AND an aviation context word
     (AVIATION_CONTEXT) - so 'Brent rises' passes only as 'Brent rises, airlines ...'.
Terms are matched case-insensitively on word boundaries; English, German and French variants included because
GDELT carries all three. Also: outlet names from domains, and de-duplication across sources ("also reported by").
"""
import re

AIRLINE_TERMS = (
    "Lufthansa", "SWISS International", "Swiss Air Lines", "Austrian Airlines", "Brussels Airlines", "ITA Airways",
    "Eurowings", "Discover Airlines", "Air France", "KLM", "Transavia", "IAG", "International Airlines Group",
    "British Airways", "Iberia", "Aer Lingus", "Vueling", "LEVEL",
)
FUEL_STRONG = (
    "jet fuel", "kerosene", "aviation fuel", "jet fuel price", "crack spread", "jet crack", "fuel hedge",
    "fuel hedging", "fuel surcharge", "fuel bill", "SAF mandate", "sustainable aviation fuel",
    # German / French
    "Kerosin", "Kerosinpreis", "Treibstoffzuschlag", "Kerosinzuschlag", "Flugbenzin", "kérosène",
    "carburant aviation", "surcharge carburant", "surcharge kérosène",
)
GENERAL_TERMS = (
    "refinery outage", "refining margin", "Brent", "oil price", "oil prices", "crude", "OPEC", "diesel", "gasoil",
    "hedging", "profit warning", "guidance", "outlook", "earnings", "results", "ticket prices", "airfares", "fares",
    "yields", "demand", "capacity cut", "cancellations", "cancelled flights", "strike", "airspace closure",
    "airspace", "rerouting", "Middle East", "Iran", "Strait of Hormuz", "Red Sea", "EU ETS", "carbon price",
    "emissions", "euro dollar", "EUR/USD", "Ölpreis", "Streik", "Luftraum", "prix du pétrole", "grève",
    "espace aérien",
)
AVIATION_CONTEXT = (
    "airline", "airlines", "aviation", "flight", "flights", "carrier", "carriers", "air travel", "airport",
    "airports", "jet", "aircraft", "Fluggesellschaft", "Airline", "Luftfahrt", "Flüge", "compagnie aérienne",
    "compagnies aériennes", "aérien", "vols",
) + AIRLINE_TERMS

# Phrases that contain an airline name but are not about it (place names etc.) - checked before the rule above.
EXCLUDE_TERMS = ("New Iberia", "Iberia Parish")

OUTLETS = {
    "reuters.com": "Reuters", "bloomberg.com": "Bloomberg", "ft.com": "Financial Times", "wsj.com": "WSJ",
    "handelsblatt.com": "Handelsblatt", "lesechos.fr": "Les Echos", "bbc.co.uk": "BBC", "bbc.com": "BBC",
    "cnbc.com": "CNBC", "theguardian.com": "The Guardian", "nytimes.com": "New York Times", "faz.net": "FAZ",
    "spiegel.de": "Der Spiegel", "lefigaro.fr": "Le Figaro", "lemonde.fr": "Le Monde", "apnews.com": "AP",
    "afr.com": "AFR", "economist.com": "The Economist", "telegraph.co.uk": "The Telegraph", "dw.com": "DW",
    "aviationweek.com": "Aviation Week", "flightglobal.com": "FlightGlobal", "simpleflying.com": "Simple Flying",
    "aerotime.aero": "AeroTime", "skift.com": "Skift", "airlineweekly.com": "Airline Weekly",
    "argusmedia.com": "Argus", "spglobal.com": "S&P Global", "marketscreener.com": "MarketScreener",
    "cnn.com": "CNN", "cbsnews.com": "CBS News", "nbcnews.com": "NBC News", "npr.org": "NPR",
    "washingtonpost.com": "Washington Post", "fortune.com": "Fortune", "forbes.com": "Forbes", "axios.com": "Axios",
    "finance.yahoo.com": "Yahoo Finance", "investing.com": "Investing.com", "morningstar.com": "Morningstar",
    "morningstar.co.uk": "Morningstar UK", "nasdaq.com": "Nasdaq", "oilprice.com": "OilPrice.com",
    "rigzone.com": "Rigzone", "cityam.com": "City AM", "proactiveinvestors.co.uk": "Proactive Investors",
    "lse.co.uk": "London South East", "businesstraveller.com": "Business Traveller",
}
# 'Search the web' is limited to these outlets. Every domain was accepted by Anthropic's web search on 6 Oct 2026
# (the API rejects the whole request if one listed domain blocks its crawler: Reuters, FT, WSJ, BBC, Les Echos do).
# US / UK business, energy and aviation press first; sources the Method page rules out on terms of use are not listed.
WEB_DOMAINS = (
    "bloomberg.com", "cnbc.com", "cnn.com", "cbsnews.com", "nbcnews.com", "npr.org", "washingtonpost.com",
    "fortune.com", "forbes.com", "axios.com", "finance.yahoo.com", "investing.com", "marketscreener.com",
    "morningstar.com", "morningstar.co.uk", "nasdaq.com", "oilprice.com", "rigzone.com", "argusmedia.com",
    "spglobal.com", "flightglobal.com", "cityam.com", "proactiveinvestors.co.uk", "lse.co.uk",
    "businesstraveller.com", "handelsblatt.com",
)
MAJOR_OUTLETS = tuple(OUTLETS[d] for d in WEB_DOMAINS)


def _pattern(terms):
    return re.compile(r"(?<!\w)(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")(?!\w)",
                      re.IGNORECASE)


_AIRLINE, _STRONG = _pattern(AIRLINE_TERMS), _pattern(FUEL_STRONG)
_GENERAL, _CONTEXT = _pattern(GENERAL_TERMS), _pattern(AVIATION_CONTEXT)
_EXCLUDE = _pattern(EXCLUDE_TERMS)


def match_reason(title):
    """Why a headline passes the filter ('airline' / 'fuel' / 'general+aviation'), or None if it does not.

    Excluded phrases (EXCLUDE_TERMS, e.g. the town 'New Iberia') are removed before matching.
    """
    title = _EXCLUDE.sub(" ", title)
    if _AIRLINE.search(title):
        return "airline"
    if _STRONG.search(title):
        return "fuel"
    if _GENERAL.search(title) and _CONTEXT.search(title):
        return "general+aviation"
    return None


def keep(headlines):
    """Headlines that pass the keyword rule, each with its 'match' reason (no AI involved)."""
    out = []
    for h in headlines:
        reason = match_reason(h.get("title") or "")
        if reason:
            out.append({**h, "match": reason})
    return out


def outlet_name(domain):
    """'www.reuters.com' -> 'Reuters'; unknown domains are shown as the bare domain."""
    d = (domain or "").lower().removeprefix("www.")
    for known, name in OUTLETS.items():
        if d == known or d.endswith("." + known):
            return name
    return d or "unknown source"


def story_key(title):
    """Loose key for 'the same story from several outlets': lower case, letters and digits only, first 8 words
    without short filler words."""
    words = [w for w in re.findall(r"[a-z0-9äöüéèàç]+", (title or "").lower()) if len(w) > 2]
    return " ".join(words[:8])


def merge_sources(headlines):
    """One entry per story, in first-seen order; the others' outlets go to 'also_reported_by'."""
    merged, index = [], {}
    for h in headlines:
        key = story_key(h.get("title"))
        outlet = outlet_name(h.get("domain"))
        if key in index:
            first = merged[index[key]]
            if outlet != first["outlet"] and outlet not in first["also_reported_by"]:
                first["also_reported_by"].append(outlet)
            continue
        index[key] = len(merged)
        merged.append({**h, "outlet": outlet, "also_reported_by": []})
    return merged
