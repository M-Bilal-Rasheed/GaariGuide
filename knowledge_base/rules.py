"""
KNOWLEDGE BASE - questions and IF-THEN rules of GaariGuide.

Two kinds of production rules are used:

  REQUIRE rule (hard constraint, used for DECISION MAKING)
      IF <user answer> THEN keep only cars where <condition>
      -> cars failing the condition are ELIMINATED.

  SCORE rule (soft preference, used for DECISION SUPPORT / ranking)
      IF <user answer> AND <car condition> THEN add +/- N points
      -> the car's match score goes up or down.

Every question in the bank owns one or more rules. The inference engine
(app.py) fires the rules of each answered question.
"""

from dataclasses import dataclass
from typing import Callable, Optional

SKIP = "skip"   # every question gets an "I'm not sure / skip" option


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    text: str
    options: tuple                      # ((key, label), ...)
    depends: Optional[Callable] = None  # answers(dict) -> bool : ask only if True
    help: str = ""

    def label(self, key: str) -> str:
        if key == SKIP:
            return "Not sure / skip"
        return dict(self.options).get(key, key)


@dataclass(frozen=True)
class Rule:
    id: str
    qid: str
    answers: frozenset       # rule fires when the user's answer is one of these
    kind: str                # "require" | "score"
    cond: str                # human readable car condition
    test: Callable           # car -> bool
    points: int = 0          # for score rules

    def describe(self, questions_by_id) -> str:
        q = questions_by_id[self.qid]
        ans = " / ".join(q.label(a) for a in sorted(self.answers))
        name = self.qid.replace("_", " ")
        if self.kind == "require":
            return f"IF {name} = '{ans}' THEN keep only cars where {self.cond}"
        sign = "+" if self.points > 0 else ""
        return f"IF {name} = '{ans}' AND car {self.cond} THEN score {sign}{self.points}"


QUESTIONS: list = []
RULES: list = []


def _q(id, category, text, options, depends=None, help=""):
    QUESTIONS.append(Question(id, category, text, tuple(options), depends, help))


def _require(qid, answers, cond, test):
    RULES.append(Rule(f"R{len(RULES) + 1:03d}", qid, frozenset(answers), "require", cond, test))


def _score(qid, answers, points, cond, test):
    RULES.append(Rule(f"R{len(RULES) + 1:03d}", qid, frozenset(answers), "score", cond, test, points))


# =========================================================================
# 1. BUDGET & FINANCE
# =========================================================================
_q("budget", "Budget & finance", "What is your total budget for the car?",
   [("u25", "Under 25 lakh"), ("b25_40", "25 - 40 lakh"), ("b40_60", "40 - 60 lakh"),
    ("b60_90", "60 - 90 lakh"), ("b90_130", "90 lakh - 1.3 crore"), ("b130", "Above 1.3 crore")],
   help="Approximate on-road budget in Pakistani rupees.")
BUDGETS = {"u25": (0, 25), "b25_40": (25, 40), "b40_60": (40, 60),
           "b60_90": (60, 90), "b90_130": (90, 130), "b130": (130, 400)}
for key, (lo, hi) in BUDGETS.items():
    _require("budget", [key], f"price <= {hi * 1.05:.0f} lakh (budget + 5%)",
             lambda c, hi=hi: c.price <= hi * 1.05)
    _score("budget", [key], 3, f"price is between {lo} and {hi} lakh",
           lambda c, lo=lo, hi=hi: lo <= c.price <= hi)
    if lo > 0:
        _score("budget", [key], -3, f"price is far below budget (< {lo * 0.6:.0f} lakh)",
               lambda c, lo=lo: c.price < lo * 0.6)

_q("payment", "Budget & finance", "How will you pay for the car?",
   [("cash", "Full cash"), ("lease", "Bank financing / car lease"), ("install", "Company installments")])
