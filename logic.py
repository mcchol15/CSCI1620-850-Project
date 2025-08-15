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

    def update(self):
        """this chunk is called when the user hits the add period button, it takes all the information the user selects and creates/appends a csv file to store the practice information"""
        opp = self.selectOppBox.currentText()
        pNum = self.selectPracNumBox.currentText()
        date = self.pracDateCalendar.selectedDate().toString("MM-dd-yy")
        period = self.selectPracPeriodBox.currentText()
        try:
            """Error coding to ensure a number is entered"""
            time = float(self.periodDurTextEdit.toPlainText().strip())
        except ValueError:
            print('Please enter a valid period number.')
            return

        """creates new csv file to allow for historical comparison"""
        csv_name = f'{opp} - {pNum} - {date}.csv'
        folder = "Practice Scripts"
        full_path = os.path.join(folder, csv_name)
        file_exists = os.path.isfile(full_path)

        """create/set up/define the new rows getting written to the csv file"""
        header = ['Period','Time','PL / min', 'Total PL']
        row = [period, time, round(plValues_dict[period]['PLm'],2), round(float(time*plValues_dict[period]['PLm']),1)]
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

    def view_Practice(self, full_path):
        """This chunk is used to display the practice data and is the underlying table set up"""
        practice = pd.read_csv(full_path)
        self.tableWidget.setRowCount(len(practice))
        self.tableWidget.setColumnCount(len(practice.columns))
        self.tableWidget.setHorizontalHeaderLabels(practice.columns)

        for row in range(len(practice)):
            for col in range(len(practice.columns)):
                value = str(practice.iat[row, col])
                self.tableWidget.setItem(row, col, QTableWidgetItem(value))

    def practice_Total(self,full_path):
        """This chunk is used to display the total practice load and is the underlying LCD set up"""
        totals = pd.read_csv(full_path)
        total = totals['Total PL'].sum()
        return total

    def practiceTime_Total(self,full_path):
        """This chunk is used to display the total practice time and is the underlying LCD set up"""
        totals = pd.read_csv(full_path)
        timeTotal = totals['Time'].sum()
        return timeTotal

def get_opponents():
    """This chunk allows for the loading of the opponents from the individual csv file"""
    #self.selectOppBox.addItems(logic.get_opponents())
    opponents = pd.read_csv('Opponents.csv')
    return opponents['Opponent'].dropna().tolist()

def get_practiceNum():
    """This chunk allows for selecting of the different practice number for that week"""
    #self.selectPracNumBox.addItems(logic.get_practiceNum())
    practices = ['P1', 'P2', 'P3', 'P4']
    return practices

def get_periodNames():
    """This chunk allows for the creation of the list of previously succinct and prepared period names (building blocks for practice)"""
    #self.selectPracPeriodBox.addItems(logic.get_periodNames())
    return list(plValues_dict.keys())