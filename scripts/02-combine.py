"""
Steps through the directory of parsed CSV files (each containing one or more
months of TSA complaints data) and combines/deduplicates them into a single
dataset, saved to "output/02-combined/complaints-all-by-month.csv".

Also splits that single file into three separate CSV files, at varying levels
of granularity:

1) complaints-by-subcategory-raw.csv - complaint counts by subcategory by month

2) complaints-by-category-raw.csv
  - complaint counts by category by month

3) complaints-by-airport-raw.csv  - complaint counts by airport by month
"""

import pathlib

import pandas as pd

OUTPUT_DIR = "output/02-combined"


def combine_and_dedupe_csvs(report_paths):
    """
    Combine and deduplicate the individual report CSVs into a single CSV file.

    Arguments:
    - report_paths: list of all csv files in the output directory
    """
    deduped = pd.DataFrame()
    disagreements = []
    earliest_date = "9999"
    for path in reversed(sorted(report_paths)):
        print(path.name)
        df = pd.read_csv(path)
        print(f"Date range: {df['year_month'].max()}-{df['year_month'].min()}")
        entries_unseen = df.loc[lambda df: df["year_month"] < earliest_date]
        entries_seen = df.loc[lambda df: df["year_month"] >= earliest_date]

        if len(deduped):  # if we've already processed one PDF, check disagreements
            new_disagreements = check_disagreements(deduped, entries_seen)
            disagreements.append(new_disagreements)

        deduped = pd.concat([deduped, entries_unseen])
        earliest_date = deduped["year_month"].min()
        print("---")

    return deduped, pd.concat(disagreements)


def write_levels(deduped):
    df = deduped.sort_values(
        [
            "airport",
            "year_month",
            "category",
            "subcategory",
            "pdf_report_date",
        ]
    )
    print(f"# records total deduped: {len(df):,}")

    # split dataframe into three dataframes, and save each
    # filter to include all rows with a subcategory
    df_subcat = df[df["subcategory"].notna()]
    df_subcat.to_csv(f"{OUTPUT_DIR}/complaints-by-subcategory-raw.csv", index=False)
    print(f"# records in complaints-by-subcategory-raw.csv: {len(df_subcat):,}")

    # filter to include category totals, i.e. subcategory is blank
    df_cat = df[df["category"].notna() & df["subcategory"].isna()]
    df_cat.to_csv(f"{OUTPUT_DIR}/complaints-by-category-raw.csv", index=False)
    print(f"# records in complaints-by-category-raw.csv: {len(df_cat):,}")

    # filter to include overall totals, i.e. category and subcategory are blank
    df_airport = df[df["category"].isna() & df["subcategory"].isna()]
    df_airport.to_csv(f"{OUTPUT_DIR}/complaints-by-airport-raw.csv", index=False)
    print(f"# records in complaints-by-airport-raw.csv: {len(df_airport):,}")

    # confirm no records are lost or duplicated
    print(
        "# total records in split files: "
        f"{len(df_subcat) + len(df_cat) + len(df_airport):,}"
    )


def check_disagreements(deduped, current_report):
    """
    Because TSA complaints reports overlap with prior reports by repeating
    monthly counts from recent prior months, this function checks whether the
    prior-month data in the current report matches data from the previously
    appended report.

    Arguments:
    - deduped: DataFrame containing the deduped data so far.
    - current_report: DataFrame with counts from the current report's overlapping dates.
    """
    # Define the key columns excluding "pdf_report_date"
    key_columns = ["airport", "category", "year_month"]

    # Select only category-level, drop subcategories (due to ambiguities)
    def prep_df(df):
        return (
            df.loc[lambda df: df["subcategory"].isnull()]
            .drop(columns=["subcategory"])
            .rename(columns={"pdf_report_date": "report"})
        )

    # Merge the two grouped dataframes on the key columns
    merged_data = pd.merge(
        prep_df(deduped),
        prep_df(current_report),
        on=key_columns,
        suffixes=("_deduped", "_current"),
    )

    # Check for discrepancies where the counts differ
    disagreements = merged_data[
        merged_data["count_deduped"] != merged_data["count_current"]
    ]

    print(f"Disagreements found: {len(disagreements)}")

    return disagreements


def main():
    report_paths = pathlib.Path("output/01-parsed/").glob("report-20*-month.csv")
    deduped, disagreements = combine_and_dedupe_csvs(report_paths)
    deduped.to_csv(f"{OUTPUT_DIR}/complaints-all-by-month.csv", index=False)
    disagreements.to_csv("output/misc/report-disagreements.csv", index=False)
    write_levels(deduped)


if __name__ == "__main__":
    main()
