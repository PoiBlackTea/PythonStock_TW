# -*- coding: utf-8 -*-
from re import findall
from sys import argv, exit
from traceback import print_exc

from PyQt5.QtCore import QEvent, QRegExp, Qt
from PyQt5.QtGui import QFont, QPalette, QRegExpValidator
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QHeaderView,
                             QMainWindow, QTableWidget, QTableWidgetItem)
from requests import codes, post

from Stock_GUI import Ui_MainWindow
from thread_return import ThreadWithReturnValue


def str2obj(s, s1=';', s2='='):
    li = s.split(s1)
    res = {}
    for kv in li:
        li2 = kv.split(s2)
        if len(li2) > 1:
            res[li2[0]] = li2[1]
    return res


def Calculate_stock(li1, li2):

    ar0 = []
    if len(li1) == 17 and len(li2) != 17:
        li1[15][0:2] = ['差異數調整', '0']
        li2.insert(15, ['差異數調整', '0', '0', '0.00'])
    elif len(li2) == 17 and len(li1) != 17:
        li2[15][0:2] = ['差異數調整', '0']
        li1.insert(15, ['差異數調整', '0', '0', '0.00'])
    elif len(li2) == 17 and len(li1) == 17:
        li1[15][0:2] = ['差異數調整', '0']
        li2[15][0:2] = ['差異數調整', '0']
    table_length = len(li1)

    for i in range(table_length):
        ar1 = []
        for j in range(4):
            if j == 0:
                tmp = li1[i][j]
            elif j == 1 or j == 2:
                tmp = str(int(li1[i][j].replace(',', '')) -
                          int(li2[i][j].replace(',', '')))
                tmp = f'{int(tmp):,} ({li2[i][j]}->{li1[i][j]})'
            else:
                tmp = str(round(float(li1[i][j]) - float(li2[i][j]), 2))
                tmp = f'{float(tmp)} ({li2[i][j]}->{li1[i][j]})'
            ar1.append(tmp)
        ar0.append(ar1)

    return ar0


def Web_scraping(date, ID):
    try:
        url = "https://www.tdcc.com.tw/smWeb/QryStockAjax.do"
        data = {'scaDates': date, 'scaDate': date, 'SqlMethod': 'StockNo', 'tockNo': ID, 'radioStockNo': ID,
                'StockName': '', 'REQ_OPR': 'SELECT', 'clkStockNo': ID, 'clkStockName': ''}
        html = post(url, params=data)
        if html.status_code != codes['ok']:
            raise ValueError(f'{html.status_code}')
        else:
            pattern = r'<td align=\"center\">.+</td>\s+<td align=\"right\">.+</td>\s+<td align=\"right\">.+</td>\s+<td align=\"right\">.+</td>'
            list_table = findall(pattern, html.text)
            if not list_table:
                html = post(url, params=data)
                list_table = findall(pattern, html.text)
                if not list_table:
                    return []

        stock_li = list(map(lambda x: findall(r'>(.*)<', x), list_table))
    except ValueError as error_message:
        print(str(error_message))
        return []
    except:
        print_exc
    return stock_li


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.func_load_Date()
        self.comboBox.activated[str].connect(self.func_change_start)
        self.comboBox_2.activated[str].connect(self.func_change_end)

        regular_pattern = QRegExp('[A-Z0-9]+')
        line_Vaildator = QRegExpValidator(self)
        line_Vaildator.setRegExp(regular_pattern)
        self.lineEdit.setValidator(line_Vaildator)

        self.lineEdit_2.setAlignment(Qt.AlignCenter)
        self.lineEdit_2.setFont(
            QFont("Times", 14, QFont.Bold, QFont.StyleItalic))
        self.line2_palette = QPalette()
        self.line2_palette.setColor(QPalette.Text, Qt.red)

        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def button(self):

        try:
            Stock_number = self.lineEdit.text()
            thread_1 = ThreadWithReturnValue(target=Web_scraping, args=(
                self.val_end_date, Stock_number))
            thread_2 = ThreadWithReturnValue(target=Web_scraping, args=(
                self.val_start_date, Stock_number))
            thread_1.start()
            thread_2.start()
            stock_li1 = thread_1.join()
            stock_li2 = thread_2.join()

            if not stock_li1 or not stock_li2:
                raise ValueError('請重按一次')
            final = Calculate_stock(stock_li1, stock_li2)

            self.tableWidget.setColumnCount(4)
            self.tableWidget.setRowCount(len(final))
            horizontalHeader = ["持股/單位數分級", "人數", "股數/單位數", "佔集保庫存數比例 (%)"]
            self.tableWidget.setHorizontalHeaderLabels(horizontalHeader)
            self.lineEdit_2.setText(
                f'證券代號: {Stock_number}    起始日期: {self.val_start_date}    終止日期: {self.val_end_date}')

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

    def func_load_Date(self):

        headers = '''POST /smWeb/QryStockAjax.do HTTP/1.1\nHost: www.tdcc.com.tw\nConnection: keep-alive\nAccept: application/json, text/javascript, */*; q=0.01\nSec-Fetch-Dest: empty\nX-Requested-With: XMLHttpRequest\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36\nContent-Type: application/x-www-form-urlencoded;charset=UTF-8\nOrigin: https://www.tdcc.com.tw\nSec-Fetch-Site: same-origin\nSec-Fetch-Mode: cors\nReferer: https://www.tdcc.com.tw/smWeb/QryStock.jsp\nAccept-Encoding: gzip, deflate, br\nAccept-Language: zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,ja;q=0.5\n'''
        headers = str2obj(headers, '\n', ': ')
        params = {'REQ_OPR': 'qrySelScaDates'}
        url = "https://www.tdcc.com.tw/smWeb/QryStockAjax.do"
        date = post(url, params=params, headers=headers)
        if date.status_code == codes.ok:
            date_li = findall(r'\d+', date.text)
            self.comboBox.addItems(date_li)
            self.comboBox_2.addItems(date_li)
            self.val_start_date = self.val_end_date = date_li[0]
        else:
            self.lineEdit_2.setText('Loading Date Fail')

    def func_change_start(self, text):
        self.val_start_date = text

    def func_change_end(self, text):
        self.val_end_date = text

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.button()


if __name__ == "__main__":

    try:
        app = QApplication(argv)
        window = MainWindow()
        window.show()
        exit(app.exec_())
    except:
        print_exc