_score("payment", ["lease", "install"], 2, "is new (banks finance new cars easily)", lambda c: c.condition == "new")
_score("payment", ["lease"], -3, "is a used import (hard to finance)",
       lambda c: c.condition == "used" and c.origin == "imported")

_q("fuel_budget", "Budget & finance", "What is your monthly fuel budget?",
   [("low", "Tight (under Rs 25,000)"), ("mid", "Moderate"), ("high", "Not a concern")])
_score("fuel_budget", ["low"], 3, "is economical (18+ km/l or electrified)", lambda c: c.economical)
_score("fuel_budget", ["low"], -3, "is thirsty (under 12 km/l)", lambda c: not c.electrified and c.kmpl < 12)
_score("fuel_budget", ["mid"], 1, "gives 14+ km/l or is electrified", lambda c: c.electrified or c.kmpl >= 14)

_q("maint_budget", "Budget & finance", "What is your yearly maintenance budget?",
   [("low", "Low - keep it cheap"), ("mid", "Average"), ("high", "Not a concern")])
_score("maint_budget", ["low"], 2, "has cheap maintenance (rating <= 2)", lambda c: c.maint <= 2)
_score("maint_budget", ["low"], -3, "has costly maintenance (rating >= 4)", lambda c: c.maint >= 4)
_score("maint_budget", ["mid"], -1, "has costly maintenance (rating >= 4)", lambda c: c.maint >= 4)

_q("token_tax", "Budget & finance", "Are yearly token tax and registration costs a concern for you?",
   [("yes", "Yes, keep them low"), ("no", "No")])
_score("token_tax", ["yes"], 2, "has an engine of 1300cc or less", lambda c: c.cc <= 1300)
_score("token_tax", ["yes"], -2, "has an engine above 2000cc", lambda c: c.cc > 2000)

# =========================================================================
# 2. FAMILY & SPACE
# =========================================================================
_q("passengers", "Family & space", "How many people usually travel in the car (including the driver)?",
   [("p1_2", "1 - 2"), ("p3_4", "3 - 4"), ("p5", "5"), ("p6_7", "6 - 7")])
_require("passengers", ["p3_4"], "seats >= 4", lambda c: c.seats >= 4)
_require("passengers", ["p5"], "seats >= 5", lambda c: c.seats >= 5)
_require("passengers", ["p6_7"], "seats >= 7", lambda c: c.seats >= 7)
_score("passengers", ["p1_2"], 2, "is a small car", lambda c: c.size == "small")

_q("kids", "Family & space", "Do you have young children who will travel with you?",
   [("yes", "Yes"), ("no", "No")])
_score("kids", ["yes"], 2, "has at least 2 airbags", lambda c: c.airbags >= 2)
_score("kids", ["yes"], 1, "has 4 or more seats with ISOFIX", lambda c: c.isofix and c.seats >= 4)

_q("baby_seat", "Family & space", "Do you need to fit a baby car seat (ISOFIX anchors)?",
   [("yes", "Yes"), ("no", "No")], depends=lambda a: a.get("kids") == "yes")
_score("baby_seat", ["yes"], 3, "has ISOFIX anchors", lambda c: c.isofix)

_q("elderly", "Family & space", "Will elderly family members ride in the car often?",
   [("yes", "Yes"), ("no", "No")])
_score("elderly", ["yes"], 2, "is an SUV/MPV with easy entry (clearance >= 170 mm)",
       lambda c: c.body in ("suv", "mpv") and c.clearance >= 170)
_score("elderly", ["yes"], 1, "has high comfort (rating >= 4)", lambda c: c.comfort >= 4)
_score("elderly", ["yes"], -2, "is a small cramped car", lambda c: c.size == "small" and c.comfort <= 1)

_q("luggage", "Family & space", "How much luggage do you usually carry?",
   [("small", "Very little"), ("medium", "A few bags"), ("large", "A lot (family trips, shopping)")])
