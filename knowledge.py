"""
KNOWLEDGE BASE of GaariGuide - everything the expert knows, in one file.

  1. FACT BASE        49 cars and their attributes (price, seats, engine ...)
  2. QUESTIONS        59 questions the expert can ask, in 9 categories
  3. RULES            180 rules written as plain if / else (check_rules)
  4. DIAGNOSIS        30 diagnosis rules written as plain if / else (diagnose_buyer)

Two kinds of car rules are used:

  ELIMINATE rule  if <answer>:  if <condition>: keep the car   else: remove it ("drop")
  SCORE rule      if <answer>:  if <condition>: give the car +N or -N points

Prices are APPROXIMATE (PKR lakh) and only meant for an academic demo.
Rating fields use a 1-5 scale:
    resale  - how well the car keeps its value      (5 = excellent)
    parts   - availability of parts & workshops      (5 = everywhere)
    maint   - yearly maintenance COST                (1 = very cheap, 5 = costly)
    comfort - ride / cabin comfort                   (5 = luxury)
    power   - performance / acceleration             (5 = very powerful)
    style   - looks / premium feel                   (5 = very stylish)
"""

from dataclasses import dataclass


# =========================================================================
# 1. FACT BASE - the cars
# =========================================================================
@dataclass(frozen=True)
class Car:
    name: str
    company: str
    price: float                 # approx. price in PKR lakh
    condition: str               # "new" | "used"
    origin: str                  # "local" (assembled in Pakistan) | "imported"
    body: str                    # "hatchback" | "sedan" | "suv" | "mpv" | "pickup"
    seats: int
    cc: int                      # engine size, 0 for fully electric
    fuel: str                    # "petrol" | "hybrid" | "phev" | "ev" | "diesel"
    trans: tuple                 # ("manual",) / ("auto",) / ("manual", "auto")
    kmpl: float                  # average fuel economy (km per litre); EV = 0
    clearance: int               # ground clearance in mm
    drive: str                   # "2wd" | "4wd"
    resale: int
    parts: int
    maint: int
    comfort: int
    power: int
    style: int
    airbags: int
    abs: bool
    size: str                    # "small" | "medium" | "large"
    boot: int                    # boot space in litres
    region: str                  # "japanese" | "korean" | "chinese" | "other"
    camera: bool = False
    touch: bool = False          # touchscreen with Android Auto / CarPlay
    cruise: bool = False
    sunroof: bool = False
    keyless: bool = False        # push start / smart key
    climate: bool = False        # automatic climate control
    isofix: bool = False         # baby-seat anchors
    turbo: bool = False
    cargo: bool = False          # practical for carrying goods
    warranty: int = 0            # factory warranty in years
    notes: str = ""

    # ---- derived facts (used by many rules) --------------------------------
    @property
    def electrified(self) -> bool:
        """Hybrid, plug-in hybrid or fully electric."""
        return self.fuel in ("hybrid", "phev", "ev")

    @property
    def economical(self) -> bool:
        """Good fuel economy: 18+ km/l or electrified."""
        return self.electrified or self.kmpl >= 18

    @property
    def has_auto(self) -> bool:
        return "auto" in self.trans

    @property
    def has_manual(self) -> bool:
        return "manual" in self.trans


def _new(**kw):
    kw.setdefault("condition", "new")
    kw.setdefault("origin", "local")
    kw.setdefault("drive", "2wd")
    kw.setdefault("warranty", 3)
    return Car(**kw)


def _used(**kw):
    kw.setdefault("condition", "used")
    kw.setdefault("drive", "2wd")
    kw.setdefault("warranty", 0)
    return Car(**kw)


