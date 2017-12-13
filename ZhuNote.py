# -*- coding: utf-8 -*-

"""
GUI for writing and browsing notes.
"""

__version__ = '0.2.0'

from PyQt4 import QtGui, QtCore
from PyQt4.QtWebKit import QWebView
from datetime import datetime
import pickle
import os
import argparse
from pathlib import Path

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-p", "--path", type=str, help='path to notes')
  args = parser.parse_args()
  path = args.path

  app = QtGui.QApplication([])
  note = ZhuNote(path=path)
  QtGui.QApplication.instance().exec_()

class ZhuNote(QtGui.QWidget):
  html_hi = '<html> <body> <p> HTML Viewer </p> </body> </html>'
  html_no = '<html> <body> <p> No HTML </p> </body> </html>'

  def __init__(self, path=None):
    QtGui.QMainWindow.__init__(self)
    self.setPath(path)
    print('Initializing GUI...')
    self.initUi()
    self.setFont()
    print('Loading database...')
    self.loadMaster()

  def setPath(self, path):
    if path is None :
      self.path = os.getcwd()
    else :
      self.path = path
    print('Working directory is', self.path)

  def initUi(self):
    x, y, w, h = 20, 40, 1000, 1000

    self.find = ZhuNoteFind(self) # self as parent
    self.tree = ZhuNoteTree()
    self.form = ZhuNoteForm(self.path)
    self.wbrs = QWebView()

    splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    splitter1.addWidget(self.form)
    splitter1.addWidget(self.wbrs)
    splitter1.setSizes([w/2, w/2])

    splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
    splitter.addWidget(self.tree)
    splitter.addWidget(splitter1)
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 2)

    vbox = QtGui.QVBoxLayout()
    vbox.addWidget(self.find)
    vbox.addWidget(splitter)
    self.setLayout(vbox)

    self.wbrs.setHtml(self.html_hi)

    self.tree.sigViewItem.connect(self.form.viewDict)
    self.tree.sigViewItem.connect(self.viewHtml)
    self.find.sigClear.connect(self.clear)
    self.find.sigString.connect(self.search)
    self.find.sigUpdateMaster.connect(self.updateMaster)
    self.find.sigFont.connect(self.setFont)

    self.setWindowTitle('Main - ZhuNote')
    #self.setGeometry(x, y, w, h)
    #self.move(x, y)
    self.resize(w, h)
    self.show()
    #self.tree.show()
    #self.form.show()

    styleName = 'Cleanlooks' # QtGui.QStyleFactory.keys()
    # ['Windows', 'Motif', 'CDE', 'Plastique', 'GTK+', 'Cleanlooks']
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create(
      styleName))

    self.find.txtSearch.setFocus() # not work yet

    self.actExit = QtGui.QAction('Exit', self)
    self.actExit.setShortcut('Ctrl+Q')
    self.actExit.triggered.connect(self.closeAllWindows)    
    self.addAction(self.actExit)

  def viewHtml(self, dictNote):
    htmlfn = dictNote['HTML']
    fn = os.path.join(self.path, htmlfn)
    if Path(fn).is_file() :
      url = QtCore.QUrl.fromLocalFile(fn)
      self.wbrs.load(url)
    else :
      #self.wbrs.setHtml('') # blank page
      self.wbrs.setHtml(self.html_no)

  def setFont(self, font=None):
    if font is None :
      font = QtGui.QFont() # default font
      font.setFamily('Courier New')
      font.setPointSize(11)
    self.find.txtSearch.setFont(font)
    self.tree.setFont(font)
    self.form.setFont(font)

  def closeAllWindows(self):
    app = QtGui.QApplication.instance()
    app.closeAllWindows()

  def loadMaster(self):
    fn = 'notemaster.pickle'
    self.fn_master = os.path.join(self.path, fn)

    try :
      with open(self.fn_master, 'rb') as f :
        self.dod = pickle.load(f)
    except FileNotFoundError :
      raise ValueError("Not found:", self.fn_master)

  def clear(self):
    self.find.txtSearch.clear()
    self.tree.clear()
    self.form.clear()
    self.wbrs.setHtml(self.html_hi)

  def search(self, string):
    self.tree.clear() # clear tree before a new search
    self.tree.lod = [] # used in tree class
    # break string to words by space
    stringLC = string.lower()
    words = stringLC.split()
    for key in self.dod :
      dictNote = self.dod[key]
      keyword = dictNote['Keyword']
      title = dictNote['Title']
      sstring = title + ' ' + keyword # string to be searched
      sstring = sstring.lower()
      if any(word in sstring for word in words): # weak search
      #if all(word in kw for word in words): # strong search
        self.tree.addItem(dictNote)
    self.tree.sortItems(0, QtCore.Qt.AscendingOrder)

  def updateMaster(self):
    """
    i self.path : string, path
    o file : write pickle file (list of dictionaries)
    In path, each pkl file contains one dictionary.
    This method merges all the dictionaries to a list for search.
    """
    print('Number of entries old =', len(self.dod))
    mt_master = os.path.getmtime(self.fn_master)

    for fn in os.listdir(self.path) :
      if fn.endswith(".pkl") :
        ffn = os.path.join(self.path, fn)
        mt_entry = os.path.getmtime(ffn)
        if mt_entry >= mt_master :
          with open(ffn, 'rb') as f :
            dictNote = pickle.load(f)
          title = dictNote['Title']
          if title in self.dod :
            print("Modify existing entry:", ffn)
          else :
            print("Add new entry:", ffn)
          self.dod[title] = dictNote

    with open(self.fn_master, 'wb') as f :
      pickle.dump(self.dod, f, -1)
    print('Merged file is', self.fn_master)
    print('Number of entries new =', len(self.dod))

