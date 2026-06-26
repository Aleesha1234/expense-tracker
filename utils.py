
import os
import pandas as pd
from datetime import date

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH  = os.path.join(DATA_DIR, "expenses.csv")

# Column names kept consistent everywhere
COLUMNS = ["id", "date", "type", "category", "amount", "description"]

# Category lists shown in the Add Transaction form
INCOME_CATEGORIES  = ["Salary", "Freelance", "Business", "Investment", "Gift", "Other"]
EXPENSE_CATEGORIES = ["Food", "Transport", "Housing", "Healthcare",
                      "Entertainment", "Shopping", "Utilities", "Education", "Other"]


# ---------------------------------------------------------------------------
# CSV Initialisation
# ---------------------------------------------------------------------------

def _ensure_data_dir():
    """Create the data/ directory if it does not exist yet."""
    os.makedirs(DATA_DIR, exist_ok=True)


def initialize_csv():
    """
    Create expenses.csv with the correct header row if it does not exist.
    Safe to call on every app startup.
    """
    _ensure_data_dir()
    if not os.path.exists(CSV_PATH):
        empty_df = pd.DataFrame(columns=COLUMNS)
        empty_df.to_csv(CSV_PATH, index=False)


# ---------------------------------------------------------------------------
# Load & Save
# ---------------------------------------------------------------------------

def load_data() -> pd.DataFrame:
    """
    Read the CSV and return a DataFrame.
    Ensures correct dtypes regardless of how the file was created.
    """
    initialize_csv()
    df = pd.read_csv(CSV_PATH)

    if df.empty:
        # Return a typed empty frame so the rest of the app can rely on dtypes
        df = pd.DataFrame(columns=COLUMNS)
        df["amount"] = df["amount"].astype(float)
        df["date"]   = pd.to_datetime(df["date"])
        return df

    df["date"]   = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)
    df["id"]     = df["id"].astype(int)
    return df


def save_data(df: pd.DataFrame):
    """
    Persist the DataFrame to CSV.
    Dates are stored as YYYY-MM-DD strings.
    """
    _ensure_data_dir()
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(CSV_PATH, index=False)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def _next_id(df: pd.DataFrame) -> int:
    """Return the next available integer ID."""
    if df.empty or "id" not in df.columns:
        return 1
    return int(df["id"].max()) + 1


def add_transaction(
    txn_type: str,
    category: str,
    amount: float,
    txn_date: date,
    description: str,
) -> pd.DataFrame:
    """
    Append a new transaction row and save.

    Parameters
    ----------
    txn_type    : "Income" or "Expense"
    category    : category string
    amount      : positive float
    txn_date    : datetime.date object
    description : free-text description

    Returns the updated DataFrame.
    """
    df = load_data()

    new_row = pd.DataFrame([{
        "id":          _next_id(df),
        "date":        pd.Timestamp(txn_date),
        "type":        txn_type,
        "category":    category,
        "amount":      round(float(amount), 2),
        "description": description.strip(),
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    return df


def delete_transaction(row_id: int) -> pd.DataFrame:
    """
    Remove the row with the given id and save.

    Returns the updated DataFrame.
    """
    df = load_data()
    df = df[df["id"] != row_id].reset_index(drop=True)
    save_data(df)
    return df


# ---------------------------------------------------------------------------
# Summary / KPIs
# ---------------------------------------------------------------------------

def get_summary(df: pd.DataFrame) -> dict:
    """
    Compute top-level financial summary.

    Returns a dict with:
      total_income, total_expenses, balance
    """
    if df.empty:
        return {"total_income": 0.0, "total_expenses": 0.0, "balance": 0.0}

    income   = df.loc[df["type"] == "Income",  "amount"].sum()
    expenses = df.loc[df["type"] == "Expense", "amount"].sum()
    return {
        "total_income":    round(income, 2),
        "total_expenses":  round(expenses, 2),
        "balance":         round(income - expenses, 2),
    }


# ---------------------------------------------------------------------------
# Filtering & Sorting
# ---------------------------------------------------------------------------

def filter_transactions(
    df: pd.DataFrame,
    txn_type: str   = "All",
    category: str   = "All",
    keyword: str    = "",
    sort_order: str = "Newest First",
) -> pd.DataFrame:
    """
    Apply search / filter / sort to the transactions DataFrame.

    Parameters
    ----------
    txn_type   : "All", "Income", or "Expense"
    category   : "All" or a specific category string
    keyword    : substring search across description and category
    sort_order : "Newest First" or "Oldest First"

    Returns a filtered and sorted copy of the DataFrame.
    """
    result = df.copy()

    # Filter by transaction type
    if txn_type != "All":
        result = result[result["type"] == txn_type]

    # Filter by category
    if category != "All":
        result = result[result["category"] == category]

    # Keyword search across description and category (case-insensitive)
    if keyword.strip():
        kw = keyword.strip().lower()
        mask = (
            result["description"].str.lower().str.contains(kw, na=False) |
            result["category"].str.lower().str.contains(kw, na=False)
        )
        result = result[mask]

    # Sort by date
    ascending = sort_order == "Oldest First"
    result = result.sort_values("date", ascending=ascending).reset_index(drop=True)

    return result


# ---------------------------------------------------------------------------
# Chart Data Helpers
# ---------------------------------------------------------------------------

def expense_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return total expenses grouped by category, sorted descending.
    Returns an empty DataFrame if there are no expense rows.
    """
    expenses = df[df["type"] == "Expense"]
    if expenses.empty:
        return pd.DataFrame(columns=["category", "amount"])
    grouped = (
        expenses.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )
    return grouped


def monthly_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return total expenses grouped by year-month (YYYY-MM), sorted ascending.
    Returns an empty DataFrame if there are no expense rows.
    """
    expenses = df[df["type"] == "Expense"].copy()
    if expenses.empty:
        return pd.DataFrame(columns=["month", "amount"])
    expenses["month"] = expenses["date"].dt.to_period("M").astype(str)
    grouped = (
        expenses.groupby("month", as_index=False)["amount"]
        .sum()
        .sort_values("month")
    )
    return grouped


def monthly_income_vs_expense(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return monthly totals for both Income and Expense side-by-side.
    Useful for a grouped bar chart.
    """
    if df.empty:
        return pd.DataFrame(columns=["month", "type", "amount"])
    tmp = df.copy()
    tmp["month"] = tmp["date"].dt.to_period("M").astype(str)
    grouped = (
        tmp.groupby(["month", "type"], as_index=False)["amount"]
        .sum()
        .sort_values("month")
    )
    return grouped


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Serialise the DataFrame to CSV bytes ready for Streamlit's
    st.download_button.
    """
    out = df.copy()
    if not out.empty:
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out.to_csv(index=False).encode("utf-8")
