# -*- coding: utf-8 -*-
from collections import namedtuple
from thread_return import ThreadWithReturnValue
from GUI import Ui_MainWindow
from requests import codes, post
from re import findall
from sys import argv, exit
from traceback import print_exc

from PyQt5.QtCore import QEvent, QRegExp, Qt
from PyQt5.QtGui import QFont, QKeySequence, QPalette, QRegExpValidator
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QHeaderView,
                             QMainWindow, QShortcut, QTableWidget,
                             QTableWidgetItem)


class stock:

    def __init__(self, date, securities_code) -> None:
        self._date = date
        self._securities_code = securities_code
        self._集保戶股權分散表 = self._construct()

    def __len__(self) -> int:
        return len(self._集保戶股權分散表)

    def __getitem__(self, securities_holding_range) -> str:
        return self._集保戶股權分散表[securities_holding_range]

    def __bool__(self) -> bool:
        return bool(self._集保戶股權分散表)

    def __repr__(self) -> str:
        return f'集保戶股權分散表 資料日期:{self._date} 證券代號:{self._securities_code}'

    def _construct(self) -> list:

        url = "https://www.tdcc.com.tw/smWeb/QryStockAjax.do"
        form_data = {
            'scaDates': self._date,
            'scaDate': self._date,
            'tockNo': self._securities_code,
            'radioStockNo': self._securities_code,
            'clkStockNo': self._securities_code,
            'SqlMethod': 'StockNo',
            'REQ_OPR': 'SELECT',
            'StockName': '',
            'clkStockName': ''
        }
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

        html = post(url, params=form_data, headers=header)
        pattern = r'<td align="center">(.*)</td>\s+<td align="right">(.*)</td>\s+<td align="right">(.*)</td>\s+<td align="right">(.*)</td>\s+'
        list_table = findall(pattern, html.text)

        return list_table