class ZhuNoteFind(QtGui.QWidget):
  sigString = QtCore.pyqtSignal(str)
  sigClear = QtCore.pyqtSignal()
  sigUpdateMaster = QtCore.pyqtSignal()
  sigFont = QtCore.pyqtSignal(object)

  def __init__(self, parent=None):
    QtGui.QWidget.__init__(self, parent)

    lblSearch = QtGui.QLabel('ZhuNote')
    self.txtSearch = QtGui.QLineEdit(self)
    self.txtSearch.returnPressed.connect(self.send2search)
    btnHelp = QtGui.QPushButton('Help')
    btnHelp.clicked.connect(self.showHelp)    
    btnFont = QtGui.QPushButton('Font')
    btnFont.clicked.connect(self.fontPicker)
    btnClear = QtGui.QPushButton('Clear')
    btnClear.clicked.connect(self.send2clear)
    btnMaster = QtGui.QPushButton('Master')
    btnMaster.clicked.connect(self.sigUpdateMaster.emit)
    btnSearch = QtGui.QPushButton('Search')
    btnSearch.clicked.connect(self.send2search)    

    hbox = QtGui.QHBoxLayout()
    hbox.addWidget(btnHelp)
    hbox.addWidget(btnFont)
    hbox.addWidget(btnClear)
    hbox.addWidget(btnMaster)
    hbox.addWidget(btnSearch)

    vbox = QtGui.QVBoxLayout()
    vbox.addWidget(lblSearch)
    vbox.addWidget(self.txtSearch)
    vbox.addLayout(hbox)
    self.setLayout(vbox)

  def fontPicker(self):
    font, valid = QtGui.QFontDialog.getFont()
    if valid:
      self.sigFont.emit(font)

  def send2search(self):
    string = self.txtSearch.text()
    self.sigString.emit(string)

  def send2clear(self):
    self.sigClear.emit()

  def showHelp(self):
    strMan = """
    To open a single note from file:
    Put the note.pkl file in Filename, Ctrl+O.

    To update the master to include newly added entries:
    Click the Master button.

    To browse all entries:
    Type comma in search box, hit Enter.

    To write a note:
    Type in Title and below entries. In Body, Ctrl+S. Filename and Time will be auto-generated.
    Recommend list all entries before save, to check if file already exist and avoid overwrite.

    To close all windows:
    Focus at Main window, Ctrl+Q.
    """
    #msg = QtGui.QMessageBox() # cannot resize
    msg = ZhuMessageBox()
    msg.setText("This is a message box")
    msg.setInformativeText("This is additional information")
    msg.setWindowTitle("Help - ZhuNote")
    msg.setDetailedText(strMan)
    msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
    msg.exec_()

