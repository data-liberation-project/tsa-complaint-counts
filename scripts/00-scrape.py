"""
This script scrapes the TSA's FOIA reading room, saving any newly-discovered
PDF files containing the keyword "Contact Center" to the pdfs/ directory.
"""

import pathlib
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

KEYWORD = "Contact Center"
PDF_SAVE_PREFIX = "pdfs/tsa-contact-center-traveler-complaints-report"
BASE_URL = "https://www.tsa.gov/foia/readingroom"

TITLE_FIXES = {
    "https://www.tsa.gov/sites/default/files/foia-readingroom/tsa_contact_center_traveler_complaints_report_septermber.pdf": "September 2019"  # noqa: E501
}


def process_link(link):
    """
    For each hyperlink in the TSA Reading Room that's a PDF file containing the
    keyword "Contact Center" assign it a standardized filename (e.g.
    tsa-contact-center-traveler-complaints-report-2019-02.pdf) and write it to
    the pdfs/ directory if it's not already there.

    Arguments:
    - link: the URL of the file to check
    """
    href = link["href"]

    if KEYWORD not in link.text or not href.endswith(".pdf"):
        return

    pdf_url = urljoin(BASE_URL, href)

    title = TITLE_FIXES.get(pdf_url, link.text)
    elements = title.split()
    year = elements[-1]
    # Converts, e.g., March->3
    month = datetime.strptime(elements[-2], "%B").month
    dest = pathlib.Path(f"{PDF_SAVE_PREFIX}-{year}-{month:02d}.pdf")

    if dest.exists():
        return

    print(f"Downloading {pdf_url}")
    pdf_response = requests.get(pdf_url)

    with open(dest, "wb") as pdf_file:
        pdf_file.write(pdf_response.content)


def check_and_download(page):
    """
    for a single page in the TSA Reading Room, step through each hyperlink
    calling "process_link" for each

    arguments:
    page -- page # in the reading room
    """
    response = requests.get(BASE_URL, params=dict(page=page))
    soup = BeautifulSoup(response.content, "html.parser")
    for link in soup.find_all("a", href=True):
        process_link(link)


def main():
    """
    step through up to 25 pages of posts in the TSA FOIA Reading Room
    calling check_and_download for each page
    """
    for i in range(25):
        print(f"Checking page {i}")
        check_and_download(i)


if __name__ == "__main__":
    main()
