"""

main windows combining pages

"""


from PyQt5 import QtCore, QtGui, QtWidgets
from pyqt5_ui.ui_windows import login


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = login.Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())