_score("luggage", ["large"], 3, "has a big boot (450+ litres)", lambda c: c.boot >= 450)
_score("luggage", ["large"], -3, "has a tiny boot (under 250 litres)", lambda c: c.boot < 250)
_score("luggage", ["medium"], 1, "has a boot of 300+ litres", lambda c: c.boot >= 300)

_q("cargo", "Family & space", "Will you carry goods or cargo for business?",
   [("yes", "Yes"), ("no", "No")])
_score("cargo", ["yes"], 4, "is practical for cargo", lambda c: c.cargo)
_score("cargo", ["no"], -2, "is a pickup or van built for cargo", lambda c: c.cargo)

_q("rear_comfort", "Family & space", "Will you mostly sit in the back seat (driver-driven car)?",
   [("yes", "Yes"), ("no", "No, I will drive")])
_score("rear_comfort", ["yes"], 3, "is a comfortable sedan/SUV (comfort >= 4)",
       lambda c: c.comfort >= 4 and c.body in ("sedan", "suv"))
_score("rear_comfort", ["yes"], -2, "is a small car", lambda c: c.size == "small")

# =========================================================================
# 3. USAGE
# =========================================================================
_q("main_use", "Usage", "Where will you drive the car most of the time?",
   [("city", "Inside the city"), ("highway", "Mostly highways / intercity"), ("mixed", "Both equally")])
_score("main_use", ["city"], 2, "is small or medium sized", lambda c: c.size in ("small", "medium"))
_score("main_use", ["city"], 1, "is available in automatic", lambda c: c.has_auto)
_score("main_use", ["highway"], 2, "has 1300cc+ or is electric", lambda c: c.cc >= 1300 or c.fuel == "ev")
_score("main_use", ["highway"], -2, "has an engine under 1000cc", lambda c: 0 < c.cc < 1000)
_score("main_use", ["mixed"], 1, "has a 1000-1800cc engine", lambda c: 1000 <= c.cc <= 1800)

_q("daily_km", "Usage", "How many kilometres do you drive daily?",
   [("lt20", "Less than 20 km"), ("k20_60", "20 - 60 km"), ("gt60", "More than 60 km")])
_score("daily_km", ["gt60"], 3, "is economical (18+ km/l or electrified)", lambda c: c.economical)
_score("daily_km", ["gt60"], 1, "is comfortable (rating >= 3)", lambda c: c.comfort >= 3)
_score("daily_km", ["k20_60"], 1, "gives 15+ km/l or is electrified", lambda c: c.electrified or c.kmpl >= 15)

_q("ride_hailing", "Usage", "Will you use the car for Careem / InDrive / Yango?",
   [("yes", "Yes"), ("no", "No")])
_require("ride_hailing", ["yes"], "4+ seats and a passenger body (not a pickup)",
         lambda c: c.seats >= 4 and c.body != "pickup")
_score("ride_hailing", ["yes"], 3, "has cheap parts & maintenance", lambda c: c.parts >= 4 and c.maint <= 2)
_score("ride_hailing", ["yes"], 2, "is economical", lambda c: c.economical)
_score("ride_hailing", ["yes"], -3, "costs over 70 lakh", lambda c: c.price > 70)

_q("long_trips", "Usage", "Do you often take long intercity trips (e.g. Lahore - Islamabad)?",
   [("yes", "Yes"), ("no", "No")])
_score("long_trips", ["yes"], 2, "has a 1300cc+ engine", lambda c: c.cc >= 1300)
_score("long_trips", ["yes"], 2, "has cruise control", lambda c: c.cruise)
_score("long_trips", ["yes"], -2, "is fully electric (few highway chargers)", lambda c: c.fuel == "ev")
_score("long_trips", ["yes"], -2, "has an 800cc or smaller engine", lambda c: 0 < c.cc <= 800)

_q("motorway", "Usage", "Do you often drive at high speed on motorways?",
   [("yes", "Yes"), ("no", "No")])
