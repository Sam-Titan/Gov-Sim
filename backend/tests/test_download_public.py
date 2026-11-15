from pathlib import Path

from scripts import download_public as dp


def test_filename_candidates_plain() -> None:
    assert dp.filename_candidates("RJ", "Ajmer") == ["RJ_Ajmer.pdf"]


def test_filename_candidates_spaces_and_brackets() -> None:
    names = dp.filename_candidates("BR", "Kaimur (Bhabua)")
    assert names[0] == "BR_Kaimur_(Bhabua).pdf"
    assert "BR_Kaimur.pdf" in names


def test_filename_candidates_ampersand() -> None:
    assert "AN_North_and_Middle_Andaman.pdf" in dp.filename_candidates(
        "AN", "North & Middle Andaman"
    )


def test_read_links_skips_chandigarh(tmp_path: Path) -> None:
    f = tmp_path / "links.csv"
    f.write_text(
        ",state,district,link\n"
        "0,Rajasthan,Ajmer,NFHS-5_FCTS/RJ/Ajmer.pdf\n"
        "1,Chandigarh,Chandigarh,NFHS-5_FCTS/CH/Chandigarh.pdf\n",
        encoding="utf-8",
    )
    assert dp.read_links(f) == [("RJ", "Ajmer", "Ajmer")]


def test_add_manifest_rows_no_duplicates(tmp_path: Path) -> None:
    m = tmp_path / "MANIFEST.csv"
    row = dp.pdf_row("RJ_Ajmer.pdf", "2026-11-15")
    dp.add_manifest_rows(m, [row])
    dp.add_manifest_rows(m, [row])
    assert len(dp.load_manifest(m)) == 1


def test_filename_hint_goes_first() -> None:
    names = dp.filename_candidates("UP", "Bulandshahar", "Bulandshahr")
    assert names[0] == "UP_Bulandshahr.pdf"
