"""
INFERENCE ENGINE of GaariGuide.

Forward chaining with candidate elimination + scoring:

  1. Start with every car in the fact base as a candidate.
  2. For each answer, FIRE every rule of that question whose answer matches:
       - REQUIRE rule -> eliminate cars that fail the condition
                         (if it would eliminate ALL cars, the rule is
                          relaxed into a penalty instead: conflict resolution)
       - SCORE rule   -> add / subtract points to the cars that match
  3. Choose the NEXT question dynamically: the one that best separates
     the leading candidates (questions that cannot change anything are skipped).
  4. STOP as soon as the answer is clear (one car left, or a confident
     leader), otherwise keep asking - there is no fixed question count.

The engine is a pure function of the answers given so far, so going
"back" or changing an answer simply re-runs it.
"""

from dataclasses import dataclass, field

from knowledge_base.cars import CARS, CAR_BY_NAME, Car
from knowledge_base.rules import (CORE_ORDER, QUESTIONS, QUESTIONS_BY_ID, RULES_BY_QUESTION, SKIP,
                                  Question, Rule)

# ---- tuning knobs ----------------------------------------------------------
# Stopping tiers: (min questions asked, min match % of leader, min point lead over #2).
# The longer the consultation, the less certainty is needed to decide, so a
# clear user finishes in ~10-15 questions and an unsure user is asked more.
STOP_TIERS = [(10, 75, 5), (15, 70, 1), (20, 70, 0), (25, 0, 0)]
MIN_QUESTIONS = STOP_TIERS[0][0]   # never decide earlier unless only one car is left
REQUIRE_BONUS = 2        # points a car earns for passing a hard requirement
TOP_K = 5                # how many leading cars the question selector looks at
ELIMINATED = -10         # effect value used when simulating an elimination


@dataclass
class Firing:
    """One rule that fired during a consultation (for the explanation facility)."""
    step: int
    qid: str
    rule: Rule
    cars: list            # names of cars the rule affected
    effect: str           # "eliminated" | "passed" | "+3" | "-2" | "relaxed"


@dataclass
class State:
    answers: dict = field(default_factory=dict)            # qid -> option key
    order: list = field(default_factory=list)              # qids in the order asked
    alive: list = field(default_factory=lambda: [c.name for c in CARS])
    eliminated: dict = field(default_factory=dict)         # car -> (step, qid, Rule)
    earned: dict = field(default_factory=lambda: {c.name: 0.0 for c in CARS})
    max_points: float = 0.0
    firings: list = field(default_factory=list)
    reasons: dict = field(default_factory=lambda: {c.name: [] for c in CARS})  # car -> [(Rule, pts)]
    relaxed: list = field(default_factory=list)            # Rules that had to be relaxed

    # ---- derived views ---------------------------------------------------
    def match(self, name: str) -> float:
        """Match percentage of a car: points earned / points possible."""
        if self.max_points <= 0:
            return 0.0
        return max(0.0, min(100.0, 100.0 * self.earned[name] / self.max_points))

    def ranking(self) -> list:
        """Alive cars, best first (ties broken by resale value, then lower price)."""
        return sorted(self.alive, key=lambda n: (-self.earned[n], -CAR_BY_NAME[n].resale, CAR_BY_NAME[n].price))

    @property
    def asked(self) -> int:
        return len(self.order)


# ---------------------------------------------------------------------------
# 1. Rule firing
# ---------------------------------------------------------------------------
def matching_rules(qid: str, answer: str) -> list:
    if answer == SKIP:
        return []
    return [r for r in RULES_BY_QUESTION.get(qid, []) if answer in r.answers]


def apply_answer(state: State, qid: str, answer: str) -> None:
    """Fire every rule triggered by this answer (forward chaining)."""
    step = len(state.order) + 1
    state.answers[qid] = answer
    state.order.append(qid)

    for rule in matching_rules(qid, answer):
        cars = [CAR_BY_NAME[n] for n in state.alive]
        if rule.kind == "require":
            passing = [c.name for c in cars if rule.test(c)]
            failing = [c.name for c in cars if not rule.test(c)]
            state.max_points += REQUIRE_BONUS
            if not passing:
                # Conflict resolution: nothing left would satisfy this rule,
                # so treat it as a strong preference instead of a hard filter.
                state.relaxed.append(rule)
                for n in failing:
                    state.earned[n] -= 3
                    state.reasons[n].append((rule, -3))
                state.firings.append(Firing(step, qid, rule, failing, "relaxed"))
                continue
            for n in failing:
                state.alive.remove(n)
                state.eliminated[n] = (step, qid, rule)
            for n in passing:
                state.earned[n] += REQUIRE_BONUS
                state.reasons[n].append((rule, REQUIRE_BONUS))
            if failing:
                state.firings.append(Firing(step, qid, rule, failing, "eliminated"))
        else:
            if rule.points > 0:
                state.max_points += rule.points
            hit = [c.name for c in cars if rule.test(c)]
            for n in hit:
                state.earned[n] += rule.points
                state.reasons[n].append((rule, rule.points))
            if hit:
                sign = "+" if rule.points > 0 else ""
                state.firings.append(Firing(step, qid, rule, hit, f"{sign}{rule.points}"))


def run(answers: list) -> State:
    """Replay a whole consultation. `answers` is a list of (qid, option_key)."""
    state = State()
    for qid, ans in answers:
        apply_answer(state, qid, ans)
    return state