CARS = [
    # ------------------------------------------------------------- NEW: small
    _new(name="Suzuki Alto VXL AGS", company="Suzuki", price=31, body="hatchback", seats=4, cc=660,
         fuel="petrol", trans=("manual", "auto"), kmpl=22, clearance=160, resale=5, parts=5, maint=1,
         comfort=1, power=1, style=1, airbags=2, abs=True, size="small", boot=177, region="japanese"),
    _new(name="Suzuki Wagon R VXL", company="Suzuki", price=36, body="hatchback", seats=5, cc=1000,
         fuel="petrol", trans=("manual", "auto"), kmpl=20, clearance=165, resale=4, parts=5, maint=1,
         comfort=2, power=1, style=1, airbags=1, abs=True, size="small", boot=180, region="japanese"),
    _new(name="Suzuki Cultus VXL AGS", company="Suzuki", price=44, body="hatchback", seats=5, cc=1000,
         fuel="petrol", trans=("manual", "auto"), kmpl=19, clearance=170, resale=4, parts=5, maint=1,
         comfort=2, power=2, style=2, airbags=2, abs=True, size="small", boot=254, region="japanese",
         touch=True),
    _new(name="KIA Picanto 1.0 AT", company="KIA", price=40, body="hatchback", seats=5, cc=1000,
         fuel="petrol", trans=("manual", "auto"), kmpl=17, clearance=150, resale=3, parts=3, maint=2,
         comfort=2, power=2, style=3, airbags=2, abs=True, size="small", boot=255, region="korean"),
    _new(name="Suzuki Swift GLX CVT", company="Suzuki", price=57, body="hatchback", seats=5, cc=1200,
         fuel="petrol", trans=("manual", "auto"), kmpl=18, clearance=163, resale=4, parts=5, maint=2,
         comfort=3, power=2, style=4, airbags=2, abs=True, size="small", boot=265, region="japanese",
         camera=True, touch=True, keyless=True, climate=True, isofix=True),
    _new(name="Honri VE (Electric)", company="Honri", price=34, body="hatchback", seats=4, cc=0,
         fuel="ev", trans=("auto",), kmpl=0, clearance=145, resale=2, parts=2, maint=1,
         comfort=2, power=1, style=3, airbags=1, abs=True, size="small", boot=150, region="chinese",
         camera=True, touch=True, notes="City EV, ~200 km range"),
    # ------------------------------------------------------------ NEW: sedans
    _new(name="Proton Saga 1.3 Ace AT", company="Proton", price=36, body="sedan", seats=5, cc=1300,
         fuel="petrol", trans=("manual", "auto"), kmpl=16, clearance=165, resale=2, parts=2, maint=2,
         comfort=2, power=2, style=2, airbags=2, abs=True, size="medium", boot=420, region="other"),
    _new(name="Toyota Yaris 1.3 CVT", company="Toyota", price=52, body="sedan", seats=5, cc=1300,
         fuel="petrol", trans=("manual", "auto"), kmpl=17, clearance=150, resale=5, parts=5, maint=2,
         comfort=3, power=2, style=3, airbags=2, abs=True, size="medium", boot=475, region="japanese",
         camera=True, touch=True, isofix=True),
    _new(name="Changan Alsvin 1.5 Lumiere", company="Changan", price=53, body="sedan", seats=5, cc=1500,
         fuel="petrol", trans=("auto",), kmpl=15, clearance=150, resale=3, parts=3, maint=2,
         comfort=3, power=3, style=4, airbags=2, abs=True, size="medium", boot=450, region="chinese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True),
    _new(name="Honda City 1.5 Aspire CVT", company="Honda", price=60, body="sedan", seats=5, cc=1500,
         fuel="petrol", trans=("auto",), kmpl=16, clearance=165, resale=5, parts=5, maint=2,
         comfort=3, power=3, style=3, airbags=2, abs=True, size="medium", boot=506, region="japanese",
         camera=True, touch=True, cruise=True, keyless=True, isofix=True),
    _new(name="Toyota Corolla Altis 1.6 X", company="Toyota", price=74, body="sedan", seats=5, cc=1600,
         fuel="petrol", trans=("manual", "auto"), kmpl=13, clearance=170, resale=5, parts=5, maint=2,
         comfort=4, power=3, style=3, airbags=2, abs=True, size="medium", boot=470, region="japanese",
         camera=True, touch=True, isofix=True),
    _new(name="Hyundai Elantra 2.0 GLS", company="Hyundai", price=80, body="sedan", seats=5, cc=2000,
         fuel="petrol", trans=("auto",), kmpl=12, clearance=150, resale=3, parts=3, maint=3,
         comfort=4, power=4, style=4, airbags=6, abs=True, size="medium", boot=458, region="korean",
         camera=True, touch=True, cruise=True, keyless=True, climate=True, isofix=True),
    _new(name="Toyota Corolla Altis Grande 1.8", company="Toyota", price=82, body="sedan", seats=5, cc=1800,
         fuel="petrol", trans=("auto",), kmpl=12, clearance=170, resale=5, parts=5, maint=2,
         comfort=4, power=3, style=4, airbags=7, abs=True, size="medium", boot=470, region="japanese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True),
    _new(name="Honda Civic Oriel 1.5 Turbo", company="Honda", price=92, body="sedan", seats=5, cc=1500,
         fuel="petrol", trans=("auto",), kmpl=13, clearance=135, resale=5, parts=5, maint=3,
         comfort=4, power=4, style=5, airbags=4, abs=True, size="medium", boot=495, region="japanese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True,
         turbo=True),
    _new(name="Hyundai Sonata 2.5", company="Hyundai", price=125, body="sedan", seats=5, cc=2500,
         fuel="petrol", trans=("auto",), kmpl=11, clearance=145, resale=2, parts=3, maint=4,
         comfort=5, power=5, style=5, airbags=6, abs=True, size="large", boot=510, region="korean",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True),
    # -------------------------------------------------------------- NEW: SUVs
    _new(name="KIA Stonic EX+", company="KIA", price=66, body="suv", seats=5, cc=1400,
         fuel="petrol", trans=("auto",), kmpl=15, clearance=183, resale=3, parts=3, maint=2,
         comfort=3, power=3, style=4, airbags=6, abs=True, size="medium", boot=352, region="korean",
         camera=True, touch=True, cruise=True, keyless=True, isofix=True),
    _new(name="Haval Jolion 1.5T", company="Haval", price=78, body="suv", seats=5, cc=1500,
         fuel="petrol", trans=("auto",), kmpl=13, clearance=183, resale=3, parts=3, maint=3,
         comfort=4, power=4, style=5, airbags=6, abs=True, size="medium", boot=430, region="chinese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True,
         turbo=True),
    _new(name="Peugeot 2008 1.2T", company="Peugeot", price=80, body="suv", seats=5, cc=1200,
         fuel="petrol", trans=("auto",), kmpl=14, clearance=165, resale=2, parts=2, maint=3,
         comfort=4, power=3, style=5, airbags=6, abs=True, size="medium", boot=434, region="other",
         camera=True, touch=True, cruise=True, keyless=True, climate=True, isofix=True, turbo=True),
    _new(name="Honda HR-V 1.5 VTi-S", company="Honda", price=80, body="suv", seats=5, cc=1500,
         fuel="petrol", trans=("auto",), kmpl=14, clearance=196, resale=5, parts=4, maint=2,
         comfort=4, power=3, style=4, airbags=6, abs=True, size="medium", boot=395, region="japanese",
         camera=True, touch=True, cruise=True, keyless=True, climate=True, isofix=True),
    _new(name="Changan Oshan X7 FutureSense", company="Changan", price=87, body="suv", seats=7, cc=1500,
         fuel="petrol", trans=("auto",), kmpl=12, clearance=190, resale=3, parts=3, maint=3,
         comfort=4, power=4, style=4, airbags=6, abs=True, size="large", boot=445, region="chinese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True,
         turbo=True),
    _new(name="MG HS 1.5T", company="MG", price=88, body="suv", seats=5, cc=1500,
         fuel="petrol", trans=("auto",), kmpl=12, clearance=170, resale=2, parts=3, maint=3,
         comfort=4, power=4, style=4, airbags=6, abs=True, size="medium", boot=463, region="chinese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True,
         turbo=True),
    _new(name="KIA Sportage FWD", company="KIA", price=90, body="suv", seats=5, cc=2000,
         fuel="petrol", trans=("auto",), kmpl=11, clearance=182, resale=4, parts=4, maint=3,
         comfort=4, power=4, style=4, airbags=6, abs=True, size="large", boot=466, region="korean",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True),
    _new(name="Hyundai Tucson FWD", company="Hyundai", price=92, body="suv", seats=5, cc=2000,
         fuel="petrol", trans=("auto",), kmpl=11, clearance=181, resale=3, parts=3, maint=3,
         comfort=4, power=4, style=4, airbags=6, abs=True, size="large", boot=488, region="korean",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True),
    _new(name="KIA Sportage AWD", company="KIA", price=105, body="suv", seats=5, cc=2000, drive="4wd",
         fuel="petrol", trans=("auto",), kmpl=10, clearance=182, resale=4, parts=4, maint=3,
         comfort=4, power=4, style=4, airbags=6, abs=True, size="large", boot=466, region="korean",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True),
    _new(name="Toyota Corolla Cross 1.8 HEV", company="Toyota", price=100, body="suv", seats=5, cc=1800,
         fuel="hybrid", trans=("auto",), kmpl=20, clearance=161, resale=5, parts=4, maint=2,
         comfort=4, power=3, style=4, airbags=7, abs=True, size="medium", boot=440, region="japanese",
         camera=True, touch=True, cruise=True, keyless=True, climate=True, isofix=True),
    _new(name="KIA Sorento 2.4 (7-seater)", company="KIA", price=122, body="suv", seats=7, cc=2400,
         fuel="petrol", trans=("auto",), kmpl=9, clearance=176, resale=3, parts=3, maint=4,
         comfort=5, power=4, style=5, airbags=6, abs=True, size="large", boot=605, region="korean",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True),
    _new(name="Haval H6 HEV", company="Haval", price=125, body="suv", seats=5, cc=1500,
         fuel="hybrid", trans=("auto",), kmpl=17, clearance=200, resale=3, parts=3, maint=3,
         comfort=5, power=5, style=5, airbags=6, abs=True, size="large", boot=560, region="chinese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True,
         turbo=True),
    _new(name="MG HS PHEV", company="MG", price=125, body="suv", seats=5, cc=1500,
         fuel="phev", trans=("auto",), kmpl=30, clearance=170, resale=2, parts=2, maint=3,
         comfort=4, power=5, style=4, airbags=6, abs=True, size="medium", boot=448, region="chinese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True,
         turbo=True, notes="Plug-in hybrid, ~50 km on battery"),
    _new(name="MG ZS EV", company="MG", price=95, origin="imported", body="suv", seats=5, cc=0,
         fuel="ev", trans=("auto",), kmpl=0, clearance=161, resale=2, parts=2, maint=1,
         comfort=4, power=4, style=4, airbags=6, abs=True, size="medium", boot=448, region="chinese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True,
         notes="Electric, ~400 km range"),
    _new(name="BYD Atto 3", company="BYD", price=98, origin="imported", body="suv", seats=5, cc=0,
         fuel="ev", trans=("auto",), kmpl=0, clearance=175, resale=3, parts=2, maint=1,
         comfort=4, power=4, style=5, airbags=7, abs=True, size="medium", boot=440, region="chinese",
         camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True, isofix=True,
         notes="Electric, ~420 km range"),
    _new(name="Toyota Fortuner 2.8 Sigma 4", company="Toyota", price=180, body="suv", seats=7, cc=2800,
         drive="4wd", fuel="diesel", trans=("auto",), kmpl=10, clearance=279, resale=5, parts=5, maint=3,
         comfort=4, power=5, style=5, airbags=7, abs=True, size="large", boot=296, region="japanese",
         camera=True, touch=True, cruise=True, keyless=True, climate=True, isofix=True, turbo=True),
    # --------------------------------------------- NEW: MPV / van / pickups
    _new(name="Suzuki Every VX", company="Suzuki", price=30, body="mpv", seats=4, cc=660,
         fuel="petrol", trans=("manual",), kmpl=16, clearance=150, resale=4, parts=5, maint=1,
         comfort=1, power=1, style=1, airbags=0, abs=False, size="small", boot=650, region="japanese",
         cargo=True, warranty=2),
    _new(name="Changan Karvaan Plus", company="Changan", price=31, body="mpv", seats=7, cc=1000,
         fuel="petrol", trans=("manual",), kmpl=13, clearance=160, resale=3, parts=4, maint=1,
         comfort=1, power=1, style=1, airbags=0, abs=False, size="medium", boot=500, region="chinese",
         cargo=True, warranty=2),
    _new(name="Suzuki Ravi Pickup", company="Suzuki", price=23, body="pickup", seats=2, cc=800,
         fuel="petrol", trans=("manual",), kmpl=14, clearance=165, resale=4, parts=5, maint=1,
         comfort=1, power=1, style=1, airbags=0, abs=False, size="small", boot=1000, region="japanese",
         cargo=True, warranty=2),
    _new(name="Isuzu D-Max V-Cross 4x4", company="Isuzu", price=115, body="pickup", seats=5, cc=3000,
         drive="4wd", fuel="diesel", trans=("auto",), kmpl=11, clearance=235, resale=3, parts=3, maint=3,
         comfort=3, power=4, style=4, airbags=2, abs=True, size="large", boot=1000, region="japanese",
         camera=True, touch=True, cargo=True, turbo=True),
    _new(name="Toyota Hilux Revo V 2.8", company="Toyota", price=160, body="pickup", seats=5, cc=2800,
         drive="4wd", fuel="diesel", trans=("manual", "auto"), kmpl=10, clearance=286, resale=5, parts=5,
         maint=3, comfort=3, power=5, style=4, airbags=7, abs=True, size="large", boot=1000,
         region="japanese", camera=True, touch=True, cruise=True, keyless=True, climate=True, cargo=True,
         turbo=True),
    # ------------------------------------------------------------------ USED
    _used(name="Suzuki Mehran VXR (used, 2018)", company="Suzuki", price=11, origin="local", body="hatchback",
          seats=4, cc=800, fuel="petrol", trans=("manual",), kmpl=15, clearance=160, resale=4, parts=5,
          maint=1, comfort=1, power=1, style=1, airbags=0, abs=False, size="small", boot=150, region="japanese"),
    _used(name="Suzuki Cultus VXL (used, 2019)", company="Suzuki", price=25, origin="local", body="hatchback",
          seats=5, cc=1000, fuel="petrol", trans=("manual",), kmpl=17, clearance=165, resale=4, parts=5,
          maint=1, comfort=2, power=2, style=2, airbags=0, abs=True, size="small", boot=254, region="japanese"),
    _used(name="Daihatsu Mira (used, 2019 import)", company="Daihatsu", price=27, origin="imported",
          body="hatchback", seats=4, cc=660, fuel="petrol", trans=("auto",), kmpl=24, clearance=150, resale=4,
          parts=3, maint=1, comfort=1, power=1, style=2, airbags=2, abs=True, size="small", boot=160,
          region="japanese"),
    _used(name="Nissan Dayz Highway Star (used, 2019 import)", company="Nissan", price=30, origin="imported",
          body="hatchback", seats=4, cc=660, fuel="petrol", trans=("auto",), kmpl=21, clearance=150, resale=3,
          parts=3, maint=1, comfort=2, power=1, style=3, airbags=2, abs=True, size="small", boot=170,
          region="japanese", camera=True, touch=True, keyless=True, climate=True),
    _used(name="Honda Civic Reborn (used, 2012)", company="Honda", price=30, origin="local", body="sedan",
          seats=5, cc=1800, fuel="petrol", trans=("auto",), kmpl=11, clearance=150, resale=4, parts=4,
          maint=3, comfort=3, power=3, style=3, airbags=2, abs=True, size="medium", boot=440, region="japanese"),
    _used(name="Toyota Corolla GLi (used, 2016)", company="Toyota", price=33, origin="local", body="sedan",
          seats=5, cc=1300, fuel="petrol", trans=("manual", "auto"), kmpl=13, clearance=170, resale=5, parts=5,
          maint=2, comfort=3, power=2, style=2, airbags=2, abs=True, size="medium", boot=470, region="japanese"),
    _used(name="Honda City Aspire (used, 2019)", company="Honda", price=35, origin="local", body="sedan",
          seats=5, cc=1300, fuel="petrol", trans=("manual", "auto"), kmpl=14, clearance=160, resale=5, parts=5,
          maint=2, comfort=3, power=2, style=2, airbags=2, abs=True, size="medium", boot=506, region="japanese"),
    _used(name="Honda BR-V i-VTEC S (used, 2020)", company="Honda", price=45, origin="local", body="mpv",
          seats=7, cc=1500, fuel="petrol", trans=("auto",), kmpl=13, clearance=201, resale=4, parts=4, maint=2,
          comfort=3, power=3, style=3, airbags=2, abs=True, size="medium", boot=223, region="japanese",
          camera=True, isofix=True),
    _used(name="Toyota Aqua Hybrid (used, 2018 import)", company="Toyota", price=45, origin="imported",
          body="hatchback", seats=5, cc=1500, fuel="hybrid", trans=("auto",), kmpl=25, clearance=140,
          resale=4, parts=4, maint=2, comfort=2, power=2, style=3, airbags=2, abs=True, size="small", boot=305,
          region="japanese", climate=True, keyless=True),
    _used(name="Toyota Prius (used, 2017 import)", company="Toyota", price=55, origin="imported",
          body="hatchback", seats=5, cc=1800, fuel="hybrid", trans=("auto",), kmpl=25, clearance=140,
          resale=3, parts=3, maint=3, comfort=3, power=2, style=3, airbags=7, abs=True, size="medium", boot=502,
          region="japanese", camera=True, touch=True, cruise=True, keyless=True, climate=True, isofix=True),
    _used(name="Honda Vezel Hybrid (used, 2017 import)", company="Honda", price=62, origin="imported",
          body="suv", seats=5, cc=1500, fuel="hybrid", trans=("auto",), kmpl=20, clearance=185, resale=4,
          parts=3, maint=3, comfort=3, power=3, style=4, airbags=6, abs=True, size="medium", boot=393,
          region="japanese", camera=True, touch=True, cruise=True, keyless=True, climate=True, isofix=True),
    _used(name="Suzuki Jimny Sierra (used, 2020 import)", company="Suzuki", price=85, origin="imported",
          body="suv", seats=4, cc=1500, drive="4wd", fuel="petrol", trans=("manual", "auto"), kmpl=14,
          clearance=210, resale=4, parts=3, maint=2, comfort=2, power=2, style=5, airbags=6, abs=True,
          size="small", boot=85, region="japanese", isofix=True),
    _used(name="Toyota Prado TX (used, 2015 import)", company="Toyota", price=230, origin="imported",
          body="suv", seats=7, cc=2700, drive="4wd", fuel="petrol", trans=("auto",), kmpl=8, clearance=220,
          resale=5, parts=4, maint=4, comfort=5, power=4, style=5, airbags=7, abs=True, size="large", boot=550,
          region="japanese", camera=True, touch=True, cruise=True, sunroof=True, keyless=True, climate=True,
          isofix=True),
]

CAR_BY_NAME = {c.name: c for c in CARS}

# =========================================================================
# 2. QUESTIONS
# =========================================================================
SKIP = "skip"   # every question also gets a "Not sure / skip" option


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    text: str
    options: tuple       # ((key, label), ...)
    help: str = ""

    def label(self, key):
        if key == SKIP:
            return "Not sure / skip"
        return dict(self.options).get(key, key)


QUESTIONS = [
    Question("budget", "Budget & finance", "What is your total budget for the car?",
             (("u25", "Under 25 lakh"), ("b25_40", "25 - 40 lakh"), ("b40_60", "40 - 60 lakh"), ("b60_90", "60 - 90 lakh"), ("b90_130", "90 lakh - 1.3 crore"), ("b130", "Above 1.3 crore"),),
             help="Approximate on-road budget in Pakistani rupees."),
    Question("payment", "Budget & finance", "How will you pay for the car?",
             (("cash", "Full cash"), ("lease", "Bank financing / car lease"), ("install", "Company installments"),)),
    Question("fuel_budget", "Budget & finance", "What is your monthly fuel budget?",
             (("low", "Tight (under Rs 25,000)"), ("mid", "Moderate"), ("high", "Not a concern"),)),
    Question("maint_budget", "Budget & finance", "What is your yearly maintenance budget?",
             (("low", "Low - keep it cheap"), ("mid", "Average"), ("high", "Not a concern"),)),
    Question("token_tax", "Budget & finance", "Are yearly token tax and registration costs a concern for you?",
             (("yes", "Yes, keep them low"), ("no", "No"),)),
    Question("passengers", "Family & space", "How many people usually travel in the car (including the driver)?",
             (("p1_2", "1 - 2"), ("p3_4", "3 - 4"), ("p5", "5"), ("p6_7", "6 - 7"),)),
    Question("kids", "Family & space", "Do you have young children who will travel with you?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("baby_seat", "Family & space", "Do you need to fit a baby car seat (ISOFIX anchors)?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("elderly", "Family & space", "Will elderly family members ride in the car often?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("luggage", "Family & space", "How much luggage do you usually carry?",
             (("small", "Very little"), ("medium", "A few bags"), ("large", "A lot (family trips, shopping)"),)),
    Question("cargo", "Family & space", "Will you carry goods or cargo for business?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("rear_comfort", "Family & space", "Will you mostly sit in the back seat (driver-driven car)?",
             (("yes", "Yes"), ("no", "No, I will drive"),)),
    Question("main_use", "Usage", "Where will you drive the car most of the time?",
             (("city", "Inside the city"), ("highway", "Mostly highways / intercity"), ("mixed", "Both equally"),)),
    Question("daily_km", "Usage", "How many kilometres do you drive daily?",
             (("lt20", "Less than 20 km"), ("k20_60", "20 - 60 km"), ("gt60", "More than 60 km"),)),
    Question("ride_hailing", "Usage", "Will you use the car for Careem / InDrive / Yango?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("long_trips", "Usage", "Do you often take long intercity trips (e.g. Lahore - Islamabad)?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("motorway", "Usage", "Do you often drive at high speed on motorways?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("traffic", "Usage", "Do you face heavy stop-and-go traffic every day?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("shared_drivers", "Usage", "Will several family members drive this car?",
             (("yes", "Yes"), ("no", "No, mostly me"),)),
    Question("terrain", "Roads & location", "Which kind of area do you live / drive in?",
             (("plains", "Plain cities (Lahore, Karachi, Multan...)"), ("north", "Hilly / northern areas (Murree, Swat, Gilgit...)"), ("desert", "Desert / rural (Thar, Balochistan...)"),)),
    Question("rough_roads", "Roads & location", "How often do you drive on broken or unpaved roads?",
             (("often", "Often"), ("sometimes", "Sometimes"), ("never", "Rarely / never"),)),
    Question("flooding", "Roads & location", "Do roads in your area flood during monsoon rains?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("narrow", "Roads & location", "Are the streets in your area narrow or crowded?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("parking", "Roads & location", "Where will the car usually be parked?",
             (("garage", "Own garage / porch"), ("street", "On the street"), ("apartment", "Apartment / shared parking"),)),
    Question("home_charging", "Roads & location", "Can you install a charger at home (for electric / plug-in cars)?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("heat", "Roads & location", "Do you live in a very hot city with heavy AC use?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("village", "Roads & location", "Do you often visit villages or farmland?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("fuel", "Engine & fuel", "Which fuel type do you prefer?",
             (("petrol", "Petrol"), ("hybrid", "Hybrid"), ("electric", "Fully electric"), ("diesel", "Diesel"), ("any", "No preference"),)),
    Question("engine_cc", "Engine & fuel", "Which engine size do you prefer?",
             (("s660", "660 - 800cc"), ("s1000", "1000 - 1300cc"), ("s1300", "1300 - 1600cc"), ("s1800", "1800cc and above"),)),
    Question("power_eco", "Engine & fuel", "What matters more to you: power or fuel economy?",
             (("power", "Power"), ("balanced", "A balance of both"), ("economy", "Fuel economy"),)),
    Question("turbo", "Engine & fuel", "Are you OK with a turbo engine (needs high-octane petrol, costlier upkeep)?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("cng", "Engine & fuel", "Do you plan to fit a CNG / LPG kit?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("eco", "Engine & fuel", "Is low pollution / eco-friendliness important to you?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("transmission", "Driving", "Do you want a manual or automatic car?",
             (("manual", "Manual"), ("auto", "Automatic"), ("any", "Either is fine"),)),
    Question("first_car", "Driving", "Is this your first car / are you a new driver?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("sporty", "Driving", "Do you enjoy sporty, fun-to-drive cars?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("high_seat", "Driving", "Do you prefer a high seating position (SUV feel)?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("tall", "Driving", "Is the main driver very tall (over 6 feet)?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("easy_park", "Driving", "Do you find parking difficult?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("condition", "Ownership", "Do you want a new or a used car?",
             (("new", "New"), ("used", "Used"), ("either", "Either"),)),
    Question("keep_years", "Ownership", "How long will you keep the car?",
             (("short", "Less than 3 years"), ("mid", "3 - 7 years"), ("long", "More than 7 years"),)),
    Question("resale", "Ownership", "Is high resale value important to you?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("parts", "Ownership", "Do you live in a small city where parts and workshops are limited?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("brand_origin", "Ownership", "Which brand origin do you trust most?",
             (("japanese", "Japanese"), ("korean", "Korean"), ("chinese", "Chinese"), ("any", "No preference"),)),
    Question("warranty", "Ownership", "Is a factory warranty important to you?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("import_ok", "Ownership", "Are you OK with an imported used car (auction-sheet based)?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("local_assembly", "Ownership", "Do you prefer a locally assembled car (easier registration and parts)?",
             (("yes", "Yes"), ("no", "Doesn't matter"),)),
    Question("reliability", "Ownership", "What matters more: proven reliability or the latest features?",
             (("reliability", "Proven reliability"), ("features", "Latest features"), ("both", "Both equally"),)),
    Question("airbags", "Features & safety", "How many airbags do you want at minimum?",
             (("any", "Doesn't matter"), ("two", "At least 2"), ("six", "6 or more"),)),
    Question("abs", "Features & safety", "Are ABS (anti-lock) brakes a must?",
             (("yes", "Yes, must have"), ("no", "Not necessary"),)),
    Question("camera", "Features & safety", "Do you want a reverse parking camera?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("touchscreen", "Features & safety", "Do you want a touchscreen with Android Auto / Apple CarPlay?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("cruise", "Features & safety", "Do you want cruise control?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("sunroof", "Features & safety", "Do you want a sunroof?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("keyless", "Features & safety", "Do you want push-start / keyless entry?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("climate", "Features & safety", "Do you want automatic climate control?",
             (("yes", "Yes"), ("no", "No"),)),
    Question("body", "Brand & style", "Which body type do you prefer?",
             (("hatchback", "Hatchback"), ("sedan", "Sedan"), ("suv", "SUV / crossover"), ("mpv", "MPV / van"), ("pickup", "Pickup"), ("any", "No preference"),)),
    Question("company", "Brand & style", "Do you have a favourite car company?",
             (("Suzuki", "Suzuki"), ("Toyota", "Toyota"), ("Honda", "Honda"), ("KIA", "KIA"), ("Hyundai", "Hyundai"), ("Changan", "Changan"), ("MG", "MG"), ("Haval", "Haval"), ("any", "No preference"),)),
    Question("looks", "Brand & style", "What matters more: looks or practicality?",
             (("looks", "Looks / style"), ("practical", "Practicality"), ("both", "Both"),)),
]

QUESTIONS_BY_ID = {q.id: q for q in QUESTIONS}

# The first questions a car expert always asks (like a doctor's first
# "where does it hurt?"). After these, the engine picks questions itself.
CORE_ORDER = ["budget", "condition", "passengers", "body", "fuel", "transmission", "main_use"]


def is_relevant(question, answers):
    """Some questions only make sense after a certain earlier answer."""
    if question == "baby_seat":
        return answers.get("kids") == "yes"
    elif question == "engine_cc":
        return answers.get("fuel") != "electric"
    elif question == "import_ok":
        return answers.get("condition") != "new"
    else:
        return True


# =========================================================================
# 3. RULES - if <answer>: check the car with if / else
# =========================================================================
def check_rules(question, answer, car):
    """Check every rule of this question and answer against one car.

    Returns the rules that fired, as (rule id, effect, condition):
        effect "keep"  -> the car passes an eliminate rule
        effect "drop"  -> the car fails an eliminate rule (it is removed)
        effect +N / -N -> score points for the car
    """
    fired = []

    if question == "budget":
        if answer == "u25":
            if car.price <= 25 * 1.05:
                fired.append(("R001", "keep", "price <= 26 lakh (budget + 5%)"))
            else:
                fired.append(("R001", "drop", "price <= 26 lakh (budget + 5%)"))
            if 0 <= car.price <= 25:
                fired.append(("R002", +3, "price is between 0 and 25 lakh"))
        elif answer == "b25_40":
            if car.price <= 40 * 1.05:
                fired.append(("R003", "keep", "price <= 42 lakh (budget + 5%)"))
            else:
                fired.append(("R003", "drop", "price <= 42 lakh (budget + 5%)"))
            if 25 <= car.price <= 40:
                fired.append(("R004", +3, "price is between 25 and 40 lakh"))
            if car.price < 25 * 0.6:
                fired.append(("R005", -3, "price is far below budget (< 15 lakh)"))
        elif answer == "b40_60":
            if car.price <= 60 * 1.05:
                fired.append(("R006", "keep", "price <= 63 lakh (budget + 5%)"))
            else:
                fired.append(("R006", "drop", "price <= 63 lakh (budget + 5%)"))
            if 40 <= car.price <= 60:
                fired.append(("R007", +3, "price is between 40 and 60 lakh"))
            if car.price < 40 * 0.6:
                fired.append(("R008", -3, "price is far below budget (< 24 lakh)"))
        elif answer == "b60_90":
            if car.price <= 90 * 1.05:
                fired.append(("R009", "keep", "price <= 94 lakh (budget + 5%)"))
            else:
                fired.append(("R009", "drop", "price <= 94 lakh (budget + 5%)"))
            if 60 <= car.price <= 90:
                fired.append(("R010", +3, "price is between 60 and 90 lakh"))
            if car.price < 60 * 0.6:
                fired.append(("R011", -3, "price is far below budget (< 36 lakh)"))
        elif answer == "b90_130":
            if car.price <= 130 * 1.05:
                fired.append(("R012", "keep", "price <= 136 lakh (budget + 5%)"))
            else:
                fired.append(("R012", "drop", "price <= 136 lakh (budget + 5%)"))
            if 90 <= car.price <= 130:
                fired.append(("R013", +3, "price is between 90 and 130 lakh"))
            if car.price < 90 * 0.6:
                fired.append(("R014", -3, "price is far below budget (< 54 lakh)"))
        elif answer == "b130":
            if car.price <= 400 * 1.05:
                fired.append(("R015", "keep", "price <= 420 lakh (budget + 5%)"))
            else:
                fired.append(("R015", "drop", "price <= 420 lakh (budget + 5%)"))
            if 130 <= car.price <= 400:
                fired.append(("R016", +3, "price is between 130 and 400 lakh"))
            if car.price < 130 * 0.6:
                fired.append(("R017", -3, "price is far below budget (< 78 lakh)"))

    elif question == "payment":
        if answer in ("lease", "install"):
            if car.condition == "new":
                fired.append(("R018", +2, "is new (banks finance new cars easily)"))
        if answer == "lease":
            if car.condition == "used" and car.origin == "imported":
                fired.append(("R019", -3, "is a used import (hard to finance)"))

    elif question == "fuel_budget":
        if answer == "low":
            if car.economical:
                fired.append(("R020", +3, "is economical (18+ km/l or electrified)"))
            if not car.electrified and car.kmpl < 12:
                fired.append(("R021", -3, "is thirsty (under 12 km/l)"))
        elif answer == "mid":
            if car.electrified or car.kmpl >= 14:
                fired.append(("R022", +1, "gives 14+ km/l or is electrified"))

    elif question == "maint_budget":
        if answer == "low":
            if car.maint <= 2:
                fired.append(("R023", +2, "has cheap maintenance (rating <= 2)"))
            if car.maint >= 4:
                fired.append(("R024", -3, "has costly maintenance (rating >= 4)"))
        elif answer == "mid":
            if car.maint >= 4:
                fired.append(("R025", -1, "has costly maintenance (rating >= 4)"))

    elif question == "token_tax":
        if answer == "yes":
            if car.cc <= 1300:
                fired.append(("R026", +2, "has an engine of 1300cc or less"))
            if car.cc > 2000:
                fired.append(("R027", -2, "has an engine above 2000cc"))

    elif question == "passengers":
        if answer == "p3_4":
            if car.seats >= 4:
                fired.append(("R028", "keep", "seats >= 4"))
            else:
                fired.append(("R028", "drop", "seats >= 4"))
        elif answer == "p5":
            if car.seats >= 5:
                fired.append(("R029", "keep", "seats >= 5"))
            else:
                fired.append(("R029", "drop", "seats >= 5"))
        elif answer == "p6_7":
            if car.seats >= 7:
                fired.append(("R030", "keep", "seats >= 7"))
            else:
                fired.append(("R030", "drop", "seats >= 7"))
        elif answer == "p1_2":
            if car.size == "small":
                fired.append(("R031", +2, "is a small car"))

    elif question == "kids":
        if answer == "yes":
            if car.airbags >= 2:
                fired.append(("R032", +2, "has at least 2 airbags"))
            if car.isofix and car.seats >= 4:
                fired.append(("R033", +1, "has 4 or more seats with ISOFIX"))

    elif question == "baby_seat":
        if answer == "yes":
            if car.isofix:
                fired.append(("R034", +3, "has ISOFIX anchors"))

    elif question == "elderly":
        if answer == "yes":
            if car.body in ("suv", "mpv") and car.clearance >= 170:
                fired.append(("R035", +2, "is an SUV/MPV with easy entry (clearance >= 170 mm)"))
            if car.comfort >= 4:
                fired.append(("R036", +1, "has high comfort (rating >= 4)"))
            if car.size == "small" and car.comfort <= 1:
                fired.append(("R037", -2, "is a small cramped car"))

    elif question == "luggage":
        if answer == "large":
            if car.boot >= 450:
                fired.append(("R038", +3, "has a big boot (450+ litres)"))
            if car.boot < 250:
                fired.append(("R039", -3, "has a tiny boot (under 250 litres)"))
        elif answer == "medium":
            if car.boot >= 300:
                fired.append(("R040", +1, "has a boot of 300+ litres"))

    elif question == "cargo":
        if answer == "yes":
            if car.cargo:
                fired.append(("R041", +4, "is practical for cargo"))
        elif answer == "no":
            if car.cargo:
                fired.append(("R042", -2, "is a pickup or van built for cargo"))

    elif question == "rear_comfort":
        if answer == "yes":
            if car.comfort >= 4 and car.body in ("sedan", "suv"):
                fired.append(("R043", +3, "is a comfortable sedan/SUV (comfort >= 4)"))
            if car.size == "small":
                fired.append(("R044", -2, "is a small car"))

    elif question == "main_use":
        if answer == "city":
            if car.size in ("small", "medium"):
                fired.append(("R045", +2, "is small or medium sized"))
            if car.has_auto:
                fired.append(("R046", +1, "is available in automatic"))
        elif answer == "highway":
            if car.cc >= 1300 or car.fuel == "ev":
                fired.append(("R047", +2, "has 1300cc+ or is electric"))
            if 0 < car.cc < 1000:
                fired.append(("R048", -2, "has an engine under 1000cc"))
        elif answer == "mixed":
            if 1000 <= car.cc <= 1800:
                fired.append(("R049", +1, "has a 1000-1800cc engine"))

    elif question == "daily_km":
        if answer == "gt60":
            if car.economical:
                fired.append(("R050", +3, "is economical (18+ km/l or electrified)"))
            if car.comfort >= 3:
                fired.append(("R051", +1, "is comfortable (rating >= 3)"))
        elif answer == "k20_60":
            if car.electrified or car.kmpl >= 15:
                fired.append(("R052", +1, "gives 15+ km/l or is electrified"))

    elif question == "ride_hailing":
        if answer == "yes":
            if car.seats >= 4 and car.body != "pickup":
                fired.append(("R053", "keep", "4+ seats and a passenger body (not a pickup)"))
            else:
                fired.append(("R053", "drop", "4+ seats and a passenger body (not a pickup)"))
            if car.parts >= 4 and car.maint <= 2:
                fired.append(("R054", +3, "has cheap parts & maintenance"))
            if car.economical:
                fired.append(("R055", +2, "is economical"))
            if car.price > 70:
                fired.append(("R056", -3, "costs over 70 lakh"))

    elif question == "long_trips":
        if answer == "yes":
            if car.cc >= 1300:
                fired.append(("R057", +2, "has a 1300cc+ engine"))
            if car.cruise:
                fired.append(("R058", +2, "has cruise control"))
            if car.fuel == "ev":
                fired.append(("R059", -2, "is fully electric (few highway chargers)"))
            if 0 < car.cc <= 800:
                fired.append(("R060", -2, "has an 800cc or smaller engine"))

    elif question == "motorway":
        if answer == "yes":
            if car.power >= 3:
                fired.append(("R061", +2, "has good power (rating >= 3)"))
            if car.airbags >= 4:
                fired.append(("R062", +1, "has 4 or more airbags"))
            if 0 < car.cc <= 800:
                fired.append(("R063", -3, "has an 800cc or smaller engine"))

    elif question == "traffic":
        if answer == "yes":
            if car.has_auto:
                fired.append(("R064", +2, "is available in automatic"))
            if car.electrified:
                fired.append(("R065", +2, "is hybrid or electric (saves fuel in traffic)"))
            if car.size == "small":
                fired.append(("R066", +1, "is small"))

    elif question == "shared_drivers":
        if answer == "yes":
            if car.has_auto:
                fired.append(("R067", +2, "is available in automatic"))
            if car.camera:
                fired.append(("R068", +1, "has a reverse camera"))

    elif question == "terrain":
        if answer == "north":
            if car.power >= 3 or car.drive == "4wd":
                fired.append(("R069", +3, "has good power or 4WD"))
            if car.clearance >= 180:
                fired.append(("R070", +2, "has high ground clearance (180+ mm)"))
            if 0 < car.cc <= 800:
                fired.append(("R071", -3, "has an 800cc or smaller engine"))
        elif answer == "desert":
            if car.clearance >= 180:
                fired.append(("R072", +3, "has high ground clearance (180+ mm)"))
            if car.drive == "4wd":
                fired.append(("R073", +2, "has 4WD"))
            if car.clearance < 150:
                fired.append(("R074", -2, "has low ground clearance (under 150 mm)"))
        elif answer == "plains":
            if car.electrified or car.kmpl >= 15:
                fired.append(("R075", +1, "gives 15+ km/l or is electrified"))

    elif question == "rough_roads":
        if answer == "often":
            if car.clearance >= 180:
                fired.append(("R076", +3, "has high ground clearance (180+ mm)"))
            if car.clearance < 150:
                fired.append(("R077", -3, "has low ground clearance (under 150 mm)"))
        elif answer == "sometimes":
            if car.clearance >= 165:
                fired.append(("R078", +1, "has 165+ mm ground clearance"))

    elif question == "flooding":
        if answer == "yes":
            if car.clearance >= 180:
                fired.append(("R079", +2, "has high ground clearance (180+ mm)"))
            if car.clearance < 150:
                fired.append(("R080", -2, "has low ground clearance (under 150 mm)"))
            if car.fuel == "ev":
                fired.append(("R081", -2, "is fully electric (battery & water risk)"))

    elif question == "narrow":
        if answer == "yes":
            if car.size == "small":
                fired.append(("R082", +3, "is a small car"))
            if car.size == "large":
                fired.append(("R083", -3, "is a large car"))

    elif question == "parking":
        if answer in ("street", "apartment"):
            if car.size == "small":
                fired.append(("R084", +1, "is small (easy to park)"))
            if car.size == "large":
                fired.append(("R085", -2, "is a large car"))

    elif question == "home_charging":
        if answer == "yes":
            if car.fuel in ("ev", "phev"):
                fired.append(("R086", +2, "is electric or plug-in hybrid"))
        elif answer == "no":
            if car.fuel != "ev":
                fired.append(("R087", "keep", "the car is not fully electric"))
            else:
                fired.append(("R087", "drop", "the car is not fully electric"))
            if car.fuel == "phev":
                fired.append(("R088", -3, "is a plug-in hybrid"))

    elif question == "heat":
        if answer == "yes":
            if 0 < car.cc <= 800:
                fired.append(("R089", -2, "has an 800cc or smaller engine (AC drains power)"))
            if car.climate:
                fired.append(("R090", +1, "has automatic climate control"))

    elif question == "village":
        if answer == "yes":
            if car.clearance >= 180:
                fired.append(("R091", +2, "has high ground clearance (180+ mm)"))
            if car.cargo:
                fired.append(("R092", +2, "is a pickup or cargo vehicle"))
            if car.parts >= 4:
                fired.append(("R093", +1, "has parts available everywhere"))

    elif question == "fuel":
        if answer == "petrol":
            if car.fuel == "petrol":
                fired.append(("R094", "keep", "fuel is petrol"))
            else:
                fired.append(("R094", "drop", "fuel is petrol"))
        elif answer == "hybrid":
            if car.fuel in ("hybrid", "phev"):
                fired.append(("R095", "keep", "fuel is hybrid / plug-in hybrid"))
            else:
                fired.append(("R095", "drop", "fuel is hybrid / plug-in hybrid"))
        elif answer == "electric":
            if car.fuel == "ev":
                fired.append(("R096", "keep", "the car is fully electric"))
            else:
                fired.append(("R096", "drop", "the car is fully electric"))
        elif answer == "diesel":
            if car.fuel == "diesel":
                fired.append(("R097", "keep", "fuel is diesel"))
            else:
                fired.append(("R097", "drop", "fuel is diesel"))

    elif question == "engine_cc":
        if answer == "s660":
            if 600 <= car.cc <= 999:
                fired.append(("R098", +3, "engine is 600-999cc"))
            if car.cc > 0 and not 600 <= car.cc <= 999:
                fired.append(("R099", -2, "engine is outside 600-999cc"))
        elif answer == "s1000":
            if 1000 <= car.cc <= 1299:
                fired.append(("R100", +3, "engine is 1000-1299cc"))
            if car.cc > 0 and not 1000 <= car.cc <= 1299:
                fired.append(("R101", -2, "engine is outside 1000-1299cc"))
        elif answer == "s1300":
            if 1300 <= car.cc <= 1699:
                fired.append(("R102", +3, "engine is 1300-1699cc"))
            if car.cc > 0 and not 1300 <= car.cc <= 1699:
                fired.append(("R103", -2, "engine is outside 1300-1699cc"))
        elif answer == "s1800":
            if 1700 <= car.cc <= 5000:
                fired.append(("R104", +3, "engine is 1700-5000cc"))
            if car.cc > 0 and not 1700 <= car.cc <= 5000:
                fired.append(("R105", -2, "engine is outside 1700-5000cc"))

    elif question == "power_eco":
        if answer == "power":
            if car.power >= 4:
                fired.append(("R106", +3, "is powerful (rating >= 4)"))
            if car.power <= 1:
                fired.append(("R107", -2, "is underpowered (rating 1)"))
        elif answer == "economy":
            if car.economical:
                fired.append(("R108", +3, "is economical (18+ km/l or electrified)"))
            if not car.electrified and car.kmpl < 12:
                fired.append(("R109", -2, "is thirsty (under 12 km/l)"))
        elif answer == "balanced":
            if 2 <= car.power <= 3 and (car.electrified or car.kmpl >= 14):
                fired.append(("R110", +1, "has power 2-3 and 14+ km/l"))

    elif question == "turbo":
        if answer == "yes":
            if car.turbo:
                fired.append(("R111", +1, "has a turbo engine"))
        elif answer == "no":
            if not car.turbo:
                fired.append(("R112", "keep", "the engine is not turbocharged"))
            else:
                fired.append(("R112", "drop", "the engine is not turbocharged"))

    elif question == "cng":
        if answer == "yes":
            if car.fuel == "petrol" and (not car.turbo):
                fired.append(("R113", "keep", "it is a non-turbo petrol car (CNG-friendly)"))
            else:
                fired.append(("R113", "drop", "it is a non-turbo petrol car (CNG-friendly)"))
            if 0 < car.cc <= 1300:
                fired.append(("R114", +2, "has a 1300cc or smaller engine"))

    elif question == "eco":
        if answer == "yes":
            if car.electrified:
                fired.append(("R115", +3, "is hybrid or electric"))
            if car.fuel == "diesel":
                fired.append(("R116", -1, "runs on diesel"))

    elif question == "transmission":
        if answer == "manual":
            if car.has_manual:
                fired.append(("R117", "keep", "a manual version is available"))
            else:
                fired.append(("R117", "drop", "a manual version is available"))
        elif answer == "auto":
            if car.has_auto:
                fired.append(("R118", "keep", "an automatic version is available"))
            else:
                fired.append(("R118", "drop", "an automatic version is available"))

    elif question == "first_car":
        if answer == "yes":
            if car.size == "small":
                fired.append(("R119", +2, "is small and easy to drive"))
            if car.parts >= 4:
                fired.append(("R120", +1, "has cheap parts (repairs after small accidents)"))
            if car.power >= 5:
                fired.append(("R121", -2, "is very powerful (rating 5)"))
            if car.size == "large":
                fired.append(("R122", -1, "is a large car"))

    elif question == "sporty":
        if answer == "yes":
            if car.power >= 4:
                fired.append(("R123", +3, "is powerful (rating >= 4)"))
            if car.style >= 4:
                fired.append(("R124", +1, "looks stylish (rating >= 4)"))
            if car.power <= 1:
                fired.append(("R125", -2, "is underpowered (rating 1)"))

    elif question == "high_seat":
        if answer == "yes":
            if car.body in ("suv", "mpv", "pickup"):
                fired.append(("R126", +3, "is an SUV, MPV or pickup"))
            if car.body == "sedan":
                fired.append(("R127", -1, "is a low sedan"))
        elif answer == "no":
            if car.body in ("sedan", "hatchback"):
                fired.append(("R128", +1, "is a sedan or hatchback"))

    elif question == "tall":
        if answer == "yes":
            if car.size == "small" and car.cc <= 1000:
                fired.append(("R129", -2, "is a small car with a tiny engine (cramped)"))
            if car.size == "large":
                fired.append(("R130", +1, "is a large car"))

    elif question == "easy_park":
        if answer == "yes":
            if car.camera:
                fired.append(("R131", +2, "has a reverse camera"))
            if car.size == "small":
                fired.append(("R132", +2, "is small"))
            if car.size == "large":
                fired.append(("R133", -1, "is a large car"))

    elif question == "condition":
        if answer == "new":
            if car.condition == "new":
                fired.append(("R134", "keep", "the car is new"))
            else:
                fired.append(("R134", "drop", "the car is new"))
        elif answer == "used":
            if car.condition == "used":
                fired.append(("R135", "keep", "the car is used"))
            else:
                fired.append(("R135", "drop", "the car is used"))

    elif question == "keep_years":
        if answer == "short":
            if car.resale >= 4:
                fired.append(("R136", +3, "has strong resale value (rating >= 4)"))
            if car.resale <= 2:
                fired.append(("R137", -2, "has weak resale value (rating <= 2)"))
        elif answer == "long":
            if car.parts >= 4:
                fired.append(("R138", +2, "has parts available everywhere"))
            if car.maint <= 2:
                fired.append(("R139", +1, "has cheap maintenance"))
            if car.parts <= 2:
                fired.append(("R140", -2, "has scarce parts (rating <= 2)"))

    elif question == "resale":
        if answer == "yes":
            if car.resale >= 4:
                fired.append(("R141", +3, "has strong resale value (rating >= 4)"))
            if car.resale <= 2:
                fired.append(("R142", -3, "has weak resale value (rating <= 2)"))

    elif question == "parts":
        if answer == "yes":
            if car.parts >= 4:
                fired.append(("R143", +3, "has parts available everywhere"))
            if car.parts <= 2:
                fired.append(("R144", -3, "has scarce parts (rating <= 2)"))

    elif question == "brand_origin":
        if answer == "japanese":
            if car.region == "japanese":
                fired.append(("R145", +3, "is a Japanese brand"))
        elif answer == "korean":
            if car.region == "korean":
                fired.append(("R146", +3, "is a Korean brand"))
        elif answer == "chinese":
            if car.region == "chinese":
                fired.append(("R147", +3, "is a Chinese brand"))

    elif question == "warranty":
        if answer == "yes":
            if car.warranty >= 3:
                fired.append(("R148", +2, "has a 3+ year warranty"))
            if car.warranty == 0:
                fired.append(("R149", -3, "has no warranty (used car)"))

    elif question == "import_ok":
        if answer == "no":
            if not (car.condition == "used" and car.origin == "imported"):
                fired.append(("R150", "keep", "it is not a used import"))
            else:
                fired.append(("R150", "drop", "it is not a used import"))

    elif question == "local_assembly":
        if answer == "yes":
            if car.origin == "local":
                fired.append(("R151", +2, "is assembled in Pakistan"))

    elif question == "reliability":
        if answer == "reliability":
            if car.maint <= 2 and car.parts >= 4:
                fired.append(("R152", +2, "has cheap upkeep and parts everywhere"))
        elif answer == "features":
            if car.camera and car.touch and car.cruise:
                fired.append(("R153", +2, "has camera, touchscreen and cruise control"))

    elif question == "airbags":
        if answer == "two":
            if car.airbags >= 2:
                fired.append(("R154", "keep", "airbags >= 2"))
            else:
                fired.append(("R154", "drop", "airbags >= 2"))
        elif answer == "six":
            if car.airbags >= 6:
                fired.append(("R155", "keep", "airbags >= 6"))
            else:
                fired.append(("R155", "drop", "airbags >= 6"))

    elif question == "abs":
        if answer == "yes":
            if car.abs:
                fired.append(("R156", "keep", "the car has ABS"))
            else:
                fired.append(("R156", "drop", "the car has ABS"))

    elif question == "camera":
        if answer == "yes":
            if car.camera:
                fired.append(("R157", +2, "has a reverse camera"))
            if not car.camera:
                fired.append(("R158", -1, "has no reverse camera"))

    elif question == "touchscreen":
        if answer == "yes":
            if car.touch:
                fired.append(("R159", +2, "has a touchscreen"))

    elif question == "cruise":
        if answer == "yes":
            if car.cruise:
                fired.append(("R160", +2, "has cruise control"))

    elif question == "sunroof":
        if answer == "yes":
            if car.sunroof:
                fired.append(("R161", +2, "has a sunroof"))

    elif question == "keyless":
        if answer == "yes":
            if car.keyless:
                fired.append(("R162", +1, "has push-start"))

    elif question == "climate":
        if answer == "yes":
            if car.climate:
                fired.append(("R163", +1, "has automatic climate control"))

    elif question == "body":
        if answer == "hatchback":
            if car.body == "hatchback":
                fired.append(("R164", "keep", "body type is hatchback"))
            else:
                fired.append(("R164", "drop", "body type is hatchback"))
        elif answer == "sedan":
            if car.body == "sedan":
                fired.append(("R165", "keep", "body type is sedan"))
            else:
                fired.append(("R165", "drop", "body type is sedan"))
        elif answer == "suv":
            if car.body == "suv":
                fired.append(("R166", "keep", "body type is suv"))
            else:
                fired.append(("R166", "drop", "body type is suv"))
        elif answer == "mpv":
            if car.body == "mpv":
                fired.append(("R167", "keep", "body type is mpv"))
            else:
                fired.append(("R167", "drop", "body type is mpv"))
        elif answer == "pickup":
            if car.body == "pickup":
                fired.append(("R168", "keep", "body type is pickup"))
            else:
                fired.append(("R168", "drop", "body type is pickup"))

    elif question == "company":
        if answer == "Suzuki":
            if car.company == "Suzuki":
                fired.append(("R169", +4, "is made by Suzuki"))
        elif answer == "Toyota":
            if car.company == "Toyota":
                fired.append(("R170", +4, "is made by Toyota"))
        elif answer == "Honda":
            if car.company == "Honda":
                fired.append(("R171", +4, "is made by Honda"))
        elif answer == "KIA":
            if car.company == "KIA":
                fired.append(("R172", +4, "is made by KIA"))
        elif answer == "Hyundai":
            if car.company == "Hyundai":
                fired.append(("R173", +4, "is made by Hyundai"))
        elif answer == "Changan":
            if car.company == "Changan":
                fired.append(("R174", +4, "is made by Changan"))
        elif answer == "MG":
            if car.company == "MG":
                fired.append(("R175", +4, "is made by MG"))
        elif answer == "Haval":
            if car.company == "Haval":
                fired.append(("R176", +4, "is made by Haval"))

    elif question == "looks":
        if answer == "looks":
            if car.style >= 4:
                fired.append(("R177", +3, "looks stylish (rating >= 4)"))
            if car.style <= 2:
                fired.append(("R178", -1, "looks plain (rating <= 2)"))
        elif answer == "practical":
            if car.parts >= 4 and car.maint <= 2:
                fired.append(("R179", +2, "has cheap upkeep and parts everywhere"))
            if car.boot >= 400:
                fired.append(("R180", +1, "has a 400+ litre boot"))

    return fired


# =========================================================================
# 4. DIAGNOSIS - what kind of buyer is this? (answers = the "symptoms")
# =========================================================================
def diagnose_buyer(a):
    """Return (profile, needs, conflicts) for the answers `a` (question -> answer)."""

    # ---- buyer type: the first rule that matches wins -------------------
    if a.get("cargo") == "yes" or a.get("body") == "pickup":
        profile = ("D01", "Business & cargo user", "You need a working vehicle that can carry goods every day.")
    elif a.get("ride_hailing") == "yes":
        profile = ("D02", "Ride-hailing earner", "The car has to earn money, so running costs and reliability come first.")
    elif a.get("terrain") in ("north", "desert") or a.get("rough_roads") == "often":
        profile = ("D03", "Rough-road explorer", "Your roads are tough, so ground clearance and power matter most.")
    elif a.get("passengers") == "p6_7":
        profile = ("D04", "Large family", "You need space for 6-7 people and their luggage.")
    elif a.get("budget") in ("b90_130", "b130"):
        profile = ("D05", "Premium buyer", "Your budget is high, so comfort, features and brand matter more than price.")
    elif a.get("power_eco") == "power" or a.get("sporty") == "yes":
        profile = ("D06", "Performance enthusiast", "You enjoy driving, so power and handling come first.")
    elif a.get("fuel") in ("hybrid", "electric") or a.get("eco") == "yes":
        profile = ("D07", "Eco-conscious driver", "You want low fuel use and low pollution.")
    elif a.get("first_car") == "yes":
        profile = ("D08", "First-time driver", "You need a car that is easy to drive, park and maintain.")
    elif a.get("budget") in ("u25", "b25_40") and a.get("main_use") == "city":
        profile = ("D09", "Budget city commuter", "You need an affordable, economical car for daily city driving.")
    elif a.get("main_use") == "highway" or a.get("long_trips") == "yes":
        profile = ("D10", "Highway cruiser", "You drive long distances, so a stable, comfortable car is key.")
    elif a.get("passengers") in ("p3_4", "p5") or a.get("kids") == "yes":
        profile = ("D11", "Family car buyer", "You need a safe, roomy car for everyday family use.")
    else:
        profile = ("D00", "Balanced everyday buyer", "Your needs are balanced, with no single strong priority.")

    # ---- key needs: every rule that matches is listed -------------------
    needs = []
    if a.get("fuel_budget") == "low" or a.get("power_eco") == "economy" or a.get("daily_km") == "gt60":
        needs.append(("N01", "High fuel economy"))
    if a.get("passengers") == "p6_7":
        needs.append(("N02", "7 seats"))
    if a.get("rough_roads") == "often" or a.get("flooding") == "yes" or a.get("terrain") in ("north", "desert"):
        needs.append(("N03", "High ground clearance"))
    if a.get("transmission") == "auto" or a.get("traffic") == "yes":
        needs.append(("N04", "Automatic gearbox"))
    if a.get("maint_budget") == "low" or a.get("parts") == "yes":
        needs.append(("N05", "Cheap, easy-to-find parts"))
    if a.get("kids") == "yes" or a.get("airbags") == "six" or a.get("motorway") == "yes":
        needs.append(("N06", "Strong safety"))
    if a.get("resale") == "yes":
        needs.append(("N07", "Good resale value"))
    if a.get("narrow") == "yes" or a.get("easy_park") == "yes":
        needs.append(("N08", "Compact, easy-to-park size"))
    if a.get("power_eco") == "power" or a.get("motorway") == "yes":
        needs.append(("N09", "Strong engine power"))
    if a.get("cargo") == "yes" or a.get("luggage") == "large":
        needs.append(("N10", "Large cargo space"))

    # ---- conflicts: requirements that clash -----------------------------
    conflicts = []
    if a.get("budget") == "u25" and a.get("passengers") == "p6_7":
        conflicts.append(("C01", "A budget under 25 lakh and 6-7 passengers clash: almost no 7-seater costs that little."))
    if a.get("budget") in ("u25", "b25_40") and a.get("fuel") == "electric":
        conflicts.append(("C02", "Electric cars cost far more than a budget under 40 lakh."))
    if a.get("fuel") == "electric" and a.get("home_charging") == "no":
        conflicts.append(("C03", "A fully electric car without home charging is hard to live with."))
    if a.get("fuel") == "electric" and a.get("long_trips") == "yes":
        conflicts.append(("C04", "Electric cars and frequent intercity trips clash: there are few highway chargers."))
    if a.get("power_eco") == "power" and a.get("fuel_budget") == "low":
        conflicts.append(("C05", "Wanting a powerful car and a tight fuel budget pull in opposite directions."))
    if a.get("passengers") == "p6_7" and a.get("narrow") == "yes":
        conflicts.append(("C06", "A 7-seater is large, but your streets are narrow."))
    if a.get("terrain") == "north" and a.get("engine_cc") == "s660":
        conflicts.append(("C07", "A 660-800cc engine struggles in hilly areas."))
    if a.get("budget") == "u25" and a.get("airbags") == "six":
        conflicts.append(("C08", "6 airbags are not available under 25 lakh."))
    if a.get("body") == "suv" and a.get("fuel_budget") == "low" and a.get("fuel") != "hybrid":
        conflicts.append(("C09", "Petrol SUVs use a lot of fuel, but your fuel budget is tight."))

    return profile, needs, conflicts


# =========================================================================
# Rule list for the knowledge-base browser and the explanations.
# It is collected by asking check_rules() about every answer and every car,
# so the if / else code above stays the only place where rules are written.
# =========================================================================
@dataclass(frozen=True)
class Rule:
    id: str
    qid: str
    answers: frozenset   # the answers that fire this rule
    kind: str            # "require" (eliminate) | "score"
    cond: str            # the car condition, as text
    points: int = 0      # for score rules

    def describe(self, questions_by_id=None):
        q = QUESTIONS_BY_ID[self.qid]
        ans = " / ".join(q.label(a) for a in sorted(self.answers))
        name = self.qid.replace("_", " ")
        if self.kind == "require":
            return f"if {name} is '{ans}': keep the car if {self.cond}, else remove it"
        sign = "+" if self.points > 0 else ""
        return f"if {name} is '{ans}' and the car {self.cond}: {sign}{self.points} points"


def _collect_rules():
    found = {}
    for q in QUESTIONS:
        for key, _ in q.options:
            for car in CARS:
                for rule_id, effect, cond in check_rules(q.id, key, car):
                    kind = "require" if effect in ("keep", "drop") else "score"
                    points = 0 if kind == "require" else effect
                    old = found.get(rule_id)
                    answers = (old.answers if old else frozenset()) | {key}
                    found[rule_id] = Rule(rule_id, q.id, answers, kind, cond, points)
    return sorted(found.values(), key=lambda r: r.id)


RULES = _collect_rules()
RULE_BY_ID = {r.id: r for r in RULES}
RULES_BY_QUESTION = {}
for _r in RULES:
    RULES_BY_QUESTION.setdefault(_r.qid, []).append(_r)


def rules_for(question, answer):
    """The rules (in order) that this answer can fire."""
    return [r for r in RULES_BY_QUESTION.get(question, []) if answer in r.answers]