_score("motorway", ["yes"], 2, "has good power (rating >= 3)", lambda c: c.power >= 3)
_score("motorway", ["yes"], 1, "has 4 or more airbags", lambda c: c.airbags >= 4)
_score("motorway", ["yes"], -3, "has an 800cc or smaller engine", lambda c: 0 < c.cc <= 800)

_q("traffic", "Usage", "Do you face heavy stop-and-go traffic every day?",
   [("yes", "Yes"), ("no", "No")])
_score("traffic", ["yes"], 2, "is available in automatic", lambda c: c.has_auto)
_score("traffic", ["yes"], 2, "is hybrid or electric (saves fuel in traffic)", lambda c: c.electrified)
_score("traffic", ["yes"], 1, "is small", lambda c: c.size == "small")

_q("shared_drivers", "Usage", "Will several family members drive this car?",
   [("yes", "Yes"), ("no", "No, mostly me")])
_score("shared_drivers", ["yes"], 2, "is available in automatic", lambda c: c.has_auto)
_score("shared_drivers", ["yes"], 1, "has a reverse camera", lambda c: c.camera)

# =========================================================================
# 4. ROADS & LOCATION
# =========================================================================
_q("terrain", "Roads & location", "Which kind of area do you live / drive in?",
   [("plains", "Plain cities (Lahore, Karachi, Multan...)"),
    ("north", "Hilly / northern areas (Murree, Swat, Gilgit...)"),
    ("desert", "Desert / rural (Thar, Balochistan...)")])
_score("terrain", ["north"], 3, "has good power or 4WD", lambda c: c.power >= 3 or c.drive == "4wd")
_score("terrain", ["north"], 2, "has high ground clearance (180+ mm)", lambda c: c.clearance >= 180)
_score("terrain", ["north"], -3, "has an 800cc or smaller engine", lambda c: 0 < c.cc <= 800)
_score("terrain", ["desert"], 3, "has high ground clearance (180+ mm)", lambda c: c.clearance >= 180)
_score("terrain", ["desert"], 2, "has 4WD", lambda c: c.drive == "4wd")
_score("terrain", ["desert"], -2, "has low ground clearance (under 150 mm)", lambda c: c.clearance < 150)
_score("terrain", ["plains"], 1, "gives 15+ km/l or is electrified", lambda c: c.electrified or c.kmpl >= 15)

_q("rough_roads", "Roads & location", "How often do you drive on broken or unpaved roads?",
   [("often", "Often"), ("sometimes", "Sometimes"), ("never", "Rarely / never")])
_score("rough_roads", ["often"], 3, "has high ground clearance (180+ mm)", lambda c: c.clearance >= 180)
_score("rough_roads", ["often"], -3, "has low ground clearance (under 150 mm)", lambda c: c.clearance < 150)
_score("rough_roads", ["sometimes"], 1, "has 165+ mm ground clearance", lambda c: c.clearance >= 165)

_q("flooding", "Roads & location", "Do roads in your area flood during monsoon rains?",
   [("yes", "Yes"), ("no", "No")])
_score("flooding", ["yes"], 2, "has high ground clearance (180+ mm)", lambda c: c.clearance >= 180)
_score("flooding", ["yes"], -2, "has low ground clearance (under 150 mm)", lambda c: c.clearance < 150)
_score("flooding", ["yes"], -2, "is fully electric (battery & water risk)", lambda c: c.fuel == "ev")

_q("narrow", "Roads & location", "Are the streets in your area narrow or crowded?",
   [("yes", "Yes"), ("no", "No")])
_score("narrow", ["yes"], 3, "is a small car", lambda c: c.size == "small")
_score("narrow", ["yes"], -3, "is a large car", lambda c: c.size == "large")

_q("parking", "Roads & location", "Where will the car usually be parked?",
   [("garage", "Own garage / porch"), ("street", "On the street"), ("apartment", "Apartment / shared parking")])
