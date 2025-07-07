import pathlib
from datetime import datetime
from urllib.parse import urljoin
import re
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

KEYWORD = "Contact Center"
PDF_SAVE_PREFIX = "pdfs/tsa-contact-center-traveler-complaints-report"
BASE_URL = "https://www.tsa.gov/foia/readingroom"

TITLE_FIXES = {
    "https://www.tsa.gov/sites/default/files/foia-readingroom/tsa_contact_center_traveler_complaints_report_septermber.pdf": "September 2019"
}


def extract_date_from_pdf(file_path):
    """Extracts MM/YYYY from the first page of the PDF."""
    try:
        reader = PdfReader(file_path)
        first_page = reader.pages[0]
        text = first_page.extract_text()
        match = re.search(r"(0[1-9]|1[0-2])/([0-9]{4})", text)
        if match:
            month = int(match.group(1))
            year = match.group(2)
            return year, month
    except Exception as e:
        print(f"Warning: Failed to extract date from {file_path}: {e}")
    # fallback to current year and month
    now = datetime.now()
    return str(now.year), now.month


def process_link(link):
    href = link["href"]

    if KEYWORD not in link.text or not href.endswith(".pdf"):
        return

    pdf_url = urljoin(BASE_URL, href)
    title = TITLE_FIXES.get(pdf_url, link.text)
    elements = title.split()

    try:
        year = elements[-1]
        month = datetime.strptime(elements[-2], "%B").month
    except (IndexError, ValueError):
        # fallback: download first, then parse date inside PDF
        print(f"Title parsing failed for '{title}'. Downloading to parse date from PDF.")
        temp_dest = pathlib.Path(f"{PDF_SAVE_PREFIX}-temp.pdf")
        pdf_response = requests.get(pdf_url)
        with open(temp_dest, "wb") as pdf_file:
            pdf_file.write(pdf_response.content)

        year, month = extract_date_from_pdf(temp_dest)
        dest = pathlib.Path(f"{PDF_SAVE_PREFIX}-{year}-{month:02d}.pdf")

        if dest.exists():
            temp_dest.unlink()  # remove temp file
            return

        temp_dest.rename(dest)
        print(f"Saved PDF as {dest}")
        return

    dest = pathlib.Path(f"{PDF_SAVE_PREFIX}-{year}-{month:02d}.pdf")

    if dest.exists():
        return

    print(f"Downloading {pdf_url}")
    pdf_response = requests.get(pdf_url)

    with open(dest, "wb") as pdf_file:
        pdf_file.write(pdf_response.content)

    print(f"Saved PDF as {dest}")


def check_and_download(page):
    response = requests.get(BASE_URL, params=dict(page=page))
    soup = BeautifulSoup(response.content, "html.parser")
    for link in soup.find_all("a", href=True):
        process_link(link)


def main():
    for i in range(25):
        print(f"Checking page {i}")
        check_and_download(i)


if __name__ == "__main__":
    main()