def deviation_from_stock(stock_1, stock_2) -> list:

    first_part_table = [(
        i[0],
        f"{int(i[1].replace(',',''))-int(j[1].replace(',','')):,} ({i[1]}->{j[1]})",
        f"{int(i[2].replace(',',''))-int(j[2].replace(',','')):,} ({i[2]}->{j[2]})",
        f"{round(float(i[3])-float(j[3]),2)}  ({i[3]}->{j[3]})"
    ) for i, j in zip(stock_1[0:15], stock_2[0:15])
    ]

    length_of_stock_1, length_of_stock_2 = len(stock_1), len(stock_2)
    if length_of_stock_1 == 17 and length_of_stock_2 != 17:
        second_part_table = [(
            '差異數調整',
            '0',
            f"{stock_1[15][2]} ({stock_1[15][2]}->0)",
            f"{stock_1[15][3]}  ({stock_1[15][3]}->0.00)"
        )]
    elif length_of_stock_1 != 17 and length_of_stock_2 == 17:
        second_part_table = [(
            '差異數調整',
            '0',
            f"-{stock_2[15][2]} (0->{stock_2[15][2]})",
            f"{stock_2[15][3]}  (0.00->{stock_2[15][3]})"
        )]
    elif length_of_stock_2 == 17 and length_of_stock_2 == 17:
        second_part_table = [(
            '差異數調整',
            '0',
            f"{int(stock_1[15][2].replace(',',''))-int(stock_2[15][2].replace(',','')):,} ({stock_1[15][2]}->{stock_2[15][2]})",
            f"{round(float(stock_1[15][3])-float(stock_2[15][3]),2)}  ({stock_1[15][3]}->{stock_2[15][3]})"
        )]
    else:
        second_part_table = []

    last_part_table = [(
        f"{stock_1[-1][0]}",
        f"{int(stock_1[-1][1].replace(',',''))-int(stock_2[-1][1].replace(',','')):,} ({stock_1[-1][1]}->{stock_2[-1][1]})",
        f"{int(stock_1[-1][2].replace(',',''))-int(stock_2[-1][2].replace(',','')):,} ({stock_1[-1][2]}->{stock_2[-1][2]})",
        f"{round(float(stock_1[-1][3])-float(stock_2[-1][3]),2)}  ({stock_1[-1][3]}->{stock_2[-1][3]})"
    )]
    return first_part_table+second_part_table+last_part_table


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None) -> None:
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.func_load_Date()
        self.comboBox.activated[str].connect(self.func_change_start)
        self.comboBox_2.activated[str].connect(self.func_change_end)

        regular_pattern = QRegExp('[\w]+')
        line_Vaildator = QRegExpValidator(self)
        line_Vaildator.setRegExp(regular_pattern)
        self.lineEdit.setValidator(line_Vaildator)

        self.lineEdit_2.setAlignment(Qt.AlignCenter)
        self.lineEdit_2.setFont(
            QFont("Times", 14, QFont.Bold, QFont.StyleItalic))
        self.line2_palette = QPalette()
        self.line2_palette.setColor(QPalette.Text, Qt.red)

        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        QShortcut(QKeySequence("Enter"), self, self.button)

    def button(self) -> None:

        try:
            Stock_number = self.lineEdit.text()
            thread_1 = ThreadWithReturnValue(target=stock, args=(
                self.val_end_date, Stock_number))
            thread_2 = ThreadWithReturnValue(target=stock, args=(
                self.val_start_date, Stock_number))
            thread_1.start()
            thread_2.start()
            end_date_stock_statistics = thread_1.join()
            start_date_stock_statistics = thread_2.join()

            if not end_date_stock_statistics or not start_date_stock_statistics:
                raise ValueError('請重按一次')
            final = deviation_from_stock(
                end_date_stock_statistics, start_date_stock_statistics)

            self.tableWidget.setColumnCount(4)
            self.tableWidget.setRowCount(len(final))
            horizontalHeader = ["持股/單位數分級", "人數", "股數/單位數", "佔集保庫存數比例 (%)"]
            self.tableWidget.setHorizontalHeaderLabels(horizontalHeader)
            self.lineEdit_2.setText(
                f'證券代號: {Stock_number}{" "*4}起始日期: {self.val_start_date}{" "*4}終止日期: {self.val_end_date}')

            count = 0
            for i in final:
                self.tableWidget.setItem(count, 0, QTableWidgetItem(i[0]))
                self.tableWidget.setItem(count, 1, QTableWidgetItem(i[1]))
                self.tableWidget.setItem(count, 2, QTableWidgetItem(i[2]))
                self.tableWidget.setItem(count, 3, QTableWidgetItem(i[3]))
                count += 1

            self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tableWidget.horizontalHeader().setSectionResizeMode(2,
                                                                     QHeaderView.ResizeToContents)

        except ValueError as e:
            self.lineEdit_2.setPalette(self.line2_palette)
            self.lineEdit_2.setText(str(e))

    # Web scrapting. Fetching the Date. Padding to the Drop-down menu
    def func_load_Date(self) -> None:

        url = "https://www.tdcc.com.tw/smWeb/QryStockAjax.do"
        params = {
            'REQ_OPR': 'qrySelScaDates'
        }
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        date = post(url, params=params, headers=header)
        if date.status_code == codes.ok:
            date_li = findall(r'\d+', date.text)
            self.comboBox.addItems(date_li)
            self.comboBox_2.addItems(date_li)
            self.val_start_date = self.val_end_date = date_li[0]
        else:
            self.lineEdit_2.setText('Loading Date Fail')

    def func_change_start(self, text) -> None:
        self.val_start_date = text

    def func_change_end(self, text) -> None:
        self.val_end_date = text

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.button()


if __name__ == "__main__":

    try:
        app = QApplication(argv)
        window = MainWindow()
        window.show()
        exit(app.exec_())
    except:
        print_exc()
