"""
GaariGuide - a car recommendation expert system for the Pakistani market.
User interface (Streamlit). Run with:  streamlit run streamlit_app.py

All reasoning lives in app.py (inference engine) and knowledge_base/.
This file only draws the single-page experience:
    landing  ->  questions (animated)  ->  recommendation (+ decision support)
Styling is in ui/style.css and the exit/confetti animations in ui/motion.js.
"""

import html
import json
import zlib
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import app
from knowledge_base.cars import CARS
from knowledge_base.rules import QUESTIONS, QUESTIONS_BY_ID, RULES, SKIP

UI_DIR = Path(__file__).parent / "ui"

st.set_page_config(page_title="GaariGuide - Car Expert System", page_icon="🚗",
                   layout="centered", initial_sidebar_state="collapsed")


def raw(markup: str):
    """Render HTML in the page itself (st.html isolates its content, so CSS would not reach it).
    Lines are stripped so Markdown never mistakes indented HTML for a code block."""
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


raw(f"<style>{(UI_DIR / 'style.css').read_text(encoding='utf-8')}</style>")

# ---------------------------------------------------------------- session ---
ss = st.session_state
ss.setdefault("started", False)   # landing screen passed
ss.setdefault("answers", [])      # list of (qid, option)
ss.setdefault("finished", False)  # user pressed "show result now"


def start():
    ss.started = True


def restart():
    ss.answers = []
    ss.finished = False
    ss.started = True


def go_back(to_index=None):
    ss.answers = ss.answers[:-1] if to_index is None else ss.answers[:to_index]
    ss.finished = False


def submit(qid, widget_key):
    """Record the selected option for this question (Next button)."""
    choice = ss.get(widget_key)
    if choice is not None:
        ss.answers = ss.answers + [(qid, choice)]


def finish_now():
    ss.finished = True


def motion(token: str = "", confetti: bool = False):
    """Load ui/motion.js into the main page once; optionally fire confetti."""
    js = (UI_DIR / "motion.js").read_text(encoding="utf-8")
    fire = f"P.ggConfetti && P.ggConfetti({json.dumps(token)});" if confetti else ""
    components.html(f"""<script>
      (function () {{
        var P = window.parent, D = P.document;
        if (!P.__ggMotion) {{
          var s = D.createElement('script');
          s.textContent = {json.dumps(js)};
          D.head.appendChild(s);
        }}
        {fire}
      }})();
    </script><!-- {token} -->""", height=0)


# ---------------------------------------------------------------- helpers ---
def esc(text) -> str:
    return html.escape(str(text))


def fmt_price(lakh: float) -> str:
    return f"Rs {lakh / 100:.2f} crore" if lakh >= 100 else f"Rs {lakh:.0f} lakh"


def car_specs(car) -> dict:
    return {
        "Car": car.name,
        "Price (approx.)": fmt_price(car.price),
        "Condition": car.condition.title(),
        "Body": car.body.upper() if car.body in ("suv", "mpv") else car.body.title(),
        "Seats": car.seats,
        "Engine": "Electric" if car.cc == 0 else f"{car.cc} cc",
        "Fuel": car.fuel.upper() if car.fuel in ("ev", "phev") else car.fuel.title(),
        "Transmission": " / ".join(t.title() for t in car.trans),
        "Fuel economy": "Electric" if car.fuel == "ev" else f"{car.kmpl:g} km/l",
        "Ground clearance": f"{car.clearance} mm",
        "Airbags": car.airbags,
        "Resale (1-5)": car.resale,
        "Parts (1-5)": car.parts,
        "Comfort (1-5)": car.comfort,
    }


def match_message(pct: float) -> str:
    if pct >= 95:
        return "A perfect fit for everything you told us."
    if pct >= 80:
        return "An excellent match for your needs."
    if pct >= 65:
        return "A strong match with a few trade-offs."
    return "The best fit among the cars available."


def cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def build_report(state, reason, top) -> str:
    lines = ["GaariGuide - Car Recommendation Report", "=" * 40, "",
             f"Decision: {top[0][0].name} ({top[0][1]:.0f}% match, {fmt_price(top[0][0].price)})",
             f"Reason: {reason}", "", "Alternatives:"]
    lines += [f"  {i}. {c.name} - {m:.0f}% match, {fmt_price(c.price)}" for i, (c, m, _) in enumerate(top[1:], 2)]
    lines += ["", f"Your answers ({state.asked} questions):"]
    for i, qid in enumerate(state.order, 1):
        q = QUESTIONS_BY_ID[qid]
        lines.append(f"  Q{i}. {q.text} -> {q.label(state.answers[qid])}")
    lines += ["", "Rules fired:"]
    for f in state.firings:
        lines.append(f"  Q{f.step} {f.rule.id} [{f.effect}] {f.rule.describe(QUESTIONS_BY_ID)}")
    lines += ["", "Prices are approximate and for demonstration only."]
    return "\n".join(lines)


# ================================================================ DIALOGS ===
@st.dialog("Knowledge base", width="large")
def knowledge_dialog():
    a, b, c, d = st.columns(4)
    a.metric("Questions", len(QUESTIONS))
    b.metric("Rules (IF-THEN)", len(RULES))
    c.metric("Hard rules", sum(r.kind == "require" for r in RULES))
    d.metric("Cars (facts)", len(CARS))
    t1, t2, t3 = st.tabs(["Rules", "Questions", "Cars"])
    with t1:
        cat = {q.id: q.category for q in QUESTIONS}
        rows = [{"ID": r.id, "Category": cat[r.qid], "Type": "Eliminate" if r.kind == "require" else "Score",
                 "Rule": r.describe(QUESTIONS_BY_ID)} for r in RULES]
        df = pd.DataFrame(rows)
        pick = st.multiselect("Filter by category", sorted(df.Category.unique()))
        if pick:
            df = df[df.Category.isin(pick)]
        st.dataframe(df, hide_index=True, width="stretch", height=460)
    with t2:
        rows = [{"#": i + 1, "Category": q.category, "Question": q.text,
                 "Options": ", ".join(lbl for _, lbl in q.options),
                 "Rules": len(app.RULES_BY_QUESTION.get(q.id, []))} for i, q in enumerate(QUESTIONS)]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=460)
    with t3:
        st.dataframe(pd.DataFrame([car_specs(c) for c in CARS]), hide_index=True, width="stretch", height=460)


@st.dialog("Why this question?", width="large")
def why_dialog(state, why):
    st.markdown(f"**{why}**")
    st.caption("Live reasoning - how the inference engine currently ranks the cars:")
    if state.asked:
        rows = [{"Rank": i + 1, "Car": n, "Match %": round(state.match(n)), "Points": state.earned[n]}
                for i, n in enumerate(state.ranking()[:6])]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        last = [f for f in state.firings if f.step == state.asked]
        if last:
            st.caption("Rules fired by your last answer:")
            for f in last:
                st.markdown(f"- **{f.rule.id}** ({f.effect}, {len(f.cars)} cars): {f.rule.describe(QUESTIONS_BY_ID)}")
        else:
            st.caption("Your last answer fired no rules.")
    else:
        st.caption(f"All {len(CARS)} cars are still possible - answer this question to start the reasoning.")


# ================================================================ LANDING ===
def landing():
    with st.container(key="stage_landing"):
        raw("""
        <div class="gg-hero">
          <div class="gg-badge"><span class="gg-dot"></span>AI expert system · Pakistani car market</div>
          <div class="gg-title">Gaari<span>Guide</span></div>
          <div class="gg-sub">Tell us how you live, drive and spend. Our rule-based expert reasons like a seasoned
             car advisor and stops the moment it knows your perfect car.</div>
        </div>""")
        with st.container(key="go_start_wrap", horizontal=True, horizontal_alignment="center"):
            st.button("Start  →", key="go_start", type="primary", on_click=start)
        with st.container(key="landing_links", horizontal=True, horizontal_alignment="center"):
            if st.button("Knowledge base", key="kb_link", type="tertiary"):
                knowledge_dialog()
    motion("landing")