_score("parking", ["street", "apartment"], 1, "is small (easy to park)", lambda c: c.size == "small")
_score("parking", ["street", "apartment"], -2, "is a large car", lambda c: c.size == "large")

_q("home_charging", "Roads & location", "Can you install a charger at home (for electric / plug-in cars)?",
   [("yes", "Yes"), ("no", "No")])
_score("home_charging", ["yes"], 2, "is electric or plug-in hybrid", lambda c: c.fuel in ("ev", "phev"))
_require("home_charging", ["no"], "the car is not fully electric", lambda c: c.fuel != "ev")
_score("home_charging", ["no"], -3, "is a plug-in hybrid", lambda c: c.fuel == "phev")

_q("heat", "Roads & location", "Do you live in a very hot city with heavy AC use?",
   [("yes", "Yes"), ("no", "No")])
_score("heat", ["yes"], -2, "has an 800cc or smaller engine (AC drains power)", lambda c: 0 < c.cc <= 800)
_score("heat", ["yes"], 1, "has automatic climate control", lambda c: c.climate)

_q("village", "Roads & location", "Do you often visit villages or farmland?",
   [("yes", "Yes"), ("no", "No")])
_score("village", ["yes"], 2, "has high ground clearance (180+ mm)", lambda c: c.clearance >= 180)
_score("village", ["yes"], 2, "is a pickup or cargo vehicle", lambda c: c.cargo)
_score("village", ["yes"], 1, "has parts available everywhere", lambda c: c.parts >= 4)

# =========================================================================
# 5. ENGINE & FUEL
# =========================================================================
_q("fuel", "Engine & fuel", "Which fuel type do you prefer?",
   [("petrol", "Petrol"), ("hybrid", "Hybrid"), ("electric", "Fully electric"),
    ("diesel", "Diesel"), ("any", "No preference")])
_require("fuel", ["petrol"], "fuel is petrol", lambda c: c.fuel == "petrol")
_require("fuel", ["hybrid"], "fuel is hybrid / plug-in hybrid", lambda c: c.fuel in ("hybrid", "phev"))
_require("fuel", ["electric"], "the car is fully electric", lambda c: c.fuel == "ev")
_require("fuel", ["diesel"], "fuel is diesel", lambda c: c.fuel == "diesel")

_q("engine_cc", "Engine & fuel", "Which engine size do you prefer?",
   [("s660", "660 - 800cc"), ("s1000", "1000 - 1300cc"), ("s1300", "1300 - 1600cc"), ("s1800", "1800cc and above")],
   depends=lambda a: a.get("fuel") != "electric")
CC_RANGES = {"s660": (600, 999), "s1000": (1000, 1299), "s1300": (1300, 1699), "s1800": (1700, 5000)}
for key, (lo, hi) in CC_RANGES.items():
    _score("engine_cc", [key], 3, f"engine is {lo}-{hi}cc", lambda c, lo=lo, hi=hi: lo <= c.cc <= hi)
    _score("engine_cc", [key], -2, f"engine is outside {lo}-{hi}cc",
           lambda c, lo=lo, hi=hi: c.cc > 0 and not lo <= c.cc <= hi)

_q("power_eco", "Engine & fuel", "What matters more to you: power or fuel economy?",
   [("power", "Power"), ("balanced", "A balance of both"), ("economy", "Fuel economy")])
_score("power_eco", ["power"], 3, "is powerful (rating >= 4)", lambda c: c.power >= 4)
_score("power_eco", ["power"], -2, "is underpowered (rating 1)", lambda c: c.power <= 1)
_score("power_eco", ["economy"], 3, "is economical (18+ km/l or electrified)", lambda c: c.economical)
_score("power_eco", ["economy"], -2, "is thirsty (under 12 km/l)", lambda c: not c.electrified and c.kmpl < 12)
_score("power_eco", ["balanced"], 1, "has power 2-3 and 14+ km/l",
       lambda c: 2 <= c.power <= 3 and (c.electrified or c.kmpl >= 14))

