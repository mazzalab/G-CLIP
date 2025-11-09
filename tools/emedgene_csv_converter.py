import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os

# Import processing logic from new core module
from tools.emedgene_csv_converter_core import run_conversion, load_hpo_list, resource_path, preselected_date_columns, sample_id_column_default


class CSVConverterPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        tk.Label(self, text="Excel to Emedgene CSV Converter",
                 font=("Arial", 15, "bold")).pack(pady=10)
        tk.Label(self, text="1) Load Excel, 2) Select date columns, 3) Convert",
                 font=("Arial", 11)).pack(pady=5)

        tk.Button(self, text="Load Excel and Show Column Names",
                  width=35, command=self.load_excel).pack(pady=5)

        options_frame = tk.LabelFrame(self, text="Options", padx=10, pady=10)
        options_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(options_frame, text="Header row:").grid(
            row=0, column=0, sticky="w")
        self.header_entry = tk.Entry(options_frame, width=5)
        self.header_entry.insert(0, "2")
        self.header_entry.grid(row=0, column=1, sticky="w")

        tk.Label(options_frame, text="HPO column name:").grid(
            row=1, column=0, sticky="w")
        self.hpo_entry = tk.Entry(options_frame, width=30)
        self.hpo_entry.insert(0, "Phenotypes Id")
        self.hpo_entry.grid(row=1, column=1, sticky="w")

        tk.Label(options_frame, text="Sample ID column name:").grid(
            row=2, column=0, sticky="w")
        self.sampleid_entry = tk.Entry(options_frame, width=30)
        self.sampleid_entry.insert(0, sample_id_column_default)
        self.sampleid_entry.grid(row=2, column=1, sticky="w")

        tk.Label(options_frame, text="Select date columns:").grid(
            row=3, column=0, sticky="nw")
        self.date_listbox = tk.Listbox(
            options_frame, selectmode=tk.MULTIPLE, width=40, height=10)
        self.date_listbox.grid(row=3, column=1, sticky="w")

        tk.Button(self, text="Convert to CLEAN CSV", width=35,
                  command=self.process_excel).pack(pady=10)

    # -------- load_excel --------
    def load_excel(self):
        global loaded_excel_path, df_loaded

        excel_path = filedialog.askopenfilename(
            title="Select patient Excel file",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not excel_path:
            return

        header_row_txt = self.header_entry.get().strip()
        if not header_row_txt.isdigit() or int(header_row_txt) < 1:
            messagebox.showerror(
                "Error", "Header row must be a positive integer.")
            return

        header_row = int(header_row_txt) - 1

        try:
            df = pd.read_excel(excel_path, header=header_row)
            df.columns = df.columns.astype(str).str.strip()

            loaded_excel_path = excel_path
            df_loaded = df

            self.date_listbox.delete(0, tk.END)
            for col in df.columns:
                self.date_listbox.insert(tk.END, col)

            # Preselect default columns
            for i, col in enumerate(df.columns):
                if col.strip() in preselected_date_columns:
                    self.date_listbox.selection_set(i)

            messagebox.showinfo(
                "Excel Loaded", "Columns loaded. Select date columns and then convert.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read Excel:\n{e}")

    # -------- process_excel --------
    def process_excel(self):
        global loaded_excel_path, df_loaded

        if not loaded_excel_path or df_loaded is None:
            messagebox.showerror("Error", "Load an Excel file first.")
            return

        hpo_colname = self.hpo_entry.get().strip()
        if not hpo_colname:
            messagebox.showerror("Error", "HPO column name cannot be empty.")
            return

        sample_id_col = self.sampleid_entry.get().strip() or sample_id_column_default

        # ✅ auto-load HPO from assets
        hpo_path = resource_path(os.path.join("assets", "hp.obo"))
        if not os.path.exists(hpo_path):
            messagebox.showerror("Error", "hp.obo missing in assets folder.")
            return

        valid_hpo_codes = load_hpo_list(hpo_path)

        # Selected date columns
        selected_indices = self.date_listbox.curselection()
        selected_date_cols = [self.date_listbox.get(
            i) for i in selected_indices]

        # ✅ Use new core logic
        processed_df, invalid_records = run_conversion(
            df=df_loaded,
            hpo_colname=hpo_colname,
            date_cols=selected_date_cols,
            valid_hpo_codes=valid_hpo_codes,
            sample_id_col=sample_id_col
        )

        # ✅ Insert the fixed first row: ["DATA", "", "", ...]
        padding_row = ["[DATA]"] + [""] * (len(processed_df.columns) - 1)

        # Output folder
        input_folder = os.path.dirname(loaded_excel_path)
        # result_folder = os.path.join(input_folder, "result")
        result_folder = input_folder  # Save in same folder as input
        os.makedirs(result_folder, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(loaded_excel_path))[0]
        out_csv = os.path.join(result_folder, base_name + "_CLEAN.csv")

        with open(out_csv, "w", encoding="utf-8") as f:
            f.write(",".join(padding_row) + "\n")
            processed_df.to_csv(
                f, index=False, encoding="utf-8", lineterminator="\n", date_format='%Y%m%d')

        # Report HPO errors if found
        if invalid_records:
            report_path = os.path.join(
                result_folder, base_name + "_HPO_ERROR_REPORT.txt")
            with open(report_path, "w", encoding="utf-8") as rep:
                rep.write("Invalid or missing HPO codes:\n\n")
                for row, sample, bad_codes in invalid_records:
                    rep.write(
                        f"Row {row+2} | Sample: {sample} | Invalid: {', '.join(bad_codes)}\n")

            messagebox.showwarning(
                "Completed with warnings",
                f"CSV created: {out_csv}\n\nInvalid HPO codes found. Report:\n{report_path}"
            )
        else:
            messagebox.showinfo("Success", f"CSV created:\n{out_csv}")