class ZhuMessageBox(QtGui.QMessageBox):
  """Extend QMessageBox to allow resize """
  def __init__(self):
    QtGui.QMessageBox.__init__(self)
    self.setSizeGripEnabled(True)

  def event(self, e):
    result = QtGui.QMessageBox.event(self, e)

    self.setMinimumHeight(0)
    self.setMaximumHeight(16777215)
    self.setMinimumWidth(0)
    self.setMaximumWidth(16777215)
    self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

    textEdit = self.findChild(QtGui.QTextEdit)
    if textEdit != None :
      textEdit.setMinimumHeight(0)
      textEdit.setMaximumHeight(16777215)
      textEdit.setMinimumWidth(0)
      textEdit.setMaximumWidth(16777215)
      textEdit.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

    return result

class ZhuNoteTree(QtGui.QTreeWidget):
  sigViewItem = QtCore.pyqtSignal(object)
  def __init__(self):
    QtGui.QWidget.__init__(self)
    self.setColumnCount(2)
    self.setHeaderLabels(("Title", "Keyword"))
    #self.setGeometry(0, 0, 800, 300)
    self.setColumnWidth(0, 400)
    self.setWindowTitle('Tree - ZhuNote')
    #self.show()
    self.currentItemChanged.connect(self.send2view)
    self.lod = []
    self.font = QtGui.QFont()
  def send2view(self):
    item = self.currentItem()
    if item is not None :
      title = item.text(0)
      result = [note for note in self.lod if note['Title'] == title]
      self.sigViewItem.emit(result[0]) # send one dictionary
  def addItem(self, dictNote):
    item = QtGui.QTreeWidgetItem(self)
    item.setText(0, dictNote['Title'])
    item.setText(1, dictNote['Keyword'])
    item.setFont(0, self.font)
    item.setFont(1, self.font)
    self.lod.append(dictNote)
  def setFont(self, font):
    self.font = font # for future use
    # set the current tree items
    iterator = QtGui.QTreeWidgetItemIterator(self)
    while iterator.value() :
      item = iterator.value()
      item.setFont(0, self.font)
      item.setFont(1, self.font)
      iterator += 1