# ---------------------------------------------------------------------------
# 2. Choosing the next question
# ---------------------------------------------------------------------------
def option_effect(qid: str, option: str, car: Car) -> float:
    """What would this answer do to this car? (ELIMINATED or net points)."""
    total = 0.0
    for rule in matching_rules(qid, option):
        if rule.kind == "require":
            if not rule.test(car):
                return ELIMINATED
            total += REQUIRE_BONUS
        elif rule.test(car):
            total += rule.points
    return total


def discrimination(q: Question, names: list) -> float:
    """How well a question separates these cars.

    For each option we measure the spread of its effect on the cars; the
    score blends the average spread and the best option's spread, so a
    question with many options (e.g. favourite company) is not undervalued.
    """
    if len(names) < 2:
        return 0.0
    cars = [CAR_BY_NAME[n] for n in names]
    spreads = []
    for key, _ in q.options:
        effects = [option_effect(q.id, key, c) for c in cars]
        spreads.append(max(effects) - min(effects))
    return (sum(spreads) / len(spreads) + max(spreads)) / 2


def leaders(state: State) -> list:
    """The leader plus every car within 1 point of it (at least two cars)."""
    ranking = state.ranking()
    best = state.earned[ranking[0]]
    group = [n for n in ranking if state.earned[n] >= best - 1]
    return group if len(group) >= 2 else ranking[:2]


def available(q: Question, state: State) -> bool:
    return q.id not in state.answers and (q.depends is None or q.depends(state.answers))


def next_question(state: State):
    """Return (Question, why_text) or (None, None) when nothing useful is left."""
    ranking = state.ranking()
    candidates = [q for q in QUESTIONS if available(q, state)]

    # Core questions first, in a fixed expert order - if they still matter.
    for qid in CORE_ORDER:
        q = QUESTIONS_BY_ID[qid]
        if q in candidates and discrimination(q, state.alive) > 0:
            return q, f"Core question: it narrows down the {len(state.alive)} cars still possible."

    top = ranking[:TOP_K]
    lead_group = leaders(state)
    best, best_value = None, 0.0
    for q in candidates:
        # Separating the leader from its closest rivals counts double.
        value = 2 * discrimination(q, lead_group) + discrimination(q, top)
        if value == 0 and discrimination(q, state.alive) > 0:
            value = 0.01                    # still useful for the wider pool
        if value > best_value:
            best, best_value = q, value
    if best is None:
        return None, None
    if discrimination(best, lead_group) > 0:
        why = "It can decide between the closest leaders: " + " and ".join(lead_group[:3]) + "."
    elif discrimination(best, top) > 0:
        why = "It best separates the current leaders: " + ", ".join(top[:3]) + "."
    else:
        why = f"It still separates some of the {len(state.alive)} remaining cars."
    return best, why


# ---------------------------------------------------------------------------
# 3. Stopping (is the answer clear yet?)
# ---------------------------------------------------------------------------
def should_stop(state: State):
    """Return (stop?, reason)."""
    ranking = state.ranking()
    if len(ranking) == 1:
        return True, "Only one car satisfies all of your requirements."
    q, _ = next_question(state)
    if q is None:
        return True, "No remaining question can change the recommendation."
    leader, second = ranking[0], ranking[1]
    lead = state.earned[leader] - state.earned[second]
    if state.asked >= MIN_QUESTIONS and not winner_can_change(state):
        return True, (f"{leader} stays on top whatever you answer next: "
                      f"no remaining question can change the winner ({state.match(leader):.0f}% match).")
    for min_asked, min_match, min_lead in STOP_TIERS:
        if state.asked >= min_asked and state.match(leader) >= min_match and lead >= min_lead:
            if lead == 0:
                return True, (f"{leader} and {second} fit you equally well ({state.match(leader):.0f}% match); "
                              f"{leader} wins the tie on resale value and price.")
            return True, (f"{leader} is the clear winner after {state.asked} questions: "
                          f"{state.match(leader):.0f}% match and {lead:.0f} points ahead of {second}.")
    return False, ""


def winner_can_change(state: State) -> bool:
    """Could any single remaining answer put a different car in first place?"""
    ranking = state.ranking()
    leader = CAR_BY_NAME[ranking[0]]
    rivals = [CAR_BY_NAME[n] for n in ranking[1:]]
    for q in QUESTIONS:
        if not available(q, state):
            continue
        for key, _ in q.options:
            lead_eff = option_effect(q.id, key, leader)
            if lead_eff == ELIMINATED:
                return True
            lead_total = state.earned[leader.name] + lead_eff
            for c in rivals:
                eff = option_effect(q.id, key, c)
                if eff != ELIMINATED and state.earned[c.name] + eff >= lead_total:
                    if state.earned[c.name] + eff > lead_total or eff != lead_eff:
                        return True
    return False


# ---------------------------------------------------------------------------
# 4. Explanation facility helpers (decision support)
# ---------------------------------------------------------------------------
def explain_car(state: State, name: str):
    """Positive and negative reasons for a car, strongest first."""
    pros = [(r, p) for r, p in state.reasons[name] if p > 0]
    cons = [(r, p) for r, p in state.reasons[name] if p < 0]
    pros.sort(key=lambda x: -x[1])
    cons.sort(key=lambda x: x[1])
    return pros, cons


def recommendation(state: State, top_n: int = 3) -> list:
    """Top N cars as (Car, match %, points)."""
    return [(CAR_BY_NAME[n], state.match(n), state.earned[n]) for n in state.ranking()[:top_n]]
