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




def validate_excel_content(file_path):
    """
    Controlla la presenza di colonne obbligatorie e campi vuoti.
    Ritorna (True, None) se ok, o (False, "messaggio errore") se fallisce.
    """
    
    REQUIRED_COLUMNS = ["Family Id","Relation (rdrc_name)","Gender","Phenotype","HPO","Patient Date Of Birth","Accession Number","Id","Date Accessioned","Requesting Physicians User Name","Patient First Name","Patient Last Name","Protocol (rdrc_name)","Type (cntp_name)","Requesting Unit"] #"Boost Genes","Indication","Ethnicity (rdrc_name)"
    NON_EMPTY_COLUMNS = ["Family Id","Accession Number","Id","Patient First Name","Patient Last Name","Type (cntp_name)","Gender"]

    #da valutare se possono rimanere vuote o se è meglio renderle obbligatorie:
    #"HPO" puo essere vuoto se unfected il phenotype
    #"Protocol (rdrc_name)" puo essere vuoto se non è specificato, puo essere compilato su emedgene
    #"Requesting Unit","Requesting Physicians Last Name","Requesting Physicians First Name","Ethnicity (rdrc_name)","Date Accessioned","Collection date",,"Patient Date Of Birth","Boost Genes","Indication","Phenotype",
    try:
        df = pd.read_excel(file_path, skiprows=2,dtype=str)  # Carica tutto come stringa per evitare problemi di formattazione
        
        # 1. Controllo Colonne Mancanti
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            msg = "Il file Excel non è conforme.\nColonne mancanti:\n" + "\n".join(f"• {c}" for c in missing_cols)
            return False, msg

        # 2. Controllo Campi Vuoti
        cols_with_empty = [col for col in NON_EMPTY_COLUMNS if df[col].isnull().any()]
        if cols_with_empty:
            msg = "Il file contiene celle vuote in colonne con campi obbligatori:\n" + "\n".join(f"• {c}" for c in cols_with_empty)
            return False, msg

        return True, None

    except Exception as e:
        return False, f"Errore critico durante la lettura dell'Excel: {e}"



