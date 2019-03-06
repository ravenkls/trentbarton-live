from PyQt5 import QtWidgets, QtCore, QtGui
from gui import TrentBartonSystemTray
import trentbarton
import sys


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    bus_stop = trentbarton.BusStop('Chain Lane', 262)
    system_tray = TrentBartonSystemTray(bus_stop)

    sys.exit(app.exec_())


