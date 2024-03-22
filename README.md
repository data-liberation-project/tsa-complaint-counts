# TSA Complaint Counts

In its [FOIA Electronic Reading Room](https://www.tsa.gov/foia/readingroom?page=0), the US Transportation Security Administration (TSA) publishes semi-regular reports on the monthly numbers of traveler complaints by airport, category, and subcategory.

Unfortunately, they post these data only as PDFs ([example here](https://www.tsa.gov/sites/default/files/foia-readingroom/tsa-contact-center-traveler-complaints-report-may-2023.xlsm_.pdf)), rather than as [machine-readable data files](https://en.wikipedia.org/wiki/Machine-readable_medium_and_data#Data), and at unpredictable intervals. Because of the idiosyncratic fashion in which the records are provided, some additional effort is needed to get the data in a format that can be easily analyzed.

This repository, created by the [Data Liberation Project](https://www.data-liberation-project.org/) and [volunteers](#credits):

- Fetches new PDFs as they become available
- Parses the raw data from these PDFs
- Converts that data into CSV files
- Standardizes the results

## Data guidance

The Data Liberation Project recommends using the files in [output/03-standardized/](output/03-standardized/), which contain monthly complaint counts for January 2015 – January 2024 and are divided into three levels of granularity: 

- [output/03-standardized/complaints-by-airport.csv](output/03-standardized/complaints-by-airport.csv): Overall complaint count by airport and month.
- [output/03-standardized/complaints-by-category.csv](output/03-standardized/complaints-by-category.csv): Complaint count by airport, month, and complaint category.
- [output/03-standardized/complaints-by-subcategory.csv](output/03-standardized/complaints-by-subcategory.csv): Complaint count by airport, month, complaint category, and complaint subcategory.

These CSV files use the following fields, where applicable:

| Column | Example Value | Description |
|--------|---------------|-------------|
| pdf_report_date | `2019-12` | The month (YYYY-MM) of the PDF from which this row is sourced. |
| airport | `ABE` | The airport's three-letter code. __Note__: Null/blank values appear to represent complaints not associated with any airport in particular. They are *not* grand totals. |
| category | `Mishandling of Passenger Property` | The complaint category. |
| subcategory | `Mishandling of Passenger Property - Damaged/Missing Items--Checked Bag` | The complaint subcategory. |
| year_month | `2016-01` | The complaint month. |
| count | `1` | The number of complaints matching that airport, category, and subcategory for that month. |
| clean_cat | `Mishandling of Passenger Property` | The standardized/cleaned category label; see below for details. |
| clean_subcat | `Damaged/Missing Items--Checked Baggage` | The standardized/cleaned subcategory label; see below for details. |
| clean_cat_status | `original` | See below for details. |
| clean_subcat_status | `imputed` | See below for details. |
| is_category_prefix_removed | `True` | Whether the standardization process trimmed off the (redundant) category label from the subcategory label. |

### Caveat: Comparisons over time

In March 2024, a TSA spokesperson [provided comments to FedScoop reporter Rebecca Heilweil](https://fedscoop.com/tsa-precheck-complaints-data/) indicating that (at least) some of the increase in complaints over time can be attributed to the agency making it easier to submit PreCheck complaints:

> The spokesperson said that changes to several platforms and customer service tools are responsible for the rise in complaints. In May 2021, the agency created a new TSA PreCheck webform that saw complaints increase around 79% in the following four months. That August, the agency deployed messaging enhancements that, in combination with the new online form, saw complaints grow by 62% in the subsequent four months. (Switching to Salesforce for the TSA Contact Center at the end of 2020 also meant that the airport field in the data started to populate). 


### Caveat: Ambiguous subcategories

Due to how the TSA formats its PDFs, subcategories are sometimes rendered ambiguously.

For instance, the PDFs sometimes list a `Mishandling of Passenger Property` subcategory that has been truncated to `Damaged/Missing Items--C`. This name is ambiguous because it could represent either of the following (both of which appear elsewhere, in non-truncated entries):

- `Damaged/Missing Items--Carry-on Luggage`
- `Damaged/Missing Items--Checked Baggage`

Similar types of ambiguous subcategories appear under the following three categories:

- `Mishandling of Passenger Property`- all subcategories beginning with “Damaged/Missing Items”
- `Property - Special Handling`- all subcategories
- `Expedited Passenger Screening Program`- all subcategories

For this reason, subcategory totals in these categories may not be definitive.

Subcategories impacted by ambiguous values are marked with an asterisk. For example, both the ambiguous subcategory `*Damaged Items`, and related categories `*Damaged Items - Carry-On` and `*Damaged Items - Checked` are marked with asterisks to warn of potentially inaccurate totals.

### Caveat: Null Values

**By airport:** Preliminary analysis of [output/03-standardized/complaints-by-airport.csv](output/03-standardized/complaints-by-airport.csv) shows that nearly half of all complaints overall have a null value for `airport`. Though the reason for these null values is currently unknown, this seems to suggest that complaints may not be associated with any particular airport. Also noteworthy, this proportion declines to about a quarter of all complaints by 2022.

**By subcategory:** Records having a subcategory of `Expedited Passenger Screening Program` are cleaned to render simply `*`. This is because the subcategory is simply a repetition of the category with no further detail provided.

## Data cleaning

In the CSV files in `output/03-standardized`, the fields `clean_cat_status` and `clean_subcat_status` track how data is cleaned/standardized, based on assumptions about how the data was likely truncated in the TSA's PDF complaint report outputs. There are four possible values:

|Status|Description|Change Made|
|---|---|---|
| `original` | Not truncated | Original category retained |
| `imputed` | Only one possible truncation | Category imputed to likely value |
| `ambiguous` | Two or more truncatations possible | Original category retained |
| `missing` | No corresponding value in the Data Liberation Project's [lookup tables](lookups/) | Category left blank |

### Imputation criteria

For imputed categories and subcategories, we have reasonable certainty of what was truncated. For example:

> Additional Information Required/Insufficient Inf

... is likely truncated from (and thus transformed to):

> Additional Information Required/Insufficient Information

### Trimmed attributes

Many TSA complaint subcategories repeat the category within the subcategory. The standardization process trims out these repeated categories. For example, the following record:

|Category|Subcategory|
|---|---|
|Advanced Imaging Technology (AIT)|Advanced Imaging Technology (AIT) - Non-Flyer|

...is transformed to:

|Category|Subcategory|
|---|---|
|Advanced Imaging Technology (AIT)|Non-Flyer|

These trimmed subcategories are flagged as `True` in the column `is_category_prefix_removed`.

### Data Cleaning Lookup Tables
The values of `clean_cat` and `clean_cat_status` are determined for each record in `output/03-standardized/complaints-by-category.csv` using the lookup table [`lookups/lkp_cleaner_categories.csv`](lookups/lkp_cleaner_categories.csv) based on matching values of `Category`.

Similarly, the values of `clean_cat`, `clean_cat_status`, `clean_subcat`, and `clean_subcat_status` are determined for each record in `output/03-standardized/complaints-by-subcategory.csv` using the lookup table [`lookups/lkp_cleaner_subcategories.csv`](lookups/lkp_cleaner_subcategories.csv) based on matching values of `Category` and `Subcategory`.



## Scripts

The repository's pipeline consists of the following scripts:

- [scripts/00-scrape.py](scripts/00-scrape.py): Scrapes the TSA FOIA electronic reading room for all relevant PDFs and downloads them to the [pdfs/](pdfs/) directory.
- [scripts/01-parse.py](scripts/01-parse.py): Parses each of the PDFs, extracting the structured data and saving it to the [output/01-parsed/](output/01-parsed/) directory. For each PDF, the output includes two CSV files: one containing one row per fiscal year total (as stated literally in the PDF), and one containing one row per monthly total.
- [scripts/02-combine.py](scripts/02-combine.py): Combines the monthly-total CSVs into a single, deduplicated CSV (since each report covers multiple years, and the coverage periods overlap across reports), saved to [output/02-combined/](output/02-combined/). Also saves three additional subsets, each focused on a single level of granularity (airport, airport-category, and airport-category-subcategory).
    - In instances where the same month's data is available in multiple PDF reports, we use the counts from the most recent report. A given entry's count rarely changes over time; when it does, it's typically by small amounts.
- [scripts/03-standardize.py](scripts/03-standardize.py): Standardizes the category and subcategory labels, since the reports' PDF layouts often trim the full description, and saves the results to [output/03-standardized/](output/03-standardized/). The script also trims redundant category prefixes from subcategory descriptions. See the [Data guidance](#data-guidance) section above for interpreting the results.

## Repository structure

```
.
├── .github
│   └── workflows
│       └── run.yml
├── .gitignore
├── Makefile
├── README.md
├── lookups
│   ├── lkp_cleaner_categories.csv
│   └── lkp_cleaner_subcategories.csv
├── output
│   ├── 01-parsed
│   │   ├── report-2019-02-fiscal-year.csv
│   │   ├── report-2019-02-month.csv
│   │   ├── …
│   │   ├── report-2023-10-fiscal-year.csv
│   │   └── report-2023-10-month.csv
│   ├── 02-combined
│   │   ├── complaints-by-airport-raw.csv
│   │   ├── complaints-all-by-month.csv
│   │   ├── complaints-by-category-raw.csv
│   │   └── complaints-by-subcategory-raw.csv
│   ├── 03-standardized
│   │   ├── complaints-by-airport.csv
│   │   ├── complaints-by-category.csv
│   │   └── complaints-by-subcategory.csv
│   └── misc
│       └── report-disagreements.csv
├── pdfs
│   ├── tsa-contact-center-traveler-complaints-report-2019-02.pdf
│   ├── …
│   └── tsa-contact-center-traveler-complaints-report-2023-10.pdf
├── requirements.in
├── requirements.txt
└── scripts
    ├── 00-scrape.py
    ├── 01-parse.py
    ├── 02-combine.py
    └── 03-standardize.py
```

## Credits

This data pipeline has been developed by Jake Zucker, Rob Reid, Emily Keller-O'Donnell, Asako Mikami, and Jeremy Singer-Vine, collaborating through the [Data Liberation Project](https://www.data-liberation-project.org/).

## Licensing

This repository's code is available under the [MIT License terms](https://opensource.org/license/mit/). The PDFs in the `pdfs/` directory are public domain. All other data files are available under Creative Commons' [CC BY-SA 4.0 license terms](https://creativecommons.org/licenses/by-sa/4.0/).