# =================================================================== QUIZ ===
def question_screen(state, q, why):
    total = len(CARS)
    prev_alive = len(app.run(ss.answers[:-1]).alive) if ss.answers else total
    pct = lambda alive: round(100 * (1 - (alive - 1) / (total - 1)))  # noqa: E731
    raw(f"""
    <div class="gg-meta">
      <div class="gg-step">Question {state.asked + 1} <em>· {esc(q.category)}</em></div>
      <div class="gg-track"><div style="--from:{pct(prev_alive)};--to:{pct(len(state.alive))}"></div></div>
      <div class="gg-left"><b>{len(state.alive)}</b> of {total} cars still in the race</div>
    </div>""")

    stage = f"stage_q{state.asked}_{q.id}"
    widget_key = f"ans_{state.asked}_{q.id}"
    with st.container(key=stage):
        raw(f"<div class='gg-q'>{esc(q.text)}</div>"
                + (f"<div class='gg-help'>{esc(q.help)}</div>" if q.help else "<div class='gg-gap'></div>"))
        keys = [k for k, _ in q.options] + [SKIP]
        choice = st.radio("Your answer", keys, index=None, format_func=q.label,
                          key=widget_key, label_visibility="collapsed")

        b1, b2, b3 = st.columns([1, 1.5, 1], vertical_alignment="center")
        with b1:
            st.button("←  Back", key=f"go_back_{state.asked}", type="tertiary",
                      disabled=not ss.answers, on_click=go_back)
        with b2:
            st.button("Next  →", key=f"go_next_{state.asked}", type="primary", width="stretch",
                      disabled=choice is None, on_click=submit, args=(q.id, widget_key))
        with b3:
            st.button("Show result", key=f"go_finish_{state.asked}", type="tertiary",
                      disabled=state.asked < 3, on_click=finish_now,
                      help="Stop here and see the best match so far")
        with st.container(key="why_row", horizontal=True, horizontal_alignment="center"):
            if st.button("Why is the expert asking this?", key=f"why_{state.asked}", type="tertiary"):
                why_dialog(state, why)
    motion(f"q{state.asked}")