_q("turbo", "Engine & fuel", "Are you OK with a turbo engine (needs high-octane petrol, costlier upkeep)?",
   [("yes", "Yes"), ("no", "No")])
_score("turbo", ["yes"], 1, "has a turbo engine", lambda c: c.turbo)
_require("turbo", ["no"], "the engine is not turbocharged", lambda c: not c.turbo)

_q("cng", "Engine & fuel", "Do you plan to fit a CNG / LPG kit?",
   [("yes", "Yes"), ("no", "No")])
_require("cng", ["yes"], "it is a non-turbo petrol car (CNG-friendly)",
         lambda c: c.fuel == "petrol" and not c.turbo)
_score("cng", ["yes"], 2, "has a 1300cc or smaller engine", lambda c: 0 < c.cc <= 1300)

_q("eco", "Engine & fuel", "Is low pollution / eco-friendliness important to you?",
   [("yes", "Yes"), ("no", "No")])
_score("eco", ["yes"], 3, "is hybrid or electric", lambda c: c.electrified)
_score("eco", ["yes"], -1, "runs on diesel", lambda c: c.fuel == "diesel")

# =========================================================================
# 6. DRIVING
# =========================================================================
_q("transmission", "Driving", "Do you want a manual or automatic car?",
   [("manual", "Manual"), ("auto", "Automatic"), ("any", "Either is fine")])
_require("transmission", ["manual"], "a manual version is available", lambda c: c.has_manual)
_require("transmission", ["auto"], "an automatic version is available", lambda c: c.has_auto)

_q("first_car", "Driving", "Is this your first car / are you a new driver?",
   [("yes", "Yes"), ("no", "No")])
_score("first_car", ["yes"], 2, "is small and easy to drive", lambda c: c.size == "small")
_score("first_car", ["yes"], 1, "has cheap parts (repairs after small accidents)", lambda c: c.parts >= 4)
_score("first_car", ["yes"], -2, "is very powerful (rating 5)", lambda c: c.power >= 5)
_score("first_car", ["yes"], -1, "is a large car", lambda c: c.size == "large")

_q("sporty", "Driving", "Do you enjoy sporty, fun-to-drive cars?",
   [("yes", "Yes"), ("no", "No")])
_score("sporty", ["yes"], 3, "is powerful (rating >= 4)", lambda c: c.power >= 4)
_score("sporty", ["yes"], 1, "looks stylish (rating >= 4)", lambda c: c.style >= 4)
_score("sporty", ["yes"], -2, "is underpowered (rating 1)", lambda c: c.power <= 1)

_q("high_seat", "Driving", "Do you prefer a high seating position (SUV feel)?",
   [("yes", "Yes"), ("no", "No")])
_score("high_seat", ["yes"], 3, "is an SUV, MPV or pickup", lambda c: c.body in ("suv", "mpv", "pickup"))
_score("high_seat", ["yes"], -1, "is a low sedan", lambda c: c.body == "sedan")
_score("high_seat", ["no"], 1, "is a sedan or hatchback", lambda c: c.body in ("sedan", "hatchback"))

_q("tall", "Driving", "Is the main driver very tall (over 6 feet)?",
   [("yes", "Yes"), ("no", "No")])
_score("tall", ["yes"], -2, "is a small car with a tiny engine (cramped)", lambda c: c.size == "small" and c.cc <= 1000)
_score("tall", ["yes"], 1, "is a large car", lambda c: c.size == "large")

_q("easy_park", "Driving", "Do you find parking difficult?",
   [("yes", "Yes"), ("no", "No")])
_score("easy_park", ["yes"], 2, "has a reverse camera", lambda c: c.camera)
_score("easy_park", ["yes"], 2, "is small", lambda c: c.size == "small")
_score("easy_park", ["yes"], -1, "is a large car", lambda c: c.size == "large")

