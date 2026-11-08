# 🚗 GaariGuide – Car Recommendation Expert System

GaariGuide is a rule-based **expert system** that recommends the best car for a buyer in the
**Pakistani market**. Like a doctor asking about symptoms, it asks the buyer about their needs
(budget, family, roads, fuel, features...). It then reasons with **180 IF-THEN rules** and recommends
a car, **stopping as soon as the answer is clear** (usually after 10–15 of its 59 questions).

It is both:
- **Decision making system**: it gives one final recommended car and the reason it stopped.
- **Decision support system**: it shows the top 3 alternatives with a match %, why this car and its
  trade-offs, a comparison table, the full reasoning trace, the eliminated cars, and what-if answer changes.

## Features
- **59-question knowledge base** in 9 categories: budget, family, usage, roads, engine & fuel,
  driving, ownership, features & safety, brand & style
- **180 production rules**:
  - *eliminate* rules (hard constraints)
  - *score* rules (preferences)
- **Fact base of 49 cars**: new and used, local and imported, petrol, hybrid, EV and diesel
- **Forward-chaining inference engine** with conflict resolution: a hard rule that would remove every
  remaining car is relaxed into a penalty
- **Smart questioning**:
  - asks the question that best separates the current leaders
  - skips irrelevant questions
- **Dynamic stopping**: no fixed number of questions, so clear users finish quickly and unsure users
  are asked more
- **Explanation facility**: "Why is the expert asking this?", the live reasoning panel, and a rule-by-rule trace
- **What-if analysis**: change any earlier answer and see the decision update
- **Animated single-page experience**:
  - landing screen
  - each question drops in from the top while its answer cards fly in from the left and right
  - on Next, the question exits upward and the cards exit downward
  - the result screen has a counting match ring and confetti
  - responsive on desktop, tablet and mobile
- Downloadable text report
- **Knowledge base browser**: every rule, question and car in searchable tables (opened from the landing screen)

## Tech stack
- Python 3.10+
- Streamlit (UI)
- pandas (tables)

## Getting started
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
Open http://localhost:8501.

## Project structure
```
streamlit_app.py           Streamlit user interface (screens and dialogs)
app.py                     Inference engine (rule firing, question selection, stopping)
ui/
  style.css                Theme, layout and all entrance/exit animations
  motion.js                Exit-animation timing and confetti (no libraries)
knowledge_base/
  cars.py                  Fact base: 49 cars and their attributes
  rules.py                 59 questions and 180 IF-THEN rules
.streamlit/config.toml     Dark theme, hidden toolbar
requirements.txt
```

## How the reasoning works
1. Every car starts as a candidate.
2. Each answer fires the rules of its question:
   - an **eliminate** rule removes cars that fail it (`IF passengers = 6-7 THEN keep only cars with 7+ seats`);
   - a **score** rule adds or subtracts points (`IF fuel budget = tight AND car gives 18+ km/l THEN +3`).
3. The next question is the one that best separates the leading cars.
4. The engine stops when one of these is true:
   - only one car is left;
   - no single remaining answer could change the winner;
   - the leader is confident enough (75%+ match and a 5-point lead after 10 questions, relaxing after 15, 20 and 25);
   - no useful question is left.
5. Match % = points earned ÷ points possible for the answers given.

## Disclaimer
Car prices and specifications are approximate and are for academic demonstration only.

## License
Academic project – Introduction to Artificial Intelligence course.
