import os
import pandas as pd
from PyQt6.QtWidgets import *
from addWindow_gui import *
import csv

plValues = pd.read_csv('Period Amounts.csv')
plValues_dict = plValues.set_index('Period.Name').to_dict(orient='index')

class Logic(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.addButton.clicked.connect(lambda: self.update())
        self.removeButton.clicked.connect(self.remove_selected_period)

    def update(self):
        """this chunk is called when the user hits the add period button, it takes all the information the user selects and creates/appends a csv file to store the practice information"""
        opp = self.selectOppBox.currentText()
        pNum = self.selectPracNumBox.currentText()
        date = self.pracDateCalendar.selectedDate().toString("MM-dd-yy")
        period = self.selectPracPeriodBox.currentText()
        try:
            """Error coding to ensure a number is entered"""
            time = float(self.periodDurTextEdit.toPlainText().strip())
            if time < 0 or time > 300:
                raise ValueError
        except ValueError:
            self.numberError('Enter a valid number (0-300)')
            print('Please enter a valid period number.')
            return

        """creates new csv file to allow for historical comparison"""
        csv_name = f'{opp} - {pNum} - {date}.csv'
        folder = "Practice Scripts"
        full_path = os.path.join(folder, csv_name)
        file_exists = os.path.isfile(full_path)

        """create/set up/define the new rows getting written to the csv file"""
        header = ['Period','Time','PL / min', 'Total PL']
        row = [period, time, round(plValues_dict[period]['PLm.Avg'],2), round(float(time*plValues_dict[period]['PLm.Avg']),1)]
        with open(full_path, mode = 'a' if file_exists else 'w', newline = '') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(row)

        """Update the table view and and practice total with each button click"""
        self.view_Practice(full_path)
        total = self.practice_Total(full_path)
        timeTotal = self.practiceTime_Total(full_path)
        self.practiceTotalLcd.display(total)
        self.practiceDurTotalLcd.display(timeTotal)

    def _current_practice_csv_path(self) -> str:
        """
        Builds the CSV path based on the currently selected Opponent, Practice #, and Date.
        Matches the naming used when adding rows.
        """
        opp = self.selectOppBox.currentText()
        pNum = self.selectPracNumBox.currentText()
        date = self.pracDateCalendar.selectedDate().toString("MM-dd-yy")
        csv_name = f"{opp} - {pNum} - {date}.csv"
        folder = "Practice Scripts"
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

def get_opponents() -> list:
    """This chunk allows for the loading of the opponents from the individual csv file"""
    #self.selectOppBox.addItems(logic.get_opponents())
    opponents = ['FC-Wk1','FC-Wk2','FC-Wk3','FC-Wk4','01 - Cincinnati','02 - Akron','03 - HCU','04 - Michigan','05 - Bye 1','06 - Michigan State','07 - Maryland','08 - Minnesota','09 - Northwestern','10 - USC','11 - UCLA','12 - Bye 2','13 - Penn State','14 - Iowa']
    return opponents

def get_practiceNum() -> list:
    """This chunk allows for selecting of the different practice number for that week"""
    #self.selectPracNumBox.addItems(logic.get_practiceNum())
    practices = ['P1', 'P2', 'P3', 'P4','Game', 'Walk Thru']
    return practices

def get_periodNames() -> list:
    """This chunk allows for the creation of the list of previously succinct and prepared period names (building blocks for practice)"""
    #self.selectPracPeriodBox.addItems(logic.get_periodNames())
    return list(plValues_dict.keys())