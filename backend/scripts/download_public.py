"""Download public NFHS-5 district fact sheets (PDF) into data/raw/nfhs/.

Source: DHS Program (dhsprogram.com), publication OF43. robots.txt does not block
/pubs/pdf. We wait between requests and skip files we already have.

The district list comes from two open GitHub files (see MANIFEST.csv). Chandigarh is
skipped on purpose. Telangana names come from a CC BY 4.0 file; its sheets are fetched
from the same DHS folder as the others.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "nfhs"
PDF_DIR = RAW / "district_pdfs"
MANIFEST = ROOT / "data" / "MANIFEST.csv"
DHS_BASE = "https://dhsprogram.com/pubs/pdf/OF43"
LINKS_URL = "https://raw.githubusercontent.com/rohitdwivedula/nfhs5/master/districtwise_links.csv"
TG_URL = (
    "https://raw.githubusercontent.com/pratapvardhan/NFHS-5/master/"
    "district-level/NFHS-5-TG-Telangana.csv"
)
CENSUS_URL = (
    "https://censusindia.gov.in/nada/index.php/catalog/6191/download/9268/"
    "DDW_PCA0000_2011_Indiastatedist.xlsx"
)
CENSUS_FILE = ROOT / "data" / "raw" / "census2011" / "DDW_PCA0000_2011_Indiastatedist.xlsx"
CENSUS_NADA = "https://censusindia.gov.in/nada/index.php/catalog/"
C20_DIR = ROOT / "data" / "raw" / "census2011" / "c20_disability"
# Census 2011 table C-20 (disabled population by type of disability, age and sex),
# state files with district rows. Census state id -> "<catalog id>/download/<file id>/<name>".
C20_PATHS = {
    "01": "43370/download/47074/DDW-C20-0100.xlsx",
    "02": "43371/download/47075/DDW-C20-0200.xlsx",
    "03": "43372/download/47076/DDW-C20-0300.xlsx",
    "04": "43373/download/47077/DDW-C20-0400.xlsx",
    "05": "43374/download/47078/DDW-C20-0500.xlsx",
    "06": "43375/download/47079/DDW-C20-0600.xlsx",
    "07": "43376/download/47080/DDW-C20-0700.xlsx",
    "08": "43377/download/47081/DDW-C20-0800.xlsx",
    "09": "43378/download/47082/DDW-C20-0900.xlsx",
    "10": "43379/download/47083/DDW-C20-1000.xlsx",
    "11": "43380/download/47084/DDW-C20-1100.xlsx",
    "12": "43381/download/47085/DDW-C20-1200.xlsx",
    "13": "43382/download/47086/DDW-C20-1300.xlsx",
    "14": "43383/download/47087/DDW-C20-1400.xlsx",
    "15": "43384/download/47088/DDW-C20-1500.xlsx",
    "16": "43385/download/47089/DDW-C20-1600.xlsx",
    "17": "43386/download/47090/DDW-C20-1700.xlsx",
    "18": "43387/download/47091/DDW-C20-1800.xlsx",
    "19": "43388/download/47092/DDW-C20-1900.xlsx",
    "20": "43389/download/47093/DDW-C20-2000.xlsx",
    "21": "43390/download/47094/DDW-C20-2100.xlsx",
    "22": "43391/download/47095/DDW-C20-2200.xlsx",
    "23": "43392/download/47096/DDW-C20-2300.xlsx",
    "24": "43393/download/47097/DDW-C20-2400.xlsx",
    "25": "43394/download/47098/DDW-C20-2500.xlsx",
    "26": "43395/download/47099/DDW-C20-2600.xlsx",
    "27": "43396/download/47100/DDW-C20-2700.xlsx",
    "28": "43397/download/47101/DDW-C20-2800.xlsx",
    "29": "43398/download/47102/DDW-C20-2900.xlsx",
    "30": "43399/download/47103/DDW-C20-3000.xlsx",
    "31": "43400/download/47104/DDW-C20-3100.xlsx",
    "32": "43401/download/47105/DDW-C20-3200.xlsx",
    "33": "43402/download/47106/DDW-C20-3300.xlsx",
    "34": "43403/download/47107/DDW-C20-3400.xlsx",
    "35": "43404/download/47108/DDW-C20-3500.xlsx",
}
C13_DIR = ROOT / "data" / "raw" / "census2011" / "c13_age"
# Census 2011 table C-13 (single-year age by residence and sex), old .xls, district rows.
C13_PATHS = {
    "01": "1451/download/4528/DDW-0100C-13.xls",
    "02": "1450/download/4527/DDW-0200C-13.xls",
    "03": "1464/download/4541/DDW-0300C-13.xls",
    "04": "1442/download/4519/DDW-0400C-13.xls",
    "05": "1470/download/4547/DDW-0500C-13.xls",
    "06": "1449/download/4526/DDW-0600C-13.xls",
    "07": "1446/download/4523/DDW-0700C-13.xls",
    "08": "1465/download/4542/DDW-0800C-13.xls",
    "09": "1469/download/4546/DDW-0900C-13.xls",
    "10": "1441/download/4518/DDW-1000C-13.xls",
    "11": "1466/download/4543/DDW-1100C-13.xls",
    "12": "1439/download/4516/DDW-1200C-13.xls",
    "13": "1461/download/4538/DDW-1300C-13.xls",
    "14": "1458/download/4535/DDW-1400C-13.xls",
    "15": "1460/download/4537/DDW-1500C-13.xls",
    "16": "1468/download/4545/DDW-1600C-13.xls",
    "17": "1459/download/4536/DDW-1700C-13.xls",
    "18": "1440/download/4517/DDW-1800C-13.xls",
    "19": "1471/download/4548/DDW-1900C-13.xls",
    "20": "1452/download/4529/DDW-2000C-13.xls",
    "21": "1462/download/4539/DDW-2100C-13.xls",
    "22": "1443/download/4520/DDW-2200C-13.xls",
    "23": "1456/download/4533/DDW-2300C-13.xls",
    "24": "1448/download/4525/DDW-2400C-13.xls",
    "25": "1445/download/4522/DDW-2500C-13.xls",
    "26": "1444/download/4521/DDW-2600C-13.xls",
    "27": "1457/download/4534/DDW-2700C-13.xls",
    "28": "1438/download/4515/DDW-2800C-13.xls",
    "29": "1453/download/4530/DDW-2900C-13.xls",
    "30": "1447/download/4524/DDW-3000C-13.xls",
    "31": "1455/download/4532/DDW-3100C-13.xls",
    "32": "1454/download/4531/DDW-3200C-13.xls",
    "33": "1467/download/4544/DDW-3300C-13.xls",
    "34": "1463/download/4540/DDW-3400C-13.xls",
    "35": "1437/download/4514/DDW-3500C-13.xls",
}
INCOME_URL = "https://indiabudget.gov.in/budget2024-25/economicsurvey/doc/stat/tab111a.pdf"
INCOME_DIR = ROOT / "data" / "raw" / "income"
INCOME_PDF = INCOME_DIR / "tab111a.pdf"
COMPENDIUM_DIR = ROOT / "data" / "raw" / "nfhs" / "compendium"
COMPENDIUM_FILES = (
    "NFHS-5_India_and_State_Factsheet_Compendium_Phase-I.pdf",
    "NFHS-5_India_and_State_Factsheet_Compendium_Phase-II.pdf",
)
HEADERS = {"User-Agent": "Mozilla/5.0 (research data download; polite, 1 request per 1.5 s)"}
DELAY_S = 1.5
SKIP_STATES = {"CH"}
MANIFEST_COLUMNS = [
    "file",
    "source_url",
    "downloaded_on",
    "licence",
    "downloaded_by",
    "notes",
]


def filename_candidates(state: str, district: str, hint: str | None = None) -> list[str]:
    """DHS file names to try, most likely first (spaces become underscores).

    `hint` is the file name in the district list (it fixes spellings like Bulandshahr).
    """
    names = [hint, district] if hint else [district]
    no_paren = re.sub(r"\s*\(.*?\)", "", district).strip()
    names.append(no_paren)
    names.append(re.sub(r"\((.*?)\)", r"\1", district))
    names.append(district.replace("&", "and"))
    names.append(no_paren.replace("&", "and"))
    seen: list[str] = []
    for name in names:
        file = f"{state}_{name.replace(' ', '_')}.pdf"
        if file not in seen:
            seen.append(file)
    return seen


def read_links(path: Path) -> list[tuple[str, str, str | None]]:
    """(state_code, district, file name hint) from the rohitdwivedula links CSV."""
    pairs: list[tuple[str, str, str | None]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row["link"].split("/")[1]
            if code not in SKIP_STATES:
                hint = Path(row["link"]).stem
                pairs.append((code, row["district"].strip(), hint))
    return pairs


def read_tg_names(path: Path) -> list[tuple[str, str, str | None]]:
    with path.open(newline="", encoding="utf-8") as f:
        names = sorted({row["District"].strip() for row in csv.DictReader(f)})
    return [("TG", n, None) for n in names]


def fetch(client: httpx.Client, url: str, dest: Path) -> bool:
    resp = client.get(url)
    if resp.status_code != 200 or not resp.content.startswith(b"%PDF"):
        return False
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(resp.content)
    tmp.replace(dest)
    return True


def download_district(
    client: httpx.Client, state: str, district: str, hint: str | None = None
) -> str | None:
    """Return the file name saved, or None if no candidate worked."""
    for file in filename_candidates(state, district, hint):
        dest = PDF_DIR / file
        if dest.exists():
            return file
        time.sleep(DELAY_S)
        if fetch(client, f"{DHS_BASE}/{file}", dest):
            return file
    return None


def load_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def add_manifest_rows(path: Path, rows: list[dict[str, str]]) -> None:
    existing = load_manifest(path)
    have = {r["file"] for r in existing}
    merged = existing + [r for r in rows if r["file"] not in have]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(merged)


def pdf_row(file: str, today: str) -> dict[str, str]:
    return {
        "file": f"data/raw/nfhs/district_pdfs/{file}",
        "source_url": f"{DHS_BASE}/{file}",
        "downloaded_on": today,
        "licence": "Govt of India (MoHFW/IIPS) public report; no licence text on page",
        "downloaded_by": "Claude Code",
        "notes": "NFHS-5 district fact sheet (NFHS-5 and NFHS-4 columns where available)",
    }


def list_row(name: str, url: str, licence: str, note: str, today: str) -> dict[str, str]:
    return {
        "file": f"data/raw/nfhs/{name}",
        "source_url": url,
        "downloaded_on": today,
        "licence": licence,
        "downloaded_by": "Claude Code",
        "notes": note,
    }


def shard_arg(argv: list[str]) -> tuple[int, int]:
    """`k/n` on the command line: this worker takes every n-th district, starting at k."""
    if len(argv) > 1:
        k, n = argv[1].split("/")
        return int(k), int(n)
    return 0, 1


def census_row(today: str) -> dict[str, str]:
    return {
        "file": "data/raw/census2011/DDW_PCA0000_2011_Indiastatedist.xlsx",
        "source_url": CENSUS_URL,
        "downloaded_on": today,
        "licence": "Govt of India (ORGI) public data; no licence stated on the page",
        "downloaded_by": "Claude Code",
        "notes": "Census 2011 Primary Census Abstract, state and district level (PC11_PCA-SD)."
        " No robots.txt on the site; no login needed",
    }


def download_census(client: httpx.Client) -> None:
    if CENSUS_FILE.exists():
        return
    CENSUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    resp = client.get(CENSUS_URL)
    resp.raise_for_status()
    tmp = CENSUS_FILE.with_suffix(".part")
    tmp.write_bytes(resp.content)
    tmp.replace(CENSUS_FILE)


def c20_rows(today: str) -> list[dict[str, str]]:
    return [
        {
            "file": f"data/raw/census2011/c20_disability/{path.rsplit('/', 1)[-1]}",
            "source_url": CENSUS_NADA + path,
            "downloaded_on": today,
            "licence": "Govt of India (ORGI) public data; no licence stated on the page",
            "downloaded_by": "Claude Code",
            "notes": f"Census 2011 C-20 disability by type, age, sex; state id {sid}",
        }
        for sid, path in sorted(C20_PATHS.items())
    ]


def download_c20(client: httpx.Client) -> None:
    C20_DIR.mkdir(parents=True, exist_ok=True)
    for path in C20_PATHS.values():
        dest = C20_DIR / path.rsplit("/", 1)[-1]
        if dest.exists():
            continue
        time.sleep(DELAY_S)
        resp = client.get(CENSUS_NADA + path)
        resp.raise_for_status()
        tmp = dest.with_suffix(".part")
        tmp.write_bytes(resp.content)
        tmp.replace(dest)


def c13_rows(today: str) -> list[dict[str, str]]:
    return [
        {
            "file": f"data/raw/census2011/c13_age/{path.rsplit('/', 1)[-1]}",
            "source_url": CENSUS_NADA + path,
            "downloaded_on": today,
            "licence": "Govt of India (ORGI) public data; no licence stated on the page",
            "downloaded_by": "Claude Code",
            "notes": f"Census 2011 C-13 single-year age; state id {sid}",
        }
        for sid, path in sorted(C13_PATHS.items())
    ]


def download_c13(client: httpx.Client) -> None:
    C13_DIR.mkdir(parents=True, exist_ok=True)
    for path in C13_PATHS.values():
        dest = C13_DIR / path.rsplit("/", 1)[-1]
        if dest.exists():
            continue
        time.sleep(DELAY_S)
        resp = client.get(CENSUS_NADA + path)
        resp.raise_for_status()
        tmp = dest.with_suffix(".part")
        tmp.write_bytes(resp.content)
        tmp.replace(dest)


def income_row(today: str) -> dict[str, str]:
    return {
        "file": "data/raw/income/tab111a.pdf",
        "source_url": INCOME_URL,
        "downloaded_on": today,
        "licence": "Govt of India (Ministry of Finance) public report; no licence text. "
        "Robots.txt: none (404)",
        "downloaded_by": "Claude Code",
        "notes": "Economic Survey 2023-24 Table 1.11A per capita NSDP, current prices "
        "(source: state DES / MoSPI). Used for the income term (beta2)",
    }


def download_income(client: httpx.Client) -> None:
    INCOME_DIR.mkdir(parents=True, exist_ok=True)
    if INCOME_PDF.exists():
        return
    time.sleep(DELAY_S)
    resp = client.get(INCOME_URL)
    resp.raise_for_status()
    tmp = INCOME_PDF.with_suffix(".part")
    tmp.write_bytes(resp.content)
    tmp.replace(INCOME_PDF)


def compendium_rows(today: str) -> list[dict[str, str]]:
    return [
        {
            "file": f"data/raw/nfhs/compendium/{name}",
            "source_url": f"{DHS_BASE}/{name}",
            "downloaded_on": today,
            "licence": "Govt of India (MoHFW/IIPS) public report; no licence text on page",
            "downloaded_by": "Claude Code",
            "notes": "NFHS-5 state/UT fact sheets. Used for state-level bank, phone, internet",
        }
        for name in COMPENDIUM_FILES
    ]


def download_compendium(client: httpx.Client) -> None:
    COMPENDIUM_DIR.mkdir(parents=True, exist_ok=True)
    for name in COMPENDIUM_FILES:
        dest = COMPENDIUM_DIR / name
        if dest.exists():
            continue
        time.sleep(DELAY_S)
        resp = client.get(f"{DHS_BASE}/{name}")
        resp.raise_for_status()
        tmp = dest.with_suffix(".part")
        tmp.write_bytes(resp.content)
        tmp.replace(dest)


def main() -> None:
    k, n = shard_arg(sys.argv)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    rows: list[dict[str, str]] = []
    failed: list[tuple[str, str]] = []
    with httpx.Client(headers=HEADERS, timeout=60, follow_redirects=True) as client:
        for name, url, licence, note in (
            (
                "district_links.csv",
                LINKS_URL,
                "Not stated for data (repo code is MIT)",
                "District list only (state, district). Third-party list built from IIPS pages",
            ),
            (
                "telangana_district_values.csv",
                TG_URL,
                "CC BY 4.0",
                "Telangana district names + cross-check values (pratapvardhan/NFHS-5)",
            ),
        ):
            dest = RAW / name
            if not dest.exists():
                resp = client.get(url)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
            rows.append(list_row(name, url, licence, note, today))
        download_census(client)
        rows.append(census_row(today))
        download_c20(client)
        download_compendium(client)
        download_c13(client)
        download_income(client)
        rows.append(income_row(today))
        rows.extend(c13_rows(today))
        rows.extend(compendium_rows(today))
        rows.extend(c20_rows(today))
        pairs = read_links(RAW / "district_links.csv") + read_tg_names(
            RAW / "telangana_district_values.csv"
        )
        pairs = pairs[k::n]
        for i, (state, district, hint) in enumerate(pairs, 1):
            file = download_district(client, state, district, hint)
            if file is None:
                failed.append((state, district))
            else:
                rows.append(pdf_row(file, today))
            if i % 50 == 0:
                print(f"{i}/{len(pairs)} done, {len(failed)} failed", flush=True)
    if n == 1:
        add_manifest_rows(MANIFEST, rows)
    n_pdfs = len(rows) - 3 - len(C20_PATHS) - len(C13_PATHS) - len(COMPENDIUM_FILES) - 1
    print(f"Worker {k}/{n}: {n_pdfs} PDFs. Failed: {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
