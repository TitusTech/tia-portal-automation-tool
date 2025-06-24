# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'app.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QTextBrowser, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1025, 633)
        self.actionImport = QAction(MainWindow)
        self.actionImport.setObjectName(u"actionImport")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(13)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(8, 8, 8, 8)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.button_import = QPushButton(self.centralwidget)
        self.button_import.setObjectName(u"button_import")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_import.sizePolicy().hasHeightForWidth())
        self.button_import.setSizePolicy(sizePolicy)
        self.button_import.setMinimumSize(QSize(0, 0))
        font = QFont()
        font.setPointSize(12)
        self.button_import.setFont(font)
        self.button_import.setStyleSheet(u"padding: 8px 16px;")

        self.horizontalLayout_3.addWidget(self.button_import)

        self.label_json_filepath = QLabel(self.centralwidget)
        self.label_json_filepath.setObjectName(u"label_json_filepath")
        self.label_json_filepath.setFont(font)

        self.horizontalLayout_3.addWidget(self.label_json_filepath)


        self.horizontalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.button_select_library = QPushButton(self.centralwidget)
        self.button_select_library.setObjectName(u"button_select_library")
        sizePolicy.setHeightForWidth(self.button_select_library.sizePolicy().hasHeightForWidth())
        self.button_select_library.setSizePolicy(sizePolicy)
        self.button_select_library.setMinimumSize(QSize(0, 0))
        self.button_select_library.setFont(font)
        self.button_select_library.setStyleSheet(u"padding: 8px 16px;")

        self.horizontalLayout_4.addWidget(self.button_select_library)

        self.label_library_path = QLabel(self.centralwidget)
        self.label_library_path.setObjectName(u"label_library_path")
        self.label_library_path.setFont(font)

        self.horizontalLayout_4.addWidget(self.label_library_path)


        self.horizontalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)
        self.label_3.setFont(font)

        self.horizontalLayout_2.addWidget(self.label_3)

        self.combobox_dll_versions = QComboBox(self.centralwidget)
        self.combobox_dll_versions.setObjectName(u"combobox_dll_versions")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.combobox_dll_versions.sizePolicy().hasHeightForWidth())
        self.combobox_dll_versions.setSizePolicy(sizePolicy2)
        self.combobox_dll_versions.setFont(font)

        self.horizontalLayout_2.addWidget(self.combobox_dll_versions)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.horizontalLayout.addLayout(self.horizontalLayout_2)

        self.checkBox_enable_ui = QCheckBox(self.centralwidget)
        self.checkBox_enable_ui.setObjectName(u"checkBox_enable_ui")
        self.checkBox_enable_ui.setFont(font)
        self.checkBox_enable_ui.setChecked(True)

        self.horizontalLayout.addWidget(self.checkBox_enable_ui)

        self.checkbox_allow_overwrite = QCheckBox(self.centralwidget)
        self.checkbox_allow_overwrite.setObjectName(u"checkbox_allow_overwrite")
        self.checkbox_allow_overwrite.setFont(font)
        self.checkbox_allow_overwrite.setChecked(True)

        self.horizontalLayout.addWidget(self.checkbox_allow_overwrite)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.textbrowser_logs = QTextBrowser(self.centralwidget)
        self.textbrowser_logs.setObjectName(u"textbrowser_logs")
        self.textbrowser_logs.setAutoFillBackground(False)

        self.verticalLayout.addWidget(self.textbrowser_logs)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.button_copy_logs = QPushButton(self.centralwidget)
        self.button_copy_logs.setObjectName(u"button_copy_logs")
        self.button_copy_logs.setFont(font)
        self.button_copy_logs.setStyleSheet(u"padding: 8px 16px;")

        self.horizontalLayout_5.addWidget(self.button_copy_logs)

        self.button_execute_portal = QPushButton(self.centralwidget)
        self.button_execute_portal.setObjectName(u"button_execute_portal")
        self.button_execute_portal.setFont(font)
        self.button_execute_portal.setStyleSheet(u"padding: 8px 16px;")

        self.horizontalLayout_5.addWidget(self.button_execute_portal)


        self.verticalLayout.addLayout(self.horizontalLayout_5)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1025, 33))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionImport)
        self.menuFile.addSeparator()
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"TIA Portal Automation Tool by Titus Global Tech", None))
        self.actionImport.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.button_import.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.label_json_filepath.setText(QCoreApplication.translate("MainWindow", u"Empty", None))
        self.button_select_library.setText(QCoreApplication.translate("MainWindow", u"Select Library", None))
        self.label_library_path.setText(QCoreApplication.translate("MainWindow", u"None", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"TIA Version:", None))
        self.checkBox_enable_ui.setText(QCoreApplication.translate("MainWindow", u"Enable UI", None))
        self.checkbox_allow_overwrite.setText(QCoreApplication.translate("MainWindow", u"Overwrite", None))
        self.textbrowser_logs.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Welcome to TIA Portal Automation Tool by Titus Global Tech", None))
        self.button_copy_logs.setText(QCoreApplication.translate("MainWindow", u"Copy Logs", None))
        self.button_execute_portal.setText(QCoreApplication.translate("MainWindow", u"Create Project", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi

