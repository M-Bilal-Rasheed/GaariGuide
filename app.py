"""
INFERENCE ENGINE of GaariGuide.

Forward chaining with candidate elimination + scoring:

  1. Start with every car in the fact base as a candidate.
  2. For each answer, FIRE the rules of that question (check_rules in
     knowledge.py) on every car that is still possible:
       - "drop"  -> the car fails an eliminate rule and is removed
                    (if a rule would remove ALL cars, it becomes a -3 penalty
                     instead: conflict resolution)
       - "keep"  -> the car passes an eliminate rule (+2 points)
       - +N / -N -> score points for the car
  3. Choose the NEXT question dynamically: the one that best separates
     the leading candidates (questions that cannot change anything are skipped).
  4. STOP as soon as the answer is clear (one car left, or a confident
     leader), otherwise keep asking - there is no fixed question count.
  5. DIAGNOSE the buyer (type, needs, conflicting requirements).

The engine is a pure function of the answers given so far, so going
"back" or changing an answer simply re-runs it.
"""

from dataclasses import dataclass, field

from knowledge import (CAR_BY_NAME, CARS, CORE_ORDER, QUESTIONS, QUESTIONS_BY_ID, SKIP,
                       check_rules, diagnose_buyer, is_relevant, rules_for)

# ---- tuning knobs ----------------------------------------------------------
# Stopping tiers: (min questions asked, min match % of leader, min point lead over #2).
# The longer the consultation, the less certainty is needed to decide, so a
# clear user finishes in ~10-15 questions and an unsure user is asked more.
STOP_TIERS = [(10, 75, 5), (15, 70, 1), (20, 70, 0), (25, 0, 0)]
MIN_QUESTIONS = 10       # never decide earlier unless only one car is left
REQUIRE_BONUS = 2        # points a car earns for passing an eliminate rule
TOP_K = 5                # how many leading cars the question selector looks at
ELIMINATED = -10         # effect value used when simulating an elimination


@dataclass
class Firing:
    """One rule that fired during a consultation (for the explanation facility)."""
    step: int
    qid: str
    rule: object          # the Rule (id, condition text ...)
    cars: list            # names of cars the rule affected
    effect: str           # "eliminated" | "relaxed" | "+3" | "-2"


@dataclass
class State:
    """Working memory: everything the expert knows so far."""
    answers: dict = field(default_factory=dict)            # question -> answer
    order: list = field(default_factory=list)              # questions in the order asked
    alive: list = field(default_factory=lambda: [c.name for c in CARS])
    eliminated: dict = field(default_factory=dict)         # car -> (step, question, Rule)
    earned: dict = field(default_factory=lambda: {c.name: 0.0 for c in CARS})
    max_points: float = 0.0
    firings: list = field(default_factory=list)
    reasons: dict = field(default_factory=lambda: {c.name: [] for c in CARS})  # car -> [(Rule, pts)]
    relaxed: list = field(default_factory=list)            # rules that had to be relaxed

    def match(self, name):
        """Match percentage of a car: points earned / points possible."""
        if self.max_points <= 0:
            return 0.0
        return max(0.0, min(100.0, 100.0 * self.earned[name] / self.max_points))

    def ranking(self):
        """Cars still possible, best first (ties broken by resale value, then lower price)."""
        return sorted(self.alive, key=lambda n: (-self.earned[n], -CAR_BY_NAME[n].resale, CAR_BY_NAME[n].price))

    @property
    def asked(self):
        return len(self.order)


# ---------------------------------------------------------------------------
# 1. Rule firing (forward chaining)
# ---------------------------------------------------------------------------
def apply_answer(state, qid, answer):
    """Fire every rule of this answer on the cars that are still possible."""
    step = len(state.order) + 1
    state.answers[qid] = answer
    state.order.append(qid)
    if answer == SKIP:
        return

    # Ask the knowledge base what each rule says about each car.
    results = {}                                   # car -> {rule id: effect}
    for name in state.alive:
        results[name] = {}
        for rule_id, effect, _ in check_rules(qid, answer, CAR_BY_NAME[name]):
            results[name][rule_id] = effect

    for rule in rules_for(qid, answer):
        cars = list(state.alive)
        if rule.kind == "require":
            state.max_points += REQUIRE_BONUS
            passing = [n for n in cars if results[n].get(rule.id) == "keep"]
            failing = [n for n in cars if results[n].get(rule.id) == "drop"]
            if not passing:
                # Conflict resolution: no car left can satisfy this rule,
                # so it becomes a strong preference instead of a hard filter.
                state.relaxed.append(rule)
                for n in failing:
                    state.earned[n] -= 3
                    state.reasons[n].append((rule, -3))
                state.firings.append(Firing(step, qid, rule, failing, "relaxed"))
            else:
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
            hit = [n for n in cars if rule.id in results[n]]
            for n in hit:
                state.earned[n] += rule.points
                state.reasons[n].append((rule, rule.points))
            if hit:
                sign = "+" if rule.points > 0 else ""
                state.firings.append(Firing(step, qid, rule, hit, f"{sign}{rule.points}"))


def run(answers):
    """Replay a whole consultation. `answers` is a list of (question, answer)."""
    state = State()
    for qid, ans in answers:
        apply_answer(state, qid, ans)
    return state


# ---------------------------------------------------------------------------
# 2. Choosing the next question
# ---------------------------------------------------------------------------
def option_effect(qid, option, car):
    """What would this answer do to this car? (ELIMINATED or net points)."""
    total = 0
    for _, effect, _ in check_rules(qid, option, car):
        if effect == "drop":
            return ELIMINATED
        elif effect == "keep":
            total += REQUIRE_BONUS
        else:
            total += effect
    return total


def discrimination(q, names):
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


def leaders(state):
    """The leader plus every car within 1 point of it (at least two cars)."""
    ranking = state.ranking()
    best = state.earned[ranking[0]]
    group = [n for n in ranking if state.earned[n] >= best - 1]
    if len(group) >= 2:
        return group
    return ranking[:2]


def available(q, state):
    """Not asked yet, and it makes sense after the earlier answers."""
    return q.id not in state.answers and is_relevant(q.id, state.answers)


def next_question(state):
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
# 3. Stopping (is the answer clear yet?) - the DECISION
# ---------------------------------------------------------------------------
def should_stop(state):
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


def winner_can_change(state):
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
# 4. Explanations (decision support) and diagnosis
# ---------------------------------------------------------------------------
def explain_car(state, name):
    """Positive and negative reasons for a car, strongest first."""
    pros = [(r, p) for r, p in state.reasons[name] if p > 0]
    cons = [(r, p) for r, p in state.reasons[name] if p < 0]
    pros.sort(key=lambda x: -x[1])
    cons.sort(key=lambda x: x[1])
    return pros, cons


def diagnose(state):
    """DIAGNOSIS: the buyer's type, needs and conflicts, found from the answers."""
    profile, needs, conflicts = diagnose_buyer(state.answers)
    # Conflicts the engine found itself: eliminate rules no remaining car could meet.
    for r in state.relaxed:
        conflicts.append((r.id, f"No car left meets this rule, so it became a -3 penalty: {r.describe()}."))
    return {"profile": profile, "needs": needs, "conflicts": conflicts}


def recommendation(state, top_n=3):
    """Top N cars as (Car, match %, points)."""
    return [(CAR_BY_NAME[n], state.match(n), state.earned[n]) for n in state.ranking()[:top_n]]
