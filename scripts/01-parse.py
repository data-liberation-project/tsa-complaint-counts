"""
This script extracts data from each PDF in the pdfs/ directory and saves the
raw extracted data as a CSV in the output/01-parsed directory.

If an argument is provided with a specific pathname when executing this script
(see parse_args), this will parse a single PDF as specified. If no argument
provided, it will parse each PDF in the pdfs/ directory in sorted order.
"""

import argparse
import csv
import pathlib
import re

import pdfplumber

PARSED_DIR = "output/01-parsed"

MONTH_ORDER = [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def get_line_type(chars):
    """
    Assigns line type to each line according to distance of leftmost character
    from left side of page.
    """
    c = chars[0]
    x0 = c["x0"]
    mult = 1 if c["ncs"] == "DeviceRGB" else 0.8
    if x0 < 18:
        return "table-header"
    if x0 < 27:
        return "airport"
    elif x0 < 34:
        return "year"
    elif x0 < (mult * 50):
        return "category"
    elif x0 < (mult * 65):
        return "subcategory"
    else:
        return "rest"


def month_parse(chars):
    """
    Given the characters representing complaint data by month, returns a list
    that includes 0s for months in which there were no complaints fitting the
    category or subcategory. Achieves this by using the x0 attribute of the
    characters.
    """
    months = [0] * 12  # set each  month to 0

    for char in chars:
        if char["text"] == ",":
            continue
        # could at some point get rid of conditionals, would make more efficient
        val = int(char["text"])  # integer value of character
        x0 = char["x0"]

        if x0 < 220:
            if x0 > 185:  # don't want to randomly catch wrong data
                months[0] = 10 * months[0] + val
        elif x0 < 252:
            months[1] = 10 * months[1] + val
        elif x0 < 285:
            months[2] = 10 * months[2] + val
        elif x0 < 315:
            months[3] = 10 * months[3] + val
        elif x0 < 350:
            months[4] = 10 * months[4] + val
        elif x0 < 380:
            months[5] = 10 * months[5] + val
        elif x0 < 410:
            months[6] = 10 * months[6] + val
        elif x0 < 440:
            months[7] = 10 * months[7] + val
        elif x0 < 470:
            months[8] = 10 * months[8] + val
        elif x0 < 500:
            months[9] = 10 * months[9] + val
        elif x0 < 540:
            months[10] = 10 * months[10] + val
        elif x0 < 570:
            months[11] = 10 * months[11] + val

    return months


def parse_line_chars(chars, line_type_getter):
    """
    For a given line, returns the line's "header" (description?), the line's text,
    (not currently used) the line's month_data, the total data for that year/category,
    and the line's type.
    """
    line_type = line_type_getter(chars)

    # Here, we identify the character at which the PDF switches
    # from the "header" to the complaint counts
    if line_type == "year":
        i = 4
    elif chars[0]["mcid"] is not None:
        for i, char in enumerate(chars):
            if i == 0:
                continue
            elif char["mcid"] != chars[i - 1]["mcid"]:
                break
    else:
        for i, char in enumerate(chars):
            if char["text"].isnumeric():
                break

    number_text = pdfplumber.utils.extract_text(chars[i:])

    elements = number_text.strip().replace(",", "").split(" ")

    total_data = int(elements[-1])

    month_data = month_parse(chars[i:])  # call month_parse

    if sum(month_data) < 999:
        if sum(month_data) == int(total_data) + 75:
            month_data[0] = 0
        elif sum(month_data) == int(total_data) + 12:
            month_data[1] = 0

    header = pdfplumber.utils.extract_text(chars[:i])

    return {  # returns all of this information as a dictionary
        "header": header,
        "line": number_text,
        "month_data": month_data,
        "total_data": total_data,
        "line_type": line_type,
    }


def parse_pdf(pdf, pdf_year, pdf_month, max_pages=None):
    """
    Loops through an entire PDF, parsing each line to extract monthly and
    annual totals.  It keeps track of the current report date, airport code,
    and category while stepping through subcategories and skips header lines.

    Arguments:
    - pdf: pathname to the pdf to be parsed
    - pdf_year: year of the pdf to be parsed
    - pdf_month: month of the pdf to be parsed

    Returns:
    rows_totals: a list of dictionaries with each category and subcategory total
    rows_months: a list of dictionaries with monthly data
    """
    rows_months = []
    rows_totals = []
    airport_code = None
    year = None
    category = None
    min_date = "9999-12"
    max_date = "0000-01"

    for page in pdf.pages[:max_pages]:
        chars_by_line = pdfplumber.utils.cluster_objects(page.chars, "top", tolerance=2)

        # Note: Intentionally skips first two lines and last line
        for j, line in enumerate(chars_by_line[2:-1]):
            parsed = parse_line_chars(line, get_line_type)

            if parsed["line_type"] == "table-header":
                continue  # catches one bug
            elif parsed["line_type"] == "airport":
                airport_code = parsed["header"][:3]
                if airport_code == "z N":
                    airport_code = "N/A"
                continue
            elif parsed["line_type"] == "year":
                year = parsed["header"]
            elif parsed["line_type"] == "category":
                category = parsed["header"]

            if sum(parsed["month_data"]) != parsed["total_data"]:
                print([(c["text"], c["mcid"]) for c in line])
                print(parsed["header"])
                print(parsed["month_data"])
                print(parsed["total_data"])
                raise Exception(f"Error parsing page {page.page_number}")

            common_values = {
                "pdf_report_date": f"{pdf_year}-{pdf_month}",
                "airport": airport_code,
                "category": category
                if parsed["line_type"] not in ["airport", "year"]
                else None,
                "subcategory": parsed["header"]
                if parsed["line_type"] == "subcategory"
                else None,
            }

            row_total = common_values.copy()
            row_total["year"] = year if parsed["line_type"] != "airport" else None
            row_total["count"] = parsed["total_data"]
            rows_totals.append(row_total)

            for column_num, month_num in enumerate(MONTH_ORDER):
                row_month = common_values.copy()

                if month_num > 9:
                    row_month[
                        "year_month"
                    ] = f"{int(row_total['year'])-1}-{month_num:02d}"
                else:
                    row_month["year_month"] = f"{row_total['year']}-{month_num:02d}"

                row_month["count"] = parsed["month_data"][column_num]

                rows_months.append(row_month)
                if row_month["count"] > 0:
                    if row_month["year_month"] < min_date:
                        min_date = row_month["year_month"]
                    if row_month["year_month"] > max_date:
                        max_date = row_month["year_month"]

    rows_months = [
        row for row in rows_months if min_date <= row["year_month"] <= max_date
    ]

    return rows_totals, rows_months


def write_parsed_rows(rows, dest):
    """
    Write parsed PDF data to a CSV.

    Arguments:
    - rows: rows of data to be written
    - dest: path to the destination csv file (either the monthly or annual totals)
    """
    with open(dest, "w") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[-1].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_single_pdf(path, reparse=False, max_pages=None):
    """
    Parses one PDF and saves the extracted data.

    Arguments:
    - path: path to the pdf to be parsed
    - reparse: if true, PDF will be parsed again even if the output file already exists
    - max-pages: limit to number of pages to parse
    """
    year, month = re.search(r"(\d+)-(\d+)\.pdf$", path.name).groups()
    totals_dest = pathlib.Path(f"{PARSED_DIR}/report-{year}-{month}-fiscal-year.csv")
    months_dest = pathlib.Path(f"{PARSED_DIR}/report-{year}-{month}-month.csv")

    needs_parsing = not totals_dest.exists() or not months_dest.exists()
    if not needs_parsing and not reparse:
        print(f"Skipping {path} because it's already been parsed.")
        return

    print(f"Parsing {path}")
    pdf = pdfplumber.open(path)
    rows_totals, rows_months = parse_pdf(pdf, year, month, max_pages)
    write_parsed_rows(rows_totals, totals_dest)
    write_parsed_rows(rows_months, months_dest)


def parse_args():
    """
    Extracts the arguments that have been passed on the command line to this
    script.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pdf",
        type=pathlib.Path,
        help="If not provided, will attempt to parse all PDFs in pdfs/ dir.",
    )
    parser.add_argument(
        "--max-pages", type=int, help="Only parse first X pages, just for debugging."
    )
    parser.add_argument(
        "--reparse",
        action="store_true",
        help="If parsing full directory, don't skip over already-parsed PDFs",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    common_kwargs = dict(reparse=args.reparse, max_pages=args.max_pages)
    if args.pdf:
        parse_single_pdf(args.pdf, **common_kwargs)
    else:
        paths = sorted(pathlib.Path("pdfs/").glob("*.pdf"), reverse=True)
        for path in paths:
            parse_single_pdf(path, **common_kwargs)


if __name__ == "__main__":
    main()
