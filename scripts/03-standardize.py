"""
Replaces all truncated (sub)categories with standardized (sub)categories.
"""

import pandas as pd

COMBINED_DIR = "output/02-combined"
STANDARDIZED_DIR = "output/03-standardized"


def clean_complaints(raw_data_path, lookup_path=None):
    raw = pd.read_csv(raw_data_path)
    print(f"{len(raw)} records in original dataset")

    if lookup_path:
        lookup = pd.read_csv(lookup_path)

        join_cols = [col for col in raw.columns if col in lookup.columns]
        status_cols = [col for col in lookup.columns if "status" in col]

        cleaned = raw.merge(lookup, on=join_cols, how="left").sort_values(
            [
                "airport",
                "year_month",
            ]
            + join_cols
        )

        for col in status_cols:
            unmatched = cleaned.loc[lambda df: df[col].fillna("") == ""]
            if len(unmatched):
                unmatched_values = (
                    unmatched[join_cols].drop_duplicates().to_dict("records")
                )
                msg = f"Cannot find {col} value for {unmatched_values}"
                raise ValueError(msg)

        print(f"{len(cleaned)} records in cleaned dataset (should match)\n")

        # Report metrics
        for col in lookup.columns:
            if "status" in col or "prefix_removed" in col:
                print(f"{cleaned[col].value_counts()}\n\n")

    else:
        # If no lookup, just drop unused categories
        cleaned = raw.drop(columns=["category", "subcategory"])
        print("No cleaning performed\n")

    return cleaned


def main():
    print("-- Airports --")
    clean_airport = clean_complaints(
        f"{COMBINED_DIR}/complaints-by-airport-raw.csv", None
    )
    clean_airport.to_csv(f"{STANDARDIZED_DIR}/complaints-by-airport.csv", index=False)

    print("-- Categories --")
    clean_cat = clean_complaints(
        f"{COMBINED_DIR}/complaints-by-category-raw.csv",
        "lookups/lkp_cleaner_categories.csv",
    )
    clean_cat.drop(columns=["subcategory"], inplace=True)
    clean_cat.to_csv(f"{STANDARDIZED_DIR}/complaints-by-category.csv", index=False)

    print("-- Subcategories --")
    clean_subcat = clean_complaints(
        f"{COMBINED_DIR}/complaints-by-subcategory-raw.csv",
        "lookups/lkp_cleaner_subcategories.csv",
    )
    clean_subcat.to_csv(
        f"{STANDARDIZED_DIR}/complaints-by-subcategory.csv", index=False
    )


if __name__ == "__main__":
    main()