def mapping_slims_emedgene(input_file, output_file, run_name,
                            biosample_mode="manuale", biosample_id_column="Id",
                            biosample_suffix="iniziali"):

    df = pd.read_excel(input_file, skiprows =2,dtype=str)
    print(df.head())

    def build_lable(row):
        prot=row["Protocol (rdrc_name)"]
        if prot=="GEN&RARE":
            return "1"
        if prot=="Research_WES":
            return "2"
        if prot=="Genesi":
            return "3"
        return ""

    def convert_sex(gender):
        if gender == "Male":
            return "M"
        if gender == "Female":
            return "F"
        return ""

    def HPOlist(HPO):
        if pd.isna(HPO) or str(HPO).strip() == "":
            return ""
        hpo_terms = [term.strip() for term in str(HPO).split(",") if term.strip()]
        return "; ".join(hpo_terms)



    def identifica_analisi(row, df):
        # Controlliamo se almeno uno dei due campi ha un valore valido
        if "Boost Genes" in df.columns:
            emedgene["Boost Genes"] = df["Boost Genes"] 
            boost_presente = pd.notna(row['Boost Genes']) and str(row['Boost Genes']).strip() != ""
            indication_presente = pd.notna(row['Indication']) and str(row['Indication']).strip() != ""
            
            if boost_presente or indication_presente:
                return "Pannello in silico"
        else:
            return "Analisi Esoma Completo"
        
    ###da modificare se cambia status su slims in inglese al momento cosi:
    def convert_relation(relation):
        #se il campo è Figlio o vuoto (NaN) lo consideriamo Proband, altrimenti traduciamo Madre/Padre
        if relation == "Figlio" or pd.isna(relation) or str(relation).strip() == "":
            return "proband"
        if relation == "Madre":
            return "mother"
        if relation == "Padre":
            return "father"
        return ""

    # BioSample Name: due modalità di costruzione, selezionabili da interfaccia
    # tramite biosample_mode ("manuale" / "routine") e, se manuale,
    # biosample_id_column ("Id" / "Original Content (cntn_id)") e
    # biosample_suffix ("iniziali" / "dna" / "nessuno").
    def build_biosample(row):
        if biosample_mode == "routine":
            # ATTIVA PER NUOVE RUN CON DEFINITIVO: lascia derivata _DNA
            acc = str(row["Id"])
            return f"{acc}"

        # Modalità manuale: SS fatto manualmente
        acc = str(row[biosample_id_column]).split("_")[0]

        if biosample_suffix == "dna":
            return f"{acc}_DNA"

        if biosample_suffix == "nessuno":
            return f"{acc}"

        # "iniziali" (default): iniziali nome/cognome paziente
        # Gestisce cognomi doppi/multipli
        last_names = str(row["Patient Last Name"]).split()
        last_initials = "".join([name[0].upper() for name in last_names if name])

        # Gestisce nomi doppi/multipli
        first_names = str(row["Patient First Name"]).split()
        first_initials = "".join([name[0].upper() for name in first_names if name])

        return f"{acc}_{first_initials}{last_initials}"

    emedgene = pd.DataFrame(index=df.index)
    emedgene["Family Id"] = df["Family Id"] 
    emedgene["Case Type"] = "Exome"
    emedgene["Files Names"] = "auto"
    emedgene["Sample Type"] = "FASTQ"

    #senza _DNA o _RNA, per uniformare con il sample sheet, altrimenti non riesce a trovare i file
    #emedgene["BioSample Name"] = df["Id"] #df.apply(build_biosample, axis=1) #calcolare
    emedgene["BioSample Name"]= df.apply(build_biosample, axis=1) #calcolare

    emedgene["Visualization Files"] = ""
    emedgene["Storage Provider Id"] = 774
    emedgene["Default Project"] = run_name
    emedgene["Execute Now"] = ""
    emedgene["Relation"] = df["Relation (rdrc_name)"]
    #emedgene["Relation"] = df["Relation (rdrc_name)"].apply(convert_relation)
    emedgene["Sex"] = df["Gender"].apply(convert_sex)

    emedgene["Phenotypes"] = df["Phenotype"]

    emedgene["Phenotypes Id"] = df["HPO"].apply(HPOlist)

    emedgene["Date Of Birth"] = pd.to_datetime(df["Patient Date Of Birth"], dayfirst=True).dt.strftime('%Y-%m-%d')
    if "Boost Genes" in df.columns:
        emedgene["Boost Genes"] = df["Boost Genes"] 
    else:
        emedgene["Boost Genes"] = ""
    if "Indication" in df.columns:
        emedgene["Gene List Id"] = df["Indication"] 
    else:
        emedgene["Gene List Id"] = ""
    emedgene["Kit Id"] = 951 #cambierà nel tempo
    emedgene["Intersect Bed Id"] = 951 #cambierà nel tempo

    emedgene["Selected Preset"] = ""
    emedgene["Label Id"] = df.apply(build_lable, axis=1)
    emedgene["Clinical Notes"] = ""
    emedgene["Due Date"] = ""
    emedgene["Opt In"] = ""

    emedgene["CodiceCampione"] = df["Accession Number"]
    emedgene["CodiceCampioneCI"] = df["Id"]

    emedgene["DataRichiesta"] = df["Date Accessioned"]
    #emedgene["DataRicezioneCampione"] = df["Collection date"]
    emedgene["DataRicezioneCampione"] = df["Date Received"]

    #emedgene["Etnia"] = df["Ethnicity (rdrc_name)"]

    emedgene["FaseAnalitica"] = ""#df["Technician"]
    emedgene["Firma1"] = ""
    emedgene["Firma2"] = ""
    # emedgene["MedicoRichiedente"] = (
    #     df["Requesting Physicians Last Name"]
    #     + " "
    #     + df["Requesting Physicians First Name"]
    # )
    emedgene["MedicoRichiedente"] = df["Requesting Physicians User Name"]

    emedgene["Paziente"] = (
        df["Patient First Name"]
        + " "
        + df["Patient Last Name"]
    )

    emedgene["Protocollo"] = df["Protocol (rdrc_name)"]

    emedgene["QuesitoDiagnostico"] = ""
    #emedgene["TipoDiAnalisi"] = df.apply(identifica_analisi, axis=1)
    if "Boost Genes" in df.columns:
    # Applichiamo la funzione riga per riga solo se la colonna esiste
        emedgene["TipoDiAnalisi"] = df.apply(identifica_analisi, axis=1, args=(df,))
    else:
        # Se la colonna non esiste, assegniamo direttamente il valore di default a tutti
        emedgene["TipoDiAnalisi"] = "Analisi Esoma Completo"

    emedgene["TipologiaCampione"] = "Blood" #df["Type (cntp_name)"] #"Sangue"

    emedgene["UnitaOperativaRichiedente"] = df["Requesting Unit"]

    emedgene["CodiceLaboratorio"] = 2348


    num_cols = len(emedgene.columns)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("[Data]" + ","*(num_cols-1) + "\n")

    emedgene.to_csv(output_file, mode="a", index=False)


    print("File generato:", output_file)



