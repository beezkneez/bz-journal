# 📓 Streamlit Trading Journal

## 📌 Purpose
This project is a **personal trading journal app** built with **Python + Streamlit**.  
It helps me:
- Record **pre-trade notes** (setup, reasoning, entry/exit plan).
- Record **post-trade reflections** (screenshot, grading, emotional state).
- Track **PnL, fees, and commissions**.
- Visualize performance with interactive dashboards.

---

## 🛠️ Tech Stack
- **Python 3.11+**
- **Streamlit** → UI framework
- **Pandas** → data handling
- **Plotly/Altair/Matplotlib** → visualizations
- **SQLite (later)** → trade storage (start with CSV for simplicity)

---

## 🚦 Current Status
- [ ] Pre-trade entry form (description, stop, target, emotions, sleep, shift info).
- [ ] Post-trade form (screenshot upload, grading, reflection).
- [ ] Save to CSV (later upgrade to SQLite).
- [ ] Dashboard:
  - PnL over time
  - Average fees/commissions
  - Filters (by shift, sleep, emotion, grade)
- [ ] Export trades/report as CSV or PDF.

---

## 🎯 Goals
- Lightweight, local app (`streamlit run app.py`).
- Easy to log trades quickly (no clutter).
- Data should be easy to analyze later.
- Dashboard insights should connect **performance vs. emotions, sleep, and work shifts**.
- Future: add **automatic fee/commission analysis**.

---

## 🔍 Coding Guidelines
- **PEP8 compliant** and readable.
- Use **functions + type hints** where possible.
- Keep code modular (UI, data, analysis separated).
- Comment logic that isn’t obvious.
- Use **Streamlit best practices** (`st.form`, `st.session_state`, layout containers).

---

## 🧪 Example AI Tasks
When I ask for help, here’s how I’d like responses structured:

1. **Bug fixing**
   - Identify cause of error in code.
   - Suggest corrected snippet (not just explanation).

2. **Feature extension**
   - Example: Add ability to upload and save screenshots.
   - Example: Add chart showing average commissions.

3. **Optimization**
   - Simplify repetitive code.
   - Improve performance on large CSVs.

4. **UI improvements**
   - Better layout using `st.columns`, `st.tabs`, etc.
   - Clean and minimal look.

5. **Analysis support**
   - If I upload/export trades as CSV/PDF, calculate:
     - Average fees/commissions per trade
     - PnL breakdown
     - Performance by emotional state, sleep, or shift type

---

## ✅ Rules for AI Assistance
- Always provide **working code snippets** (not pseudocode).
- Assume environment:
  - **Windows 10**
  - **Python 3.11**
  - **Streamlit (latest)**
  - Running in **VS Code**
- Keep answers **scoped to Python + Streamlit** unless I ask otherwise.

---

## 🗂️ Project Structure (planned)
trading-journal/
.devcontainer/
.github/
screenshots/
.gitignore
LICENSE
README.md
requirements.txt
streamlit_app.py
trading_journal_data.json