# =========================================================================
# 7. OWNERSHIP
# =========================================================================
_q("condition", "Ownership", "Do you want a new or a used car?",
   [("new", "New"), ("used", "Used"), ("either", "Either")])
_require("condition", ["new"], "the car is new", lambda c: c.condition == "new")
_require("condition", ["used"], "the car is used", lambda c: c.condition == "used")

_q("keep_years", "Ownership", "How long will you keep the car?",
   [("short", "Less than 3 years"), ("mid", "3 - 7 years"), ("long", "More than 7 years")])
_score("keep_years", ["short"], 3, "has strong resale value (rating >= 4)", lambda c: c.resale >= 4)
_score("keep_years", ["short"], -2, "has weak resale value (rating <= 2)", lambda c: c.resale <= 2)
_score("keep_years", ["long"], 2, "has parts available everywhere", lambda c: c.parts >= 4)
_score("keep_years", ["long"], 1, "has cheap maintenance", lambda c: c.maint <= 2)
_score("keep_years", ["long"], -2, "has scarce parts (rating <= 2)", lambda c: c.parts <= 2)

_q("resale", "Ownership", "Is high resale value important to you?",
   [("yes", "Yes"), ("no", "No")])
_score("resale", ["yes"], 3, "has strong resale value (rating >= 4)", lambda c: c.resale >= 4)
_score("resale", ["yes"], -3, "has weak resale value (rating <= 2)", lambda c: c.resale <= 2)

_q("parts", "Ownership", "Do you live in a small city where parts and workshops are limited?",
   [("yes", "Yes"), ("no", "No")])
_score("parts", ["yes"], 3, "has parts available everywhere", lambda c: c.parts >= 4)
_score("parts", ["yes"], -3, "has scarce parts (rating <= 2)", lambda c: c.parts <= 2)

_q("brand_origin", "Ownership", "Which brand origin do you trust most?",
   [("japanese", "Japanese"), ("korean", "Korean"), ("chinese", "Chinese"), ("any", "No preference")])
for key in ("japanese", "korean", "chinese"):
    _score("brand_origin", [key], 3, f"is a {key.title()} brand", lambda c, k=key: c.region == k)

_q("warranty", "Ownership", "Is a factory warranty important to you?",
   [("yes", "Yes"), ("no", "No")])
_score("warranty", ["yes"], 2, "has a 3+ year warranty", lambda c: c.warranty >= 3)
_score("warranty", ["yes"], -3, "has no warranty (used car)", lambda c: c.warranty == 0)

_q("import_ok", "Ownership", "Are you OK with an imported used car (auction-sheet based)?",
   [("yes", "Yes"), ("no", "No")], depends=lambda a: a.get("condition") != "new")
_require("import_ok", ["no"], "it is not a used import", lambda c: not (c.condition == "used" and c.origin == "imported"))

_q("local_assembly", "Ownership", "Do you prefer a locally assembled car (easier registration and parts)?",
   [("yes", "Yes"), ("no", "Doesn't matter")])
_score("local_assembly", ["yes"], 2, "is assembled in Pakistan", lambda c: c.origin == "local")

_q("reliability", "Ownership", "What matters more: proven reliability or the latest features?",
   [("reliability", "Proven reliability"), ("features", "Latest features"), ("both", "Both equally")])
_score("reliability", ["reliability"], 2, "has cheap upkeep and parts everywhere",
       lambda c: c.maint <= 2 and c.parts >= 4)
_score("reliability", ["features"], 2, "has camera, touchscreen and cruise control",
       lambda c: c.camera and c.touch and c.cruise)

# =========================================================================
# 8. FEATURES & SAFETY
# =========================================================================
_q("airbags", "Features & safety", "How many airbags do you want at minimum?",
   [("any", "Doesn't matter"), ("two", "At least 2"), ("six", "6 or more")])
_require("airbags", ["two"], "airbags >= 2", lambda c: c.airbags >= 2)
_require("airbags", ["six"], "airbags >= 6", lambda c: c.airbags >= 6)

