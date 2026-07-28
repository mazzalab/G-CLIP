import re
import pandas as pd

OUTPUT_HEADER = [
    "Sample ID*", "Well Position*", "RGID", "RGPU", "RGPL", "RGLB",
    "RGCN", "RGPM", "Sample_Project", "Project",
]

REQUIRED_COLUMNS = ["Id", "Plate position"]

_WELL_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def _pad_well_position(raw: str) -> str:
    """Normalizza una posizione di piastra (es. 'F9' -> 'F09')."""
    match = _WELL_RE.match(raw.strip())
    if not match:
        return raw.strip()

    letters, digits = match.groups()
    return f"{letters.upper()}{digits.zfill(2)}"


def convertitore_samplesheet(excel_file: str, output_file: str, project: str) -> list:
    """
    Converte un file Excel Slims Extraction nel formato "import sample
    template" (Sample ID / Well Position / Project).

    Parametri
    ----------
    excel_file : str
        Path del file Excel Slims Extraction (.xlsx).
    output_file : str
        Path del file CSV di output da generare.
    project : str
        Valore da inserire nella colonna "Project" per ogni campione.

    Returns
    -------
    list
        Lista di Sample ID per cui manca la Well Position nell'Excel
        (warning, non bloccante). Il file di output viene generato
        comunque, con Well Position vuota per questi campioni.
    """
    df = pd.read_excel(excel_file, skiprows=2, dtype=str)

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            "Il file Excel non contiene le colonne richieste: "
            + ", ".join(missing_cols)
        )

    rows = []
    missing_well = []

    for _, row in df.iterrows():
        raw_id = row["Id"]
        if pd.isna(raw_id) or not str(raw_id).strip():
            continue

        sample_id = str(raw_id).strip()

        raw_well = row["Plate position"]
        if pd.isna(raw_well) or not str(raw_well).strip():
            well_position = ""
            missing_well.append(sample_id)
        else:
            well_position = _pad_well_position(str(raw_well))

        rows.append((sample_id, well_position))

    with open(output_file, "w", encoding="utf-8", newline="") as out:
        out.write(",".join(OUTPUT_HEADER) + "\n")
        for sample_id, well_position in rows:
            # Sample ID*, Well Position*, RGID, RGPU, RGPL, RGLB, RGCN, RGPM, Sample_Project, Project
            out.write(f"{sample_id},{well_position},,,,,,,,{project}\n")

    return missing_well
