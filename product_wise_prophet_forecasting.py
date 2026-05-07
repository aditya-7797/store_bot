"""
Product-wise Time-Series Sales Forecasting using Prophet.

Install dependency:
    pip install prophet
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd

warnings.filterwarnings("ignore")


DATA_PATH = "grocery_sales_dataset.csv"
FORECAST_DAYS = 30
OUTPUT_CSV = "product_wise_prophet_forecast_next_30_days.csv"

TARGET_PRODUCTS = [
    "Rice",
    "Wheat Flour",
    "Milk",
    "Sugar",
    "Salt",
    "Cooking Oil",
    "Eggs",
    "Bread",
    "Tea",
    "Coffee",
]


@dataclass
class ProductForecastSummary:
    product_name: str
    total_expected_sales_next_month: float
    status: str


def load_sales_data(filepath: str) -> pd.DataFrame:
    """Load dataset and convert date column to datetime."""
    df = pd.read_csv(filepath)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date"])
    return df


def prepare_prophet_dataframe(df: pd.DataFrame, product_name: str) -> pd.DataFrame:
    """
    Filter one product, aggregate daily quantity, and format as Prophet input:
    ds=date, y=quantity.
    """
    product_df = df[df["product_name"] == product_name].copy()

    if product_df.empty:
        return pd.DataFrame(columns=["ds", "y"])

    daily_sales = (
        product_df.groupby("date", as_index=False)["quantity"]
        .sum()
        .rename(columns={"date": "ds", "quantity": "y"})
        .sort_values("ds")
    )

    full_dates = pd.date_range(daily_sales["ds"].min(), daily_sales["ds"].max(), freq="D")
    daily_sales = (
        daily_sales.set_index("ds")
        .reindex(full_dates)
        .fillna(0.0)
        .rename_axis("ds")
        .reset_index()
    )

    return daily_sales


def train_and_forecast_product(prophet_df: pd.DataFrame, days: int) -> pd.DataFrame:
    """Train Prophet for one product and forecast the next N days."""
    from prophet import Prophet

    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=True,
    )
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=days, freq="D")
    forecast = model.predict(future)

    return model, forecast


def plot_product_forecasts(model, forecast: pd.DataFrame, product_name: str) -> None:
    """Plot forecast and components (trend/seasonality) for one product."""
    fig1 = model.plot(forecast)
    plt.title(f"{product_name} - Sales Forecast")
    plt.xlabel("Date")
    plt.ylabel("Predicted Quantity")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

    fig2 = model.plot_components(forecast)
    fig2.suptitle(f"{product_name} - Trend and Seasonality", y=1.02)
    plt.tight_layout()
    plt.show()


def run_product_wise_forecasting(
    df: pd.DataFrame,
    products: List[str],
    forecast_days: int,
) -> tuple[pd.DataFrame, List[ProductForecastSummary]]:
    """
    Train Prophet model for each product and collect next-N-day forecasts.
    Returns:
      - combined forecast rows for CSV
      - per-product next-month totals
    """
    all_forecasts: List[pd.DataFrame] = []
    summaries: List[ProductForecastSummary] = []

    for product in products:
        print(f"\nProcessing product: {product}")
        prophet_df = prepare_prophet_dataframe(df, product)

        if prophet_df.empty:
            print(f"  No historical data found for '{product}'. Skipping model training.")
            summaries.append(
                ProductForecastSummary(
                    product_name=product,
                    total_expected_sales_next_month=0.0,
                    status="No historical data",
                )
            )
            continue

        model, forecast = train_and_forecast_product(prophet_df, forecast_days)

        next_30 = forecast.tail(forecast_days).copy()
        next_30["product_name"] = product
        next_30 = next_30[
            ["product_name", "ds", "yhat", "yhat_lower", "yhat_upper"]
        ].reset_index(drop=True)

        total_expected = float(next_30["yhat"].sum())
        summaries.append(
            ProductForecastSummary(
                product_name=product,
                total_expected_sales_next_month=total_expected,
                status="Forecast generated",
            )
        )

        print("  Predicted sales for next 30 days:")
        print(next_30[["ds", "yhat"]].to_string(index=False))
        print(f"  Total expected sales next month: {total_expected:.2f}")

        plot_product_forecasts(model, forecast, product)
        all_forecasts.append(next_30)

    if all_forecasts:
        combined = pd.concat(all_forecasts, ignore_index=True)
    else:
        combined = pd.DataFrame(columns=["product_name", "ds", "yhat", "yhat_lower", "yhat_upper"])

    return combined, summaries


def print_summary_table(summaries: List[ProductForecastSummary]) -> None:
    """Print total expected sales next month for each target product."""
    summary_df = pd.DataFrame(
        [
            {
                "product_name": s.product_name,
                "total_expected_sales_next_month": s.total_expected_sales_next_month,
                "status": s.status,
            }
            for s in summaries
        ]
    )
    print("\nTotal expected sales next month (product-wise):")
    print(summary_df.to_string(index=False, float_format=lambda x: f"{x:.2f}"))


def main() -> None:
    """Execute product-wise Prophet forecasting workflow."""
    print("Starting product-wise Prophet forecasting...")
    print("Install command (if needed): pip install prophet")

    df = load_sales_data(DATA_PATH)
    forecast_df, summaries = run_product_wise_forecasting(
        df=df,
        products=TARGET_PRODUCTS,
        forecast_days=FORECAST_DAYS,
    )

    forecast_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved forecast results to: {OUTPUT_CSV}")

    print_summary_table(summaries)


if __name__ == "__main__":
    main()
