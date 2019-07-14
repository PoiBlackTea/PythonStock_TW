# -*- coding: utf-8 -*-
from GUI import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow,QApplication,QTableWidget,QTableWidgetItem
import thread_return as thread
import requests
import re 
import sys
import timeit
import os

def arithmetic(li1, li2):
    ar0 = []
    try:
        if len(li1) == 17 and len(li2) != 17:
            length = 17
            li1[15][1] = '0'
            li1[15][0] = '差異數調整'
            li2.insert(15,['差異數調整', '0', '0', '0.00'])
        elif len(li2)==17 and len(li1)!=17:          
            length = 17
            li2[15][1] = '0'
            li2[15][0] = '差異數調整'
            li1.insert(15,['差異數調整', '0', '0', '0.00'])
        else:
            length = len(li1)
        
        for i in range(length):
            ar1 = []
            for j in range(4):
                if j == 0:
                    tmp = li1[i][j]
                    ar1.append(tmp)
                elif j == 1 or j == 2:
                    tmp = str(int(li1[i][j]) - int(li2[i][j]))
                    if len(tmp) < 4 or ('-' in tmp and len(tmp) == 4):
                        tmp = tmp
                    else:
                        tmp = tmp[:-3] + ',' + tmp[-3:]
                    tmp = tmp + "(" + li2[i][j] + "->" + li1[i][j] + ")"
                    ar1.append(tmp)
                else:
                    tmp = str(round(float(li1[i][j]) - float(li2[i][j]), 2)) + "(" + li2[i][j] + "->" + li1[i][j] + ")"
                    ar1.append(tmp)
            ar0.append(ar1)
        
    except:
        self.lineEdit_4.setText("check  arithmetic func and run again")

    return ar0

# preprcessing
def map_split(string):
    result = ''.join(re.findall('>.+<', string)).replace('<', '').split('>')

    return [result[2], result[3].replace(',', ''), result[4].replace(',', ''), result[5]]
    
#  Webscraping
def Webscraping(date,ID):
    try:
        url = "https://www.tdcc.com.tw/smWeb/QryStockAjax.do"
        data = {'scaDates' : '', 'scaDate' : '', 'SqlMethod' : 'StockNo', 'tockNo' : '', 'radioStockNo' : '', 'StockName' : '', 'REQ_OPR' : 'SELECT', 'clkStockNo' : '', 'clkStockName' : '' }
        data['scaDates'] = data['scaDate'] = date
        data['tockNo'] = data['radioStockNo'] = data['clkStockNo'] = ID
        html = requests.post(url, data)
        pattern = '<td align=\"center\">.+</td>\s+<td align=\"center\">.+</td>\s+<td align=\"right\">.+</td>\s+<td align=\"right\">.+</td>\s+<td align=\"right\">.+</td>'

        """ 
        html form:
           <tr >
              <td align="center">1</td>
              <td align="center">1-999</td>
              <td align="right">109,373</td>
              <td align="right">29,070,387</td>
              <td align="right">0.94</td>
            </tr>
        """
        # regular regression
        reg = re.findall(pattern, html.text)
        if reg == []:
            html = requests.post(url, data)
            reg = re.findall(pattern, html.text)
        
        #get clear data
        stock_li = list(map(map_split, reg))

    except:
        self.lineEdit_4.setText('Html run error')
        raise
	
    return stock_li

# GUI
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        
    def back(self):
        token1 =  self.lineEdit.text()     # 股票號碼
        token2 =  self.lineEdit_2.text()   # 起始日期
        token3 =  self.lineEdit_3.text()   # 截止日期

        """ 
        call thread_return.py 
        thread_1 and thread_2  catch two information ,respectively.
        """
        thread_1 = thread.ThreadWithReturnValue(target = Webscraping, args = (token3, token1))
        thread_2 = thread.ThreadWithReturnValue(target = Webscraping, args = (token2, token1))
        thread_1.start()
        thread_2.start()
        stock_li1 = thread_1.join()
        stock_li2 = thread_2.join()

        # get reslut
        final = arithmetic(stock_li1, stock_li2)
            
        # plane
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(len(final))
        horizontalHeader = ["持股/單位數分級", "人數", "股數/單位數", "佔集保庫存數比例 (%)"]
        self.tableWidget.setHorizontalHeaderLabels(horizontalHeader)    
        self.lineEdit_4.setText('ID:' + token1 + ' From:' + token2 + ' To:' + token3)
        count = 0
            
        # push result to plane
        for i in final:
            self.tableWidget.setItem(count, 0, QTableWidgetItem(i[0]))
            self.tableWidget.setItem(count, 1, QTableWidgetItem(i[1]))
            self.tableWidget.setItem(count, 2, QTableWidgetItem(i[2]))
            self.tableWidget.setItem(count, 3, QTableWidgetItem(i[3]))
            count += 1

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    os.system("pause")