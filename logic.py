import os
import pandas as pd
from PyQt6.QtWidgets import *
from addWindow_gui import *
import csv

plValues = pd.read_csv('Period Amounts.csv')
plValues_dict = plValues.set_index('Period.Name').to_dict(orient='index')

"""These need to be added to the bottom of the gui file anytime it is updated"""
#self.selectPracPeriodBox.addItems(logic.get_periodNames())
#self.selectPracNumBox.addItems(logic.get_practiceNum())
#self.selectOppBox.addItems(logic.get_opponents())

class Logic(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.addButton.clicked.connect(lambda: self.update())
        self.removeButton.clicked.connect(self.remove_selected_period)
        self.editButton.clicked.connect(self.edit_period_time)
        self.populate_prev_practice_box()
        self.loadPrevPracButton.clicked.connect(self.load_previous_practice)

    def update(self) -> None:
        """
        Add a new period row to the current practice CSV using the existing UI inputs,
        then refresh the table and totals.

        CSV path (and name) comes from the current Opponent, Practice #, and Date
        via _current_practice_csv_path(), matching the rest of the app.
        """
        import os, csv
        from PyQt6.QtWidgets import QMessageBox

        # ---- 1) Collect inputs from your UI ----
        # Period name (single line or multi-line widget; try both common cases)
        period = ""
        if hasattr(self, "addPeriodNameTextEdit"):
            period = (self.addPeriodNameTextEdit.toPlainText() or "").strip()
        elif hasattr(self, "addPeriodNameLineEdit"):
            period = (self.addPeriodNameLineEdit.text() or "").strip()

        # Time (expect an integer number of minutes; if you allow mm:ss, adapt as needed)
        time_raw = ""
        if hasattr(self, "addPeriodNewTimeTextEdit_2"):
            time_raw = (self.addPeriodNewTimeTextEdit_2.toPlainText() or "").strip()
        elif hasattr(self, "addPeriodNewTimeTextEdit"):
            time_raw = (self.addPeriodNewTimeTextEdit.toPlainText() or "").strip()
        elif hasattr(self, "addPeriodTimeLineEdit"):
            time_raw = (self.addPeriodTimeLineEdit.text() or "").strip()

        # PL / min (commonly a spin box); if not present, default to 0.0
        pl_per_min = 0.0
        if hasattr(self, "plPerMinDoubleSpinBox"):
            pl_per_min = float(self.plPerMinDoubleSpinBox.value())

    def _current_practice_csv_path(self) -> str:
        import os
        opp = self.selectOppBox.currentText()
        pNum = self.selectPracNumBox.currentText()
        date = self.pracDateCalendar.selectedDate().toString("MM-dd-yy")
        csv_name = f"{opp} - {pNum} - {date}.csv"
        folder = "Practice Scripts"  # <-- unified folder name
        return os.path.join(folder, csv_name)

    def remove_selected_period(self) -> None:
        """
        Remove the row (1-based index) specified in rmvPeriodTextEdit
        from the current practice CSV, then refresh the view/totals.
        """
        import os, csv

        # 1) Get row number from the text box (expects 1-based indexing)
        raw = self.rmvPeriodTextEdit.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, "Missing Row", "Enter a row number to remove (e.g., 1, 2, 3).")
            return

        try:
            row_num = int(raw)
            if row_num <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.critical(self, "Invalid Row", "Row number must be a positive integer.")
            return

        # 2) Build path to the active CSV
        csv_path = self._current_practice_csv_path()
        if not os.path.isfile(csv_path):
            QMessageBox.critical(self, "File Not Found",
                                 f"No practice CSV found for the current selection:\n{csv_path}")
            return

        # 3) Read all rows and validate the index
        with open(csv_path, newline="") as f:
            reader = list(csv.reader(f))

        if not reader:
            QMessageBox.information(self, "Empty File", "This practice file has no rows to remove.")
            return

        # If you wrote a header when creating the file, keep it
        header_present = False
        if reader and any(h.lower() in ("period", "time", "pl / min", "total pl") for h in reader[0]):
            header_present = True

        data_start = 1 if header_present else 0
        data_len = len(reader) - data_start

        if row_num > data_len:
            QMessageBox.critical(self, "Out of Range",
                                 f"Row {row_num} does not exist. There are only {data_len} data rows.")
            return

        # Convert to 0-based index in the data section and delete
        target_idx = data_start + (row_num - 1)
        del reader[target_idx]

        # 4) Write back
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(reader)

        # 5) Refresh UI (these calls assume you already have them wired elsewhere)
        try:
            # If you have these methods, they’ll re-render the table and totals
            self.view_Practice(csv_path)
        except Exception:
            pass

        try:
            self.practice_Total(csv_path)
        except Exception:
            pass

        try:
            self.practiceTime_Total(csv_path)
        except Exception:
            pass

        # 6) Clear the input and notify
        self.rmvPeriodTextEdit.clear()
        QMessageBox.information(self, "Removed", f"Row {row_num} removed.")


    def view_Practice(self, full_path: str) -> None:
        """This chunk is used to display the practice data and is the underlying table set up"""
        practice = pd.read_csv(full_path)
        self.tableWidget.setRowCount(len(practice))
        self.tableWidget.setColumnCount(len(practice.columns))
        self.tableWidget.setHorizontalHeaderLabels(practice.columns)

        for row in range(len(practice)):
            for col in range(len(practice.columns)):
                value = str(practice.iat[row, col])
                self.tableWidget.setItem(row, col, QTableWidgetItem(value))

    def practice_Total(self,full_path: str) -> int:
        """This chunk is used to display the total practice load and is the underlying LCD set up"""
        totals = pd.read_csv(full_path)
        total = totals['Total PL'].sum()
        return total

    def practiceTime_Total(self,full_path: str) -> int:
        """This chunk is used to display the total practice time and is the underlying LCD set up"""
        totals = pd.read_csv(full_path)
        timeTotal = totals['Time'].sum()
        return timeTotal

    def numberError(self, errorMessage: str) -> None:
        """This chunk is used to display the error message if needed"""
        error_box = QMessageBox()
        error_box.setText(errorMessage)
        error_box.exec()

    def edit_period_time(self) -> None:
        """
        Overwrite the 'Time' for a specific 1-based data row in the active CSV.
        Prefers self._active_csv_path (set by load_previous_practice), else uses the
        path derived from current UI via _current_practice_csv_path().
        """
        import os, csv
        from PyQt6.QtWidgets import QMessageBox

        # Inputs
        row_raw = (self.editPeriodRowNumTextEdit.toPlainText() or "").strip()
        time_raw = (self.editPeriodNewTimeTextEdit_2.toPlainText() or "").strip()

        if not row_raw:
            QMessageBox.warning(self, "Missing Row", "Enter the row number you want to edit.")
            return
        if not time_raw:
            QMessageBox.warning(self, "Missing Time", "Enter the new time (integer minutes).")
            return

        try:
            row_num = int(row_raw)
            if row_num <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.critical(self, "Invalid Row", "Row number must be a positive integer (1, 2, 3, …).")
            return

        try:
            new_time = float(int(time_raw))  # integer minutes stored as float for math/CSV consistency
        except ValueError:
            QMessageBox.critical(self, "Invalid Time", "Time must be an integer number of minutes.")
            return

        # Resolve active path: prefer the pinned target set by the loader
        csv_path = getattr(self, "_active_csv_path", None) or self._current_practice_csv_path()
        if not os.path.isfile(csv_path):
            QMessageBox.critical(self, "File Not Found",
                                 f"No practice CSV found for the current selection:\n{csv_path}")
            return

        # Read CSV
        with open(csv_path, newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            QMessageBox.information(self, "Empty File", "This practice file has no rows to edit.")
            return

        # Column indices (match add flow header)
        header = rows[0]
        try:
            idx_time = header.index('Time')
            idx_plm = header.index('PL / min')
            idx_total = header.index('Total PL')
        except ValueError:
            QMessageBox.critical(self, "Missing Columns",
                                 "Could not find required columns: Time, PL / min, Total PL.")
            return

        data_start = 1
        data_len = len(rows) - data_start
        if row_num > data_len:
            QMessageBox.critical(self, "Out of Range",
                                 f"Row {row_num} does not exist. There are only {data_len} data rows.")
            return

        # Update the row
        target_idx = data_start + (row_num - 1)
        row_vals = rows[target_idx]
        try:
            pl_per_min = float(row_vals[idx_plm])
        except Exception:
            QMessageBox.critical(self, "Bad Data", "The 'PL / min' value in that row is not numeric.")
            return

        row_vals[idx_time] = str(new_time)
        row_vals[idx_total] = str(round(new_time * pl_per_min, 1))
        rows[target_idx] = row_vals

        # Write back
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerows(rows)

        # Refresh UI & totals
        self.view_Practice(csv_path)
        total = self.practice_Total(csv_path)
        time_total = self.practiceTime_Total(csv_path)
        self.practiceTotalLcd.display(total)
        self.practiceDurTotalLcd.display(time_total)

        # Clear inputs
        self.editPeriodRowNumTextEdit.clear()
        self.editPeriodNewTimeTextEdit_2.clear()

        QMessageBox.information(self, "Edited", f"Updated row {row_num} time to {int(new_time)}.")

    def populate_prev_practice_box(self) -> None:
        """
        Fill selectPrevPracBox with all .csv files from Practice scripts/.
        """
        import os
        folder = "Practice scripts"
        self.selectPrevPracBox.clear()

        if not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)

        files = [f for f in os.listdir(folder) if f.lower().endswith(".csv")]
        files.sort()

        for name in files:
            full_path = os.path.join(folder, name)
            self.selectPrevPracBox.addItem(name, full_path)

    def load_previous_practice(self) -> None:
        """
        Use the selected previous practice CSV as a TEMPLATE:
          - DO NOT change the current UI selections (Opponent, Practice #, Date).
          - Compute the TARGET path from the current UI via _current_practice_csv_path().
          - Copy the selected CSV into that TARGET path (creating folder if needed).
          - Load the TARGET file into the table and set self._active_csv_path to it,
            so subsequent Edit/Update/Remove operate on the new file.
        """
        import os, shutil
        from PyQt6.QtWidgets import QMessageBox

        # 1) Get the source file from the dropdown
        idx = self.selectPrevPracBox.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "No Selection", "Choose a practice file to load as a template.")
            return

        source_csv_path = self.selectPrevPracBox.itemData(idx)
        if not source_csv_path or not os.path.isfile(source_csv_path):
            QMessageBox.critical(self, "File Not Found", "The selected template file could not be found.")
            return

        # 2) Compute the TARGET path from the CURRENT UI selections (Opponent, Practice #, Date)
        target_csv_path = self._current_practice_csv_path()
        target_folder = os.path.dirname(target_csv_path)
        os.makedirs(target_folder, exist_ok=True)

        # 3) If the target doesn't exist, create it by copying the source template
        if not os.path.isfile(target_csv_path):
            shutil.copyfile(source_csv_path, target_csv_path)

        # 4) Pin the active CSV to the TARGET so future edits hit the new file
        self._active_csv_path = target_csv_path

        # 5) Render table & totals from the TARGET file
        self.view_Practice(target_csv_path)
        total = self.practice_Total(target_csv_path)
        time_total = self.practiceTime_Total(target_csv_path)
        self.practiceTotalLcd.display(total)
        self.practiceDurTotalLcd.display(time_total)

        QMessageBox.information(
            self,
            "Loaded",
            f"Loaded template:\n{os.path.basename(source_csv_path)}\n\n"
            f"Working copy:\n{os.path.basename(target_csv_path)}"
        )


def get_opponents() -> list:
    """This chunk allows for the loading of the opponents from the individual csv file"""
    opponents = ['FC-Wk1','FC-Wk2','FC-Wk3','FC-Wk4','01 - Cincinnati','02 - Akron','03 - HCU','04 - Michigan','05 - Bye 1','06 - Michigan State','07 - Maryland','08 - Minnesota','09 - Northwestern','10 - USC','11 - UCLA','12 - Bye 2','13 - Penn State','14 - Iowa']
    return opponents

def get_practiceNum() -> list:
    """This chunk allows for selecting of the different practice number for that week"""
    practices = ['P1', 'P2', 'P3', 'P4','Game', 'Walk Thru']
    return practices

def get_periodNames() -> list:
    """This chunk allows for the creation of the list of previously succinct and prepared period names (building blocks for practice)"""
    return list(plValues_dict.keys())