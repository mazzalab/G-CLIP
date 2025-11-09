from tools.emedgene_csv_converter_core import run_conversion
from tools.emedgene_csv_converter import load_hpo_list, resource_path
import pandas as pd
import os


def test_mock_data():
    mock_excel = "tests/data/mock_data.xlsx"
    expected_csv = "tests/data/mock_data_validated.csv"

    df = pd.read_excel(mock_excel, header=1)
    df.columns = df.columns.astype(str).str.strip()

    hpo_path = resource_path(os.path.join("assets", "hp.obo"))
    valid_hpo = load_hpo_list(hpo_path)

    processed, invalid = run_conversion(
        df=df,
        hpo_colname="Phenotypes Id",
        # date_cols=["Date Of Birth", "Due Date",
        #            "DataRichiesta", "DataRicezioneCampione"],
        date_cols=["Date Of Birth"],
        valid_hpo_codes=valid_hpo,
        sample_id_col="BioSample Name"
    )

    expected = pd.read_csv(
        expected_csv,
        skiprows=1  # ,
        # dtype=str
    )

    expected = expected.fillna("")
    processed = processed.fillna("")
    pd.testing.assert_frame_equal(expected, processed, check_dtype=False)