def check_samplesheet_samples(samplesheet: str, excel_file: str) -> list:
    """
    Controlla che tutti i Sample_ID della SampleSheet LIMS siano presenti
    nell'Excel Slims Extraction (colonna 'Id'). Non genera alcun file di
    output: ritorna solo l'elenco dei campioni mancanti (lista vuota se
    tutti i campioni sono presenti).
    """
    df = pd.read_excel(excel_file, skiprows=2, dtype=str)
    valid_ids = set(df["Id"].astype(str).str.split("_").str[0])

    missing = []

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

            if sample_id not in valid_ids:
                missing.append(sample_id)

    return missing


# def convertitore_samplesheet_WES(samplesheet: str, output_file: str, excel_file: str, run_name: str) -> list:
#     """
#     Converte una SampleSheet LIMS nel formato richiesto per il run WES.

#     Parametri
#     ----------
#     samplesheet : str
#         Path del file CSV SampleSheet originale (LIMS).
#     output_file : str
#         Path del file CSV di output da generare.
#     excel_file : str
#         Path del file Excel Slims Extraction (.xlsx).
#     run_name : str
#         Nome della run da inserire nell'header del file di output.

#     Returns
#     -------
#     list
#         Lista di Sample_ID presenti nel SampleSheet ma non trovati
#         nell'Excel. Lista vuota se tutti i campioni sono presenti.
#         Il file di output viene generato in ogni caso.
#     """

#     # -------------------------
#     # CARICA EXCEL PAZIENTI
#     # -------------------------
#     df = pd.read_excel(excel_file, skiprows=2,dtype=str)
#     # Normalizza anche gli ID dell'Excel rimuovendo eventuale suffisso dopo "_"
#     #valid_ids = set(df["Sample Original ID"].astype(str).str.split("_").str[0])
#     valid_ids = set(df["Id"].astype(str).str.split("_").str[0])
#     #print(valid_ids)
#     # -------------------------
#     # LEGGI SAMPLE SHEET LIMS
#     # -------------------------
#     samples = []   # lista di (sample_id, index1, index2) — tutti i campioni validi
#     missing = []   # Sample_ID non trovati nell'Excel (warning, non bloccante)

#     with open(samplesheet, newline="") as f:
#         # salta fino alla sezione [Data]
#         for line in f:
#             if line.strip() == "[Data]":
#                 break

#         reader = csv.DictReader(f)
#         for row in reader:
#             raw_id = row["Sample_ID"]

#             if raw_id.startswith("null"):
#                 continue

#             # Rimuove il suffisso dopo il primo "_" (es. "2025019512_DNA" → "2025019512")
#             sample_id = raw_id.split("_")[0]

#             index1 = row["index"]
#             index2 = row["index2"]

#             # Aggiunge sempre il campione all'output
#             samples.append((sample_id, index1, index2))

#             # Controlla coerenza con Excel: registra il mancante ma non blocca
#             if sample_id not in valid_ids:
#                 missing.append(sample_id)

#     # -------------------------
#     # SCRIVI OUTPUT
#     # -------------------------
#     with open(output_file, "w", newline="") as out:
#         out.write(
#             f"[Header],\n"
#             f"FileFormatVersion,2\n"
#             f"RunName,{run_name}\n"
#             f"InstrumentPlatform,NovaSeq\n"
#             f"IndexOrientation,Forward\n"
#             f"AnalysisLocation,Cloud\n"
#             f"[Reads]\n"
#             f"Read1Cycles,151\n"
#             f"Read2Cycles,151\n"
#             f"Index1Cycles,10\n"
#             f"Index2Cycles,10\n"
#             f"[Sequencing_Settings]\n"
#             f"LibraryPrepKits,IlluminaDNAPrepwithExomev25Enrichment\n"
#             f"[BCLConvert_Settings]\n"
#             f"SoftwareVersion,4.3.13\n"
#             f"AdapterRead1,CTGTCTCTTATACACATCT\n"
#             f"AdapterRead2,CTGTCTCTTATACACATCT\n"
#             f"OverrideCycles,Y151;I10;I10;Y151\n"
#             f"FastqCompressionFormat,gzip\n"
#             f"[BCLConvert_Data]\n"
#             f"Sample_ID,Index,Index2\n"
#         )
#         for sample_id, i1, i2 in samples:
#             out.write(f"{sample_id},{i1},{i2}\n")

#         out.write(
#             f"\n"
#             f"[Cloud_Settings]\n"
#             f"GeneratedVersion,1.22.0\n"
#             f"Cloud_Workflow,ica_workflow_1\n"
#             f"[Cloud_Data]\n"
#             f"Sample_ID,ProjectName,LibraryName,LibraryPrepKitName,IndexAdapterKitName\n"
#         )
#         for sample_id, i1, i2 in samples:
#             library = f"{sample_id}_{i1}_{i2}"
#             out.write(
#                 f"{sample_id},,{library},"
#                 f"IlluminaDNAPrepwithExomev25Enrichment,"
#                 f"IlluminaDNARNAUDISetBTagmentation\n"
#             )

#     return missing