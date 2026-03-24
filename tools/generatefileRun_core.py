from tkinter import filedialog, messagebox
import csv
import pandas as pd

def load_csv(self):
    file_path = filedialog.askopenfilename(
        title="Select SampleSheet CSV file",
        filetypes=[("CSV files", "*.csv")],   # 🔒 solo .csv
        defaultextension=".csv"
    )

    if not file_path:
        return  # annullato

    try:
        with open(file_path, newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                print(row)

        messagebox.showinfo("Success", "CSV file loaded successfully")

    except Exception as e:
        messagebox.showerror("Error", f"Cannot load CSV:\n{e}")


def mapping_slims_emedgene(input_file,output_file,run_name):
    df = pd.read_excel(input_file, skiprows =2,dtype=str)
    print(df.head())

    def convert_sex(gender):
        if gender == "Male":
            return "M"
        if gender == "Female":
            return "F"
        return ""

    #emedgene = pd.DataFrame()
    emedgene = pd.DataFrame(index=df.index)
    emedgene["Family Id"] = "" #colonnaslims
    emedgene["Case Type"] = "Exome"
    emedgene["Files Names"] = "auto"
    emedgene["Sample Type"] = "FASTQ"

    emedgene["BioSample Name"] = df["Sample Original ID"]#df["Id"] #df.apply(build_biosample, axis=1)

    emedgene["Visualization Files"] = ""
    emedgene["Storage Provider Id"] = 774
    emedgene["Default Project"] = run_name
    emedgene["Execute Now"] = ""
    emedgene["Relation"] = df["Relation (rdrc_name)"]
    emedgene["Sex"] = df["Gender"].apply(convert_sex)

    emedgene["Phenotypes"] = df["Phenotype"]
    emedgene["Phenotypes Id"] = df["HPO"]

    emedgene["Date Of Birth"] = df["Patient Date Of Birth"]
    emedgene["Boost Genes"] = "" #ci sarà colonna slims
    emedgene["Gene List Id"] = "" #ci sarà colonna slims
    emedgene["Kit Id"] = 951 #cambierà nel tempo
    emedgene["Intersect Bed Id"] = 951 #cambierà nel tempo

    emedgene["Selected Preset"] = ""
    emedgene["Label Id"] = "" #calcolare
    emedgene["Clinical Notes"] = ""
    emedgene["Due Date"] = ""
    emedgene["Opt In"] = ""

    emedgene["CodiceCampione"] = df["Accession Number"]
    emedgene["CodiceCampioneCI"] = df["Id"]

    emedgene["DataRichiesta"] = df["Date Accessioned"]
    emedgene["DataRicezioneCampione"] = df["Collection date"]

    emedgene["Etnia"] = df["Ethnicity (rdrc_name)"]

    emedgene["FaseAnalitica"] = ""#df["Technician"]
    emedgene["Firma1"] = ""
    emedgene["Firma2"] = ""
    emedgene["MedicoRichiedente"] = (
        df["Requesting Physicians Last Name"]
        + " "
        + df["Requesting Physicians First Name"]
    )

    emedgene["Paziente"] = (
        df["Patient First Name"]
        + " "
        + df["Patient Last Name"]
    )

    emedgene["Protocollo"] = df["Protocol (rdrc_name)"]

    emedgene["QuesitoDiagnostico"] = ""

    emedgene["TipoDiAnalisi"] = "Analisi Esoma Completo"

    emedgene["TipologiaCampione"] = df["Type (cntp_name)"] #"Sangue"

    emedgene["UnitaOperativaRichiedente"] = "" #campoda creare su slims

    emedgene["CodiceLaboratorio"] = 2348

    num_cols = len(emedgene.columns)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("[Data]" + ","*(num_cols-1) + "\n")

    emedgene.to_csv(output_file, mode="a", index=False)


    print("File generato:", output_file)

import csv
import pandas as pd


def convertitore_samplesheet_WES(samplesheet: str, output_file: str, excel_file: str, run_name: str) -> list:
    """
    Converte una SampleSheet LIMS nel formato richiesto per il run WES.

    Parametri
    ----------
    samplesheet : str
        Path del file CSV SampleSheet originale (LIMS).
    output_file : str
        Path del file CSV di output da generare.
    excel_file : str
        Path del file Excel Slims Extraction (.xlsx).
    run_name : str
        Nome della run da inserire nell'header del file di output.

    Returns
    -------
    list
        Lista di Sample_ID presenti nel SampleSheet ma non trovati
        nell'Excel. Lista vuota se tutti i campioni sono presenti.
        Il file di output viene generato in ogni caso.
    """

    # -------------------------
    # CARICA EXCEL PAZIENTI
    # -------------------------
    df = pd.read_excel(excel_file, skiprows=2,dtype=str)
    # Normalizza anche gli ID dell'Excel rimuovendo eventuale suffisso dopo "_"
    valid_ids = set(df["Sample Original ID"].astype(str).str.split("_").str[0])

    # -------------------------
    # LEGGI SAMPLE SHEET LIMS
    # -------------------------
    samples = []   # lista di (sample_id, index1, index2) — tutti i campioni validi
    missing = []   # Sample_ID non trovati nell'Excel (warning, non bloccante)

    with open(samplesheet, newline="") as f:
        # salta fino alla sezione [Data]
        for line in f:
            if line.strip() == "[Data]":
                break

        reader = csv.DictReader(f)
        for row in reader:
            raw_id = row["Sample_ID"]

            if raw_id.startswith("null"):
                continue

            # Rimuove il suffisso dopo il primo "_" (es. "2025019512_DNA" → "2025019512")
            sample_id = raw_id.split("_")[0]

            index1 = row["index"]
            index2 = row["index2"]

            # Aggiunge sempre il campione all'output
            samples.append((sample_id, index1, index2))

            # Controlla coerenza con Excel: registra il mancante ma non blocca
            if sample_id not in valid_ids:
                missing.append(sample_id)

    # -------------------------
    # SCRIVI OUTPUT
    # -------------------------
    with open(output_file, "w", newline="") as out:
        out.write(
            f"[Header],\n"
            f"FileFormatVersion,2\n"
            f"RunName,{run_name}\n"
            f"InstrumentPlatform,NovaSeq\n"
            f"IndexOrientation,Forward\n"
            f"AnalysisLocation,Cloud\n"
            f"[Reads]\n"
            f"Read1Cycles,151\n"
            f"Read2Cycles,151\n"
            f"Index1Cycles,10\n"
            f"Index2Cycles,10\n"
            f"[Sequencing_Settings]\n"
            f"LibraryPrepKits,IlluminaDNAPrepwithExomev25Enrichment\n"
            f"[BCLConvert_Settings]\n"
            f"SoftwareVersion,4.3.13\n"
            f"AdapterRead1,CTGTCTCTTATACACATCT\n"
            f"AdapterRead2,CTGTCTCTTATACACATCT\n"
            f"OverrideCycles,Y151;I10;I10;Y151\n"
            f"FastqCompressionFormat,gzip\n"
            f"[BCLConvert_Data]\n"
            f"Sample_ID,Index,Index2\n"
        )
        for sample_id, i1, i2 in samples:
            out.write(f"{sample_id},{i1},{i2}\n")

        out.write(
            f"\n"
            f"[Cloud_Settings]\n"
            f"GeneratedVersion,1.22.0\n"
            f"Cloud_Workflow,ica_workflow_1\n"
            f"[Cloud_Data]\n"
            f"Sample_ID,ProjectName,LibraryName,LibraryPrepKitName,IndexAdapterKitName\n"
        )
        for sample_id, i1, i2 in samples:
            library = f"{sample_id}_{i1}_{i2}"
            out.write(
                f"{sample_id},,{library},"
                f"IlluminaDNAPrepwithExomev25Enrichment,"
                f"IlluminaDNARNAUDISetBTagmentation\n"
            )

    return missing