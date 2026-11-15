from spreadsheet_engine import (
    answer_query,
    compute_summary,
    generate_profit_loss_dataset,
    get_product_statistics,
    parse_creation_prompt,
)


def test_parse_creation_prompt():
    prods, yrs, gsheets = parse_creation_prompt(
        "Create a Google Sheet for 100 products over 5 years profit and loss"
    )
    assert prods == 100
    assert yrs == 5
    assert gsheets is True


def test_dataset_shape_and_profit_loss_math():
    df = generate_profit_loss_dataset(num_products=100, num_years=5, start_year=2022)
    assert len(df) == 100 * 5 * 12  # 6,000 rows
    assert df["product_id"].nunique() == 100
    assert df["year"].nunique() == 5
    sample = df.iloc[0]
    assert round(sample["revenue"] - sample["cost"], 2) == round(sample["profit_loss"], 2)


def test_assistant_queries():
    df = generate_profit_loss_dataset(num_products=100, num_years=5, start_year=2022)

    loss_res = answer_query(df, "What is the total loss?")
    assert loss_res["intent"] == "total_loss"
    assert loss_res["metrics"]["total_loss"] < 0
    assert len(loss_res["chart_labels"]) == 5

    avg_res = answer_query(df, "What is the total average?")
    assert avg_res["intent"] == "total_average"
    assert "avg_monthly_per_product" in avg_res["metrics"]

    comp_res = answer_query(df, "Compare Product 1 and Product 5 over 5 years", preferred_chart_type="line")
    assert comp_res["intent"] == "product_comparison"
    assert comp_res["chart_type"] == "line"
    assert len(comp_res["chart_datasets"]) == 2

    stat_res = answer_query(df, "Show statistics for Product 3")
    assert stat_res["intent"] == "product_statistics"
    assert stat_res["table_rows"][0]["product_id"] == "PRD-003"


def test_summary_and_product_stats():
    df = generate_profit_loss_dataset(num_products=10, num_years=2, start_year=2024)
    summary = compute_summary(df, "test123", "Test Sheet")
    assert summary["total_rows"] == 240
    stats = get_product_statistics(df)
    assert len(stats) == 10