# ================================================================= RESULT ===
def result_screen(state, reason):
    top = app.recommendation(state, 3)
    best, best_match, _ = top[0]
    specs = car_specs(best)
    pros, cons = app.explain_car(state, best.name)

    chips, seen = [], set()
    for r, _ in pros:
        if r.kind == "require" or r.cond in seen:
            continue
        seen.add(r.cond)
        chips.append(f"<span class='gg-chip ok'>{esc(cap(r.cond))}</span>")
        if len(chips) >= 5:
            break
    musts = {r.id for r, _ in pros if r.kind == "require"}
    if musts:
        chips.append(f"<span class='gg-chip ok'>Meets all {len(musts)} of your must-haves</span>")
    chips += [f"<span class='gg-chip warn'>{esc(cap(r.cond))}</span>" for r, _ in cons[:2]]

    name = esc(best.name)
    first, _, rest = name.partition(" ")
    signature = "|".join(f"{q}={a}" for q, a in ss.answers) + f"|{ss.finished}"

    with st.container(key=f"stage_result_{zlib.crc32(signature.encode())}"):
        raw(f"""
        <div class="gg-res">
          <div class="gg-eyebrow">Your perfect match</div>
          <div class="gg-ring" style="--target:{best_match:.0f}">
            <div class="gg-ring-num"><span class="gg-count" style="--target:{best_match:.0f}"></span><small>% match</small></div>
          </div>
          <div class="gg-msg">{match_message(best_match)}</div>
          <div class="gg-car">{first} <span>{rest}</span></div>
          <div class="gg-sub2">{esc(best.company)} · {esc(specs['Body'])} · {best.seats} seats · {esc(specs['Engine'])} · {esc(specs['Transmission'])}</div>
          <div class="gg-facts">
            <div><b>{esc(fmt_price(best.price))}</b><span>Approx. price</span></div>
            <div><b>{esc(specs['Fuel economy'])}</b><span>Fuel economy</span></div>
            <div><b>{best.airbags}</b><span>Airbags</span></div>
            <div><b>{best.resale}/5</b><span>Resale</span></div>
          </div>
          <div class="gg-chips">{''.join(chips)}</div>
          <div class="gg-why-stop">{esc(reason)}{' ' + esc(best.notes) if best.notes else ''}</div>
        </div>""")

        with st.container(key="result_actions", horizontal=True, horizontal_alignment="center",
                          vertical_alignment="center"):
            st.button("↻  Start again", key="go_restart", type="primary", on_click=restart)
            st.download_button("Download report", data=build_report(state, reason, top),
                               file_name="GaariGuide_report.txt", mime="text/plain")
            st.button("←  Back one question", key="go_back_result", type="tertiary", on_click=go_back)

        # ---- DECISION SUPPORT ----
        raw("<div class='gg-h'>Explore the decision</div>"
                "<div class='gg-hsub'>Alternatives, the full reasoning and what-if changes.</div>")
        with st.container(key="explore"):
            t0, t1, t2, t3, t4 = st.tabs(["Alternatives", "Comparison", "Reasoning trace", "Eliminated", "Your answers"])
            with t0:
                rows = "".join(
                    f"<div class='gg-alt'><div class='gg-alt-rank'>{i}</div>"
                    f"<div class='gg-alt-main'><div class='gg-alt-name'>{esc(c.name)}</div>"
                    f"<div class='gg-alt-meta'>{esc(fmt_price(c.price))} · {esc(car_specs(c)['Body'])} · "
                    f"{esc(car_specs(c)['Fuel economy'])}</div></div>"
                    f"<div class='gg-alt-bar'><div style='width:{m:.0f}%'></div></div>"
                    f"<div class='gg-alt-pct'>{m:.0f}%</div></div>"
                    for i, (c, m, _) in enumerate(top, 1))
                raw(f"<div>{rows}</div>")
            with t1:
                df = pd.DataFrame([car_specs(c) for c, _, _ in top]).set_index("Car").T
                st.dataframe(df, width="stretch")
            with t2:
                st.caption("Every rule the inference engine fired, step by step (explanation facility).")
                for step, qid in enumerate(state.order, start=1):
                    q = QUESTIONS_BY_ID[qid]
                    fired = [f for f in state.firings if f.step == step]
                    with st.expander(f"Q{step}. {q.text} → {q.label(state.answers[qid])}  ({len(fired)} rules fired)"):
                        if not fired:
                            st.write("No rule fired (answer was neutral or skipped).")
                        for f in fired:
                            shown = ", ".join(f.cars[:6]) + (" ..." if len(f.cars) > 6 else "")
                            st.markdown(f"**{f.rule.id}** · `{f.effect}` · {f.rule.describe(QUESTIONS_BY_ID)}  \n"
                                        f"<span style='color:var(--muted)'>Affected: {esc(shown)}</span>",
                                        unsafe_allow_html=True)
                if state.relaxed:
                    st.warning("Relaxed rules (no remaining car could satisfy them, so they became penalties): "
                               + ", ".join(r.id for r in state.relaxed))
            with t3:
                rows = [{"Car": n, "Eliminated at": f"Q{step}", "Rule": rule.id, "Because": rule.cond}
                        for n, (step, qid, rule) in state.eliminated.items()]
                if rows:
                    st.dataframe(pd.DataFrame(rows).sort_values("Eliminated at", key=lambda s: s.str[1:].astype(int)),
                                 hide_index=True, width="stretch")
                else:
                    st.write("No car was eliminated.")
            with t4:
                st.caption("Change any answer to see how the decision changes (what-if analysis).")
                for i, qid in enumerate(state.order):
                    q = QUESTIONS_BY_ID[qid]
                    a, b = st.columns([5, 1], vertical_alignment="center")
                    a.markdown(f"**Q{i + 1}.** {q.text}  \n→ {q.label(state.answers[qid])}")
                    b.button("Change", key=f"go_chg_{i}", on_click=go_back, args=(i,), type="tertiary")
    motion(f"result-{signature}", confetti=True)


# =================================================================== MAIN ===
if not ss.started:
    landing()
else:
    state = app.run(ss.answers)
    stop, reason = app.should_stop(state)
    if ss.finished and not stop:
        stop, reason = True, f"You asked for the result after {state.asked} questions (best match so far)."
    if stop:
        result_screen(state, reason)
    else:
        q, why = app.next_question(state)
        question_screen(state, q, why)
