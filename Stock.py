# -*- coding: utf-8 -*-
import re
import sys
from traceback import print_exc

import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget,
                             QTableWidgetItem)

import thread_return as thread
from Stock_GUI import Ui_MainWindow


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
        html = requests.post(url, params=data)
        if html.status_code == requests.codes.ok:
            pattern = r'<td align=\"center\">.+</td>\s+<td align=\"right\">.+</td>\s+<td align=\"right\">.+</td>\s+<td align=\"right\">.+</td>'
            list_table = re.findall(pattern, html.text)
        else:
            raise ValueError

        stock_li = list(map(lambda x: re.findall(r'>(.*)<', x), list_table))
    except ValueError:
        print('html.status_code error')
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

    def button(self):

        try:
            Stock_number = self.lineEdit.text()
            if not Stock_number:
                raise ValueError("股票號碼不可為空")
            elif not Stock_number.isdigit():
                raise ValueError("股票號碼必須是數字")
        except ValueError as e:
            self.lineEdit_2.setText(str(e))
        else:
            thread_1 = thread.ThreadWithReturnValue(
                target=Web_scraping, args=(self.val_end_date, Stock_number))
            thread_2 = thread.ThreadWithReturnValue(
                target=Web_scraping, args=(self.val_start_date, Stock_number))
            thread_1.start()
            thread_2.start()
            stock_li1 = thread_1.join()
            stock_li2 = thread_2.join()

            final = Calculate_stock(stock_li1, stock_li2)

            self.tableWidget.setColumnCount(4)
            self.tableWidget.setRowCount(len(final))
            horizontalHeader = ["持股/單位數分級", "人數", "股數/單位數", "佔集保庫存數比例 (%)"]
            self.tableWidget.setHorizontalHeaderLabels(horizontalHeader)
            self.lineEdit_2.setText(
                f'證券代號: {Stock_number} 起始日期:{self.val_start_date} 終止日期:{self.val_end_date}')

            count = 0
            for i in final:
                self.tableWidget.setItem(count, 0, QTableWidgetItem(i[0]))
                self.tableWidget.setItem(count, 1, QTableWidgetItem(i[1]))
                self.tableWidget.setItem(count, 2, QTableWidgetItem(i[2]))
                self.tableWidget.setItem(count, 3, QTableWidgetItem(i[3]))
                count += 1

            self.tableWidget.resizeColumnsToContents()
            self.tableWidget.resizeRowsToContents()

    def func_load_Date(self):

        headers = '''POST /smWeb/QryStockAjax.do HTTP/1.1\nHost: www.tdcc.com.tw\nConnection: keep-alive\nAccept: application/json, text/javascript, */*; q=0.01\nSec-Fetch-Dest: empty\nX-Requested-With: XMLHttpRequest\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36\nContent-Type: application/x-www-form-urlencoded;charset=UTF-8\nOrigin: https://www.tdcc.com.tw\nSec-Fetch-Site: same-origin\nSec-Fetch-Mode: cors\nReferer: https://www.tdcc.com.tw/smWeb/QryStock.jsp\nAccept-Encoding: gzip, deflate, br\nAccept-Language: zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,ja;q=0.5\n'''
        headers = str2obj(headers, '\n', ': ')
        params = {'REQ_OPR': 'qrySelScaDates'}
        url = "https://www.tdcc.com.tw/smWeb/QryStockAjax.do"
        date = requests.post(url, params=params, headers=headers)
        if date.status_code == requests.codes.ok:
            date_li = re.findall(r'\d+', date.text)
            self.comboBox.addItems(date_li)
            self.comboBox_2.addItems(date_li)
            self.val_start_date = self.val_end_date = date_li[0]
        else:
            self.lineEdit_2.setText('Loading Date Fail')

    def func_change_start(self, text):
        self.val_start_date = text

    def func_change_end(self, text):
        self.val_end_date = text


if __name__ == "__main__":

    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except:
        print_exc
