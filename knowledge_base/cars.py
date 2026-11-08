"""
FACT BASE - the cars GaariGuide knows about (Pakistani market).

Every car is a set of facts (attributes). The rules in rules.py test these
facts, e.g. "IF user needs 7 seats THEN keep only cars where seats >= 7".

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
