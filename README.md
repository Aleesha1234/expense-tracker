# 💰 Personal Expense Tracker

A clean, modern Personal Expense Tracker built with **Python**, **Streamlit**, **Pandas**, and **Plotly**.  
All data is stored locally in a CSV file — no database required.

---

## Features

| Feature | Details |
|---|---|
| 📊 Dashboard | KPI cards (Income, Expenses, Balance) + monthly overview chart |
| ➕ Add Transaction | Income or Expense with category, date, amount, description |
| 📋 View Transactions | Sort, search by keyword, filter by type and category, delete rows |
| 📈 Charts | Expense pie chart by category + monthly bar charts |
| 💾 Export | Download full transaction history as a timestamped CSV file |

---

## Project Structure

```
expense-tracker/
│── app.py               # Streamlit app — all pages and UI
│── utils.py             # Data access helpers (load, save, filter, charts)
│── requirements.txt     # Python dependencies
│── README.md            # This file
│── data/
│   └── expenses.csv     # Auto-created on first run
```

---

## Requirements

- Python **3.10** or higher
- pip

---

## Installation & Running (Windows — VS Code / Command Prompt)

### 1. Open a terminal in the project folder

In VS Code: **Terminal → New Terminal**, then make sure you are inside `expense-tracker/`.

```bash
cd expense-tracker
```

### 2. (Recommended) Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app will open automatically in your default browser at `http://localhost:8501`.

---

## Installation & Running (macOS / Linux)

```bash
cd expense-tracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Data Storage

All transactions are saved to `data/expenses.csv` automatically.  
The file is created on the first run — no setup required.

**CSV columns:**

| Column | Type | Description |
|---|---|---|
| id | integer | Auto-incremented unique ID |
| date | YYYY-MM-DD | Transaction date |
| type | Income / Expense | Transaction type |
| category | string | Category label |
| amount | float | Amount in Rupees |
| description | string | Optional free-text note |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| streamlit | ≥ 1.32 | Web UI framework |
| pandas | ≥ 2.0 | CSV data manipulation |
| plotly | ≥ 5.18 | Interactive charts |

---

## Stopping the App

Press **Ctrl + C** in the terminal to stop the Streamlit server.  
To deactivate the virtual environment:

```bash
deactivate
```
