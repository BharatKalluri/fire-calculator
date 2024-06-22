import datetime
import locale

import pandas as pd
import streamlit as st
import plotly.graph_objects as go


def round_to_two(inp: float):
    return round(inp, 2)


def format_inr(number):
    locale.setlocale(locale.LC_ALL, "en_IN")
    return locale.currency(number, grouping=True)


def gen_table(
    current_income_per_year: float,
    current_expenses_per_year: float,
    capped_max_income_per_year: float,
    capped_max_expense_per_year: float,
    year_of_birth: int,
    predicted_max_age: int,
    salary_increment_yoy: float,
    inflation_rate_yoy: float,
    portfolio_growth_yoy: float,
    expenses_at_the_time_of_retirement: float,
    major_expenses: list = (),
    current_savings_in_market: float = 0,
) -> pd.DataFrame:

    current_year = datetime.datetime.now().year

    initial_disposable_income = round_to_two(
        current_income_per_year - current_expenses_per_year
    )

    fire_number = expenses_at_the_time_of_retirement * 25

    records = [
        {
            "year": current_year,
            "age": current_year - year_of_birth,
            "income": current_income_per_year,
            "expenses": current_expenses_per_year,
            "disposable_income": initial_disposable_income,
            "net_worth": initial_disposable_income + current_savings_in_market,
            "fire_diff": initial_disposable_income - fire_number,
            "fire_target": fire_number,
        }
    ]

    predicted_year_of_death = year_of_birth + predicted_max_age

    for year in range(current_year + 1, predicted_year_of_death + 1):
        latest_record = records[-1]

        age = year - year_of_birth
        revised_income = min(
            round_to_two(
                latest_record["income"]
                + (latest_record["income"] * (salary_increment_yoy / 100))
            ),
            capped_max_income_per_year,
        )
        revised_expenses = min(
            round_to_two(
                latest_record["expenses"]
                + (latest_record["expenses"] * (inflation_rate_yoy / 100))
            ),
            capped_max_expense_per_year,
        )
        disposable_income = round_to_two(revised_income - revised_expenses)
        major_expenses_of_year = sum(
            [el.get("expense") for el in major_expenses if el["year"] == year]
        )
        net_worth = (
            round_to_two(
                (
                    latest_record["net_worth"]
                    + (latest_record["net_worth"] * (portfolio_growth_yoy / 100))
                )
                + disposable_income
            )
            - major_expenses_of_year
        )
        fire_diff = net_worth - fire_number

        records.append(
            {
                "year": year,
                "age": age,
                "income": revised_income,
                "expenses": revised_expenses,
                "disposable_income": disposable_income,
                "net_worth": net_worth,
                "fire_target": fire_number,
                "fire_diff": fire_diff,
            }
        )

    return records


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("FIRE Calculator")
    column_one, column_two = st.columns(2)
    with column_one:
        current_income_per_year = st.number_input(
            label="Current Income per year",
            min_value=100000,
            max_value=10000000,
            value=1200000,
        )
        current_expenses_in_lakhs_per_year = st.number_input(
            label="Current Expenses per year",
            min_value=100000,
            max_value=10000000,
            value=600000,
        )
        capped_max_income_per_year = st.number_input(
            label="Capped Max Income per year",
            min_value=100000,
            max_value=100000000,
            value=10000000,
        )
        capped_max_expense_per_year = st.number_input(
            label="Capped Max Expenses per year",
            min_value=100000,
            max_value=10000000,
            value=7500000,
        )
        expenses_at_the_time_of_retirement = st.number_input(
            label="Expenses at the time of Retirement",
            min_value=100000,
            max_value=10000000,
            value=7500000,
        )

        year_of_birth = st.number_input(
            label="Year of Birth", min_value=1900, max_value=2021, value=1997
        )
        predicted_max_age = st.number_input(
            label="Predicted Max Age", min_value=60, max_value=100, value=60
        )
        current_savings_in_market = st.number_input(
            label="Current Savings in Market", min_value=0, max_value=10000000, value=0
        )

    with column_two:
        salary_increment_yoy = st.slider(
            label="Salary Increment YoY as %", min_value=1, max_value=100, value=10
        )
        inflation_rate_yoy = st.slider(
            label="Inflation Rate YoY as %", min_value=1, max_value=100, value=10
        )
        portfolio_growth_yoy = st.slider(
            label="Portfolio Growth YoY as %", min_value=1, max_value=100, value=10
        )
        major_expenses = st.text_area(
            "Major expenses (format: year,expense, description)", "2030,8000000,house"
        )
        major_expenses = [expense.split(",") for expense in major_expenses.split("\n")]
        major_expenses = [
            {
                "year": int(expense[0]),
                "expense": float(expense[1]),
                "description": expense[2],
            }
            for expense in major_expenses
        ]

    df_records = gen_table(
        current_income_per_year=current_income_per_year,
        current_expenses_per_year=current_expenses_in_lakhs_per_year,
        capped_max_income_per_year=capped_max_income_per_year,
        capped_max_expense_per_year=capped_max_expense_per_year,
        year_of_birth=year_of_birth,
        predicted_max_age=predicted_max_age,
        salary_increment_yoy=salary_increment_yoy,
        inflation_rate_yoy=inflation_rate_yoy,
        portfolio_growth_yoy=portfolio_growth_yoy,
        expenses_at_the_time_of_retirement=expenses_at_the_time_of_retirement,
        current_savings_in_market=current_savings_in_market,
        major_expenses=major_expenses,
    )
    df = pd.DataFrame(df_records)

    st.markdown(
        f"## FIRE @ ₹{format_inr(int(df.fire_target[0]))}. Can be achieved at {df[df['fire_diff'] > 0]['age'].min()}"
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=df["age"], y=df["fire_target"], mode="lines", name="Fire Target")
    )
    fig.add_trace(
        go.Scatter(
            x=df["age"],
            y=df["net_worth"],
            mode="lines",
            name="Net worth",
            fill="tozeroy",
        )
    )
    fig.update_layout(
        title="Fire Number Calculator",
        xaxis_title="Age",
        yaxis_title="Amount (in lakhs)",
    )
    st.plotly_chart(fig)

    st.markdown("## Data")

    st.table(
        df.style.format(
            {
                "income": format_inr,
                "expenses": format_inr,
                "disposable_income": format_inr,
                "net_worth": format_inr,
                "fire_target": format_inr,
                "fire_diff": format_inr,
            }
        )
    )
