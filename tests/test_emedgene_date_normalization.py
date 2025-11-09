import pandas as pd
from tools.emedgene_csv_converter_core import force_dates_iso


def test_date_normalization():
    df = pd.DataFrame({
        "DOB": ["5/19/1991", "2020-01-03", "01-02-2001", None]
    })

    force_dates_iso(df, ["DOB"])
    assert df["DOB"].tolist() == ["1991-05-19", "2020-01-03", "2001-01-02", ""]