_q("abs", "Features & safety", "Are ABS (anti-lock) brakes a must?",
   [("yes", "Yes, must have"), ("no", "Not necessary")])
_require("abs", ["yes"], "the car has ABS", lambda c: c.abs)

_q("camera", "Features & safety", "Do you want a reverse parking camera?",
   [("yes", "Yes"), ("no", "No")])
_score("camera", ["yes"], 2, "has a reverse camera", lambda c: c.camera)
_score("camera", ["yes"], -1, "has no reverse camera", lambda c: not c.camera)

_q("touchscreen", "Features & safety", "Do you want a touchscreen with Android Auto / Apple CarPlay?",
   [("yes", "Yes"), ("no", "No")])
_score("touchscreen", ["yes"], 2, "has a touchscreen", lambda c: c.touch)

_q("cruise", "Features & safety", "Do you want cruise control?",
   [("yes", "Yes"), ("no", "No")])
_score("cruise", ["yes"], 2, "has cruise control", lambda c: c.cruise)

_q("sunroof", "Features & safety", "Do you want a sunroof?",
   [("yes", "Yes"), ("no", "No")])
_score("sunroof", ["yes"], 2, "has a sunroof", lambda c: c.sunroof)

_q("keyless", "Features & safety", "Do you want push-start / keyless entry?",
   [("yes", "Yes"), ("no", "No")])
_score("keyless", ["yes"], 1, "has push-start", lambda c: c.keyless)

_q("climate", "Features & safety", "Do you want automatic climate control?",
   [("yes", "Yes"), ("no", "No")])
_score("climate", ["yes"], 1, "has automatic climate control", lambda c: c.climate)

# =========================================================================
# 9. BRAND & STYLE
# =========================================================================
_q("body", "Brand & style", "Which body type do you prefer?",
   [("hatchback", "Hatchback"), ("sedan", "Sedan"), ("suv", "SUV / crossover"),
    ("mpv", "MPV / van"), ("pickup", "Pickup"), ("any", "No preference")])
for key in ("hatchback", "sedan", "suv", "mpv", "pickup"):
    _require("body", [key], f"body type is {key}", lambda c, k=key: c.body == k)

_q("company", "Brand & style", "Do you have a favourite car company?",
   [("Suzuki", "Suzuki"), ("Toyota", "Toyota"), ("Honda", "Honda"), ("KIA", "KIA"),
    ("Hyundai", "Hyundai"), ("Changan", "Changan"), ("MG", "MG"), ("Haval", "Haval"),
    ("any", "No preference")])
for key in ("Suzuki", "Toyota", "Honda", "KIA", "Hyundai", "Changan", "MG", "Haval"):
    _score("company", [key], 4, f"is made by {key}", lambda c, k=key: c.company == k)

_q("looks", "Brand & style", "What matters more: looks or practicality?",
   [("looks", "Looks / style"), ("practical", "Practicality"), ("both", "Both")])
_score("looks", ["looks"], 3, "looks stylish (rating >= 4)", lambda c: c.style >= 4)
_score("looks", ["looks"], -1, "looks plain (rating <= 2)", lambda c: c.style <= 2)
_score("looks", ["practical"], 2, "has cheap upkeep and parts everywhere", lambda c: c.parts >= 4 and c.maint <= 2)
_score("looks", ["practical"], 1, "has a 400+ litre boot", lambda c: c.boot >= 400)


QUESTIONS_BY_ID = {q.id: q for q in QUESTIONS}
RULES_BY_QUESTION: dict = {}
for _r in RULES:
    RULES_BY_QUESTION.setdefault(_r.qid, []).append(_r)

# The first questions a car expert always asks (like a doctor's first
# "where does it hurt?"). After these, the engine picks questions dynamically.
CORE_ORDER = ["budget", "condition", "passengers", "body", "fuel", "transmission", "main_use"]