class ZhuNoteForm(QtGui.QWidget):
  def __init__(self, path=None):
    QtGui.QWidget.__init__(self)
    self.initUI(path)

  def initUI(self, path):
    pathLabel = QtGui.QLabel('Path')
    filenameLabel = QtGui.QLabel('Filename')
    timeLabel = QtGui.QLabel('Time')
    titleLabel = QtGui.QLabel('Title')
    keywordLabel = QtGui.QLabel('Keyword')
    figureLabel = QtGui.QLabel('Figure')
    htmlLabel = QtGui.QLabel('HTML')
    bodyLabel = QtGui.QLabel('Body')

    self.pathEdit = QtGui.QLineEdit(path)
    self.pathEdit.setReadOnly(True)
    self.filenameEdit = QtGui.QLineEdit()
    self.timeEdit = QtGui.QLineEdit()
    self.titleEdit = QtGui.QLineEdit()
    self.keywordEdit = QtGui.QLineEdit()
    self.figureEdit = QtGui.QLineEdit()
    self.htmlEdit = QtGui.QLineEdit()
    self.bodyEdit = QtGui.QTextEdit()

    # If more than one keyword, delimit with comma.
    # Same for figure and html filenames.

    #btnSave = QtGui.QPushButton('Save')
    #btnSave.setToolTip('Save script to file')
    #btnSave.clicked.connect(self.saveFile)    
    # Replace save button with keyboard shortcut
    # Save move hand from keyboard to mouse.

    grid = QtGui.QGridLayout()
    grid.setSpacing(5)
    
    row = 0
    grid.addWidget(pathLabel, row, 0)
    grid.addWidget(self.pathEdit, row, 1)
    row += 1
    grid.addWidget(filenameLabel, row, 0)
    grid.addWidget(self.filenameEdit, row, 1)
    row += 1
    grid.addWidget(figureLabel, row, 0)
    grid.addWidget(self.figureEdit, row, 1)
    row += 1
    grid.addWidget(htmlLabel, row, 0)
    grid.addWidget(self.htmlEdit, row, 1)
    row += 1
    grid.addWidget(timeLabel, row, 0)
    grid.addWidget(self.timeEdit, row, 1)
    row += 1
    grid.addWidget(titleLabel, row, 0)
    grid.addWidget(self.titleEdit, row, 1)
    row += 1
    grid.addWidget(keywordLabel, row, 0)
    grid.addWidget(self.keywordEdit, row, 1)
    row += 1
    grid.addWidget(bodyLabel, row, 0)
    grid.addWidget(self.bodyEdit, row, 1, 6, 1)
    #grid.addWidget(btnSave, 11, 1)

    self.actOpen = QtGui.QAction('Open', self)
    self.actOpen.setShortcut('Ctrl+O')
    self.actOpen.triggered.connect(self.openFile)
    self.filenameEdit.addAction(self.actOpen)

    self.actSave = QtGui.QAction('Save', self)
    self.actSave.setShortcut('Ctrl+S')
    self.actSave.triggered.connect(self.saveFile)
    self.bodyEdit.addAction(self.actSave)

    self.setLayout(grid)
    #self.setGeometry(300, 300, 600, 400)
    self.setWindowTitle('Form - ZhuNote')
    #self.show()

  def setFont(self, font):
    #font = self.bodyEdit.font() # current font
    #font = QtGui.QFont() # default font
    self.pathEdit.setFont(font)
    self.filenameEdit.setFont(font)
    self.timeEdit.setFont(font)
    self.titleEdit.setFont(font)
    self.keywordEdit.setFont(font)
    self.figureEdit.setFont(font)
    self.htmlEdit.setFont(font)
    self.bodyEdit.setFont(font)

  def clear(self):
    self.filenameEdit.clear()
    self.timeEdit.clear()
    self.titleEdit.clear()
    self.keywordEdit.clear()
    self.figureEdit.clear()
    self.htmlEdit.clear()
    self.bodyEdit.clear()

  def viewDict(self, dictNote):
    self.filenameEdit.setText(dictNote['Filename'])
    self.timeEdit.setText(dictNote['Time'])
    self.titleEdit.setText(dictNote['Title'])
    self.keywordEdit.setText(dictNote['Keyword'])
    self.figureEdit.setText(dictNote['Figure'])
    self.htmlEdit.setText(dictNote['HTML'])
    self.bodyEdit.setText(dictNote['Body'])

  def openFile(self):
    path = self.pathEdit.text()
    fn = self.filenameEdit.text()
    ffn = os.path.join(path, fn)
    with open(ffn, 'rb') as f :
      dictNote = pickle.load(f)
    self.viewDict(dictNote)

  def saveFile(self):

    #fn = timeStr + '.txt'
    # Use title as filename to overwrite existing note file.
    base = self.titleEdit.text().replace(' ', '_')
    txtfn = base + '.txt'
    pklfn = base + '.pkl'

    path = self.pathEdit.text()
    timeStr = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    self.filenameEdit.setText(pklfn)
    self.timeEdit.setText(timeStr)

    textSum = ''
    text = 'Filename: ' + txtfn + '\n'
    textSum += text
    text = 'Time: ' + timeStr + '\n'
    textSum += text
    text = 'Title: ' + self.titleEdit.text() + '\n'
    textSum += text
    text = 'Keyword: ' + self.keywordEdit.text() + '\n'
    textSum += text
    text = 'Figure: ' + self.figureEdit.text() + '\n'
    textSum += text
    text = 'HTML: ' + self.htmlEdit.text() + '\n'
    textSum += text
    text = 'Body: ' + self.bodyEdit.toPlainText() + '\n'
    textSum += text

    dictNote = {}
    dictNote['Filename'] = pklfn
    dictNote['Time'] = timeStr
    dictNote['Title'] = self.titleEdit.text()
    dictNote['Keyword'] = self.keywordEdit.text()
    dictNote['Figure'] = self.figureEdit.text()
    dictNote['HTML'] = self.htmlEdit.text()
    dictNote['Body'] = self.bodyEdit.toPlainText()

    txtffn = os.path.join(path, txtfn)
    pklffn = os.path.join(path, pklfn)

    # Check if file exist
    myfile = Path(txtffn)
    if myfile.is_file() : # file exists
      choice = QtGui.QMessageBox.question(self, 'Warning',
      "File exists. Do you want overwrite?", QtGui.QMessageBox.Yes |
      QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
      if choice == QtGui.QMessageBox.Yes :
        self.writeFile(textSum, txtffn, dictNote, pklffn)
      else :
        print("Change title and re-save.")
        return 1
    else :
      self.writeFile(textSum, txtffn, dictNote, pklffn)
      return 0

  @staticmethod
  def writeFile(textSum, txtfn, dictNote, pklfn):
    """ input are full filename (with absolute path) """
    with open(txtfn, 'w', encoding='utf-8') as f :
      f.write(textSum)
    with open(pklfn, 'wb') as f :
      pickle.dump(dictNote, f, -1)

if __name__ == '__main__':
  main()
