try:
    from PyQt5.QtWidgets import QFileDialog, QFileIconProvider, QInputDialog, QLineEdit, QWidget
    from PyQt5.QtCore import QCoreApplication, qInfo, QSize, QStandardPaths
    from PyQt5 import QtGui, QtWidgets, QtCore
    from PyQt5.QtWidgets import QFileIconProvider
    qtHorizontal = QtCore.Qt.Horizontal
    qtCancel = QtWidgets.QDialogButtonBox.Cancel
    qtOkay = QtWidgets.QDialogButtonBox.Ok
    qtStaysOnTop = QtCore.Qt.WindowStaysOnTopHint
    qtSizePolicy = QtWidgets.QSizePolicy
    qtItemView = QtWidgets.QAbstractItemView
    qtItemFlag = QtCore.Qt
    qtCheckState = QtCore.Qt
    qtMatchFlag = QtCore.Qt
except:
    from PyQt6.QtWidgets import QFileDialog, QFileIconProvider, QInputDialog, QLineEdit, QWidget
    from PyQt6.QtCore import QCoreApplication, qInfo, QSize, QStandardPaths
    from PyQt6 import QtGui, QtWidgets, QtCore
    from PyQt6.QtWidgets import QFileIconProvider
    qtHorizontal = QtCore.Qt.Orientation.Horizontal
    qtCancel = QtWidgets.QDialogButtonBox.StandardButton.Cancel
    qtOkay = QtWidgets.QDialogButtonBox.StandardButton.Ok
    qtStaysOnTop = QtCore.Qt.WindowType.WindowStaysOnTopHint
    qtSizePolicy = QtWidgets.QSizePolicy.Policy
    qtItemView = QtWidgets.QAbstractItemView.SelectionMode
    qtItemFlag = QtCore.Qt.ItemFlag
    qtCheckState = QtCore.Qt.CheckState
    qtMatchFlag = QtCore.Qt.MatchFlag
from ..openmwplayer_plugin import OpenMWPlayerPlugin
from ...shared.shared_icons import SharedIcons
import mobase, re, os
from pathlib import Path

class OpenMWPlayerManageTool(OpenMWPlayerPlugin, mobase.IPluginTool):
    
    def __init__(self):
        super().__init__()

    def init(self, organiser=mobase.IOrganizer):
        res = super().init(organiser)
        self.dialog = self.getDialog()
        return res

    def __tr(self, trstr):
        return QCoreApplication.translate(self.pluginName, trstr)

    def master(self):
        return self.pluginName

    def settings(self):
        return []

    def icon(self):
        return self.icons.openMwIcon()

    def name(self):
        return self.baseName() + " Manage Tool"
        
    def description(self):
        return self.__tr("Manage OpenMW Player settings.")

    def display(self):
        self.dialog.show()
        self.bindPlugins()

    _settingRows = []

    def bindSettings(self):
        profile = self.organiser.profile().name()
        settingsPath = str(self.openMWPlayer.paths.openMwBaseCfgPath(profile))
        settingColl = self.openMWPlayer.getCfgSettings(settingsPath)
        self._settingRows = sorted(settingColl)
        rows = len(self._settingRows)
        self.settingsTable.clear()
        self.settingsTable.setColumnCount(1)
        self.settingsTable.setRowCount(rows)
        self.settingsTable.horizontalHeader().hide()
        self.settingsTable.horizontalHeader().setStretchLastSection(True)
        self.settingsTable.verticalHeader().setDefaultSectionSize(23)
        count = 0
        for setting in self._settingRows:
            headingItem = QtWidgets.QTableWidgetItem(setting)
            self.settingsTable.setVerticalHeaderItem(count, headingItem)
            tableItem = QtWidgets.QTableWidgetItem(settingColl[setting])
            tableItem.setFlags(tableItem.flags() | QtCore.Qt.ItemIsEditable)
            self.settingsTable.setItem(count-1, 1, tableItem)
            count = count + 1
        self.settingsTable.itemChanged.connect(self.getTableSettings)

    def bindBsas(self):
        profile = self.organiser.profile().name()
        self.bsaSelect.clear()

        # Create a bsa config if it doesn't exist.
        bsaCustom = self.openMWPlayer.paths.openMwBsaSettingsPath(profile)
        bsaFiles = []
        if not bsaCustom.exists():
            with bsaCustom.open("x") as custNew:
                custNew.write("\n")

        # Load the bsa settings from config.
        with bsaCustom.open("r") as custGrnd:
            for line in custGrnd:
                line = line.replace("\n", "")
                if len(line) > 0:
                    bsaFiles.append(line)

        # Bind the bsa list to select bsa files.
        bsas = []
        game = self.organiser.managedGame()
        rootBsa = filter(lambda x: x.lower().endswith(".bsa"), os.listdir(game.dataDirectory().absolutePath()))
        for bsa in rootBsa:
            bsas.append(bsa)
        mods = self.organiser.modList().allModsByProfilePriority(self.organiser.profile())
        for mod in mods:
            if (self.organiser.modList().state(mod) & 0x2) != 0:
                modBsa = filter(lambda x: x.lower().endswith(".bsa") , os.listdir(self.organiser.modList().getMod(mod).absolutePath()))
                for bsa in modBsa:
                    bsas.append(bsa)

        self.bsaSelect.clear()
        for name in bsas:
            item = QtWidgets.QListWidgetItem()
            item.setText(name)
            item.setFlags(qtItemFlag.ItemIsUserCheckable|qtItemFlag.ItemIsEnabled)
            item.setCheckState(qtCheckState.Unchecked)
            self.bsaSelect.addItem(item)

        # Check any currently enabled bsa files.
        for name in bsaFiles:
            for itm in self.bsaSelect.findItems(name, qtMatchFlag.MatchExactly):
                itm.setCheckState(qtCheckState.Checked)

    def getTableSettings(self):
        row = 0
        newValues = {}
        for setting in self._settingRows:
            item = self.settingsTable.item(row, 0)
            newValues[setting] = item.text()
            qInfo("Setting: " + setting + " Value: " + item.text())
            row = row + 1
        self.openMWPlayer.updateImportedSettings(newValues)

    def bindPlugins(self):
        profile = self.organiser.profile().name()

        # Get the current settings path and display it.
        cfgPath = str(self.openMWPlayer.paths.openMWCfgPath())
        self.addText.setText(cfgPath)

        # Bind the dummy esp setting checkbox.
        self.dummyCheck.setChecked(self.openMWPlayer.settings.dummyesp())

        # Bind the manage settings checkbox.
        self.manageCheck.setChecked(self.openMWPlayer.settings.managesettings())
        if self.openMWPlayer.settings.managesettings():
            self.tabSelect.setTabEnabled(2, True)
        else:
            self.tabSelect.setTabEnabled(2, False)

        # If there's no settings and there is a valid config, import the settings.
        settingsPath = str(self.openMWPlayer.paths.openMwBaseCfgPath(profile))
        if not Path(settingsPath).exists() and Path(cfgPath).exists():
            self.openMWPlayer.importOpenMWCfg(cfgPath)

        # Create a groundcover config if it doesn't exist.
        groundCoverCustom = self.openMWPlayer.paths.openMwGrassSettingsPath(profile)
        groundCoverFiles = []
        if not groundCoverCustom.exists():
            with groundCoverCustom.open("x") as custNew:
                custNew.write("\n")

        # Load the groundcover settings from config.
        with groundCoverCustom.open("r") as custGrnd:
            for line in custGrnd:
                line = line.replace("\n", "")
                if len(line) > 0:
                    groundCoverFiles.append(line)
                    
        # Bind the plugin list to select groundcover. 
        self.groundcoverSelect.clear()
        for name in self.organiser.pluginList().pluginNames():
            item = QtWidgets.QListWidgetItem()
            item.setText(name)
            item.setFlags(qtItemFlag.ItemIsUserCheckable|qtItemFlag.ItemIsEnabled)
            item.setCheckState(qtCheckState.Unchecked)
            self.groundcoverSelect.addItem(item)
            
        # Check any currently enabled groundcover.
        for name in groundCoverFiles:
            for itm in self.groundcoverSelect.findItems(name, qtMatchFlag.MatchExactly):
                itm.setCheckState(qtCheckState.Checked)

        # Bind setting table.
        self.bindSettings()

        # Bind bsas
        self.bindBsas()

    # TODO: Add a settings editor panel, where these settings can be configured.
    def refreshCfgSettings(self):
        cfgPath = str(self.openMWPlayer.paths.openMWCfgPath())
        if Path(cfgPath).exists():
            cfgSettings = self.openMWPlayer.importOpenMWCfg(cfgPath)
            self.bindSettings()
            self.bindBsas()

    def dummyEspCheck(self):
        self.organiser.setPluginSetting(self.baseName(), "dummyesp", self.dummyCheck.isChecked())
        if self.dummyCheck.isChecked():
            self.openMWPlayer.enableDummy()
        else:
            self.openMWPlayer.disableDummy()

    def manageSettingsCheck(self):
        self.organiser.setPluginSetting(self.baseName(), "managesettings", self.manageCheck.isChecked())
        if self.manageCheck.isChecked():
            self.tabSelect.setTabEnabled(2, True)
        else:
            self.tabSelect.setTabEnabled(2, False)

    def selectOpenMWCfg(self):
        manualPath = QFileDialog.getOpenFileName(self._parentWidget(), self.__tr("Locate OpenMW Config File"), ".", "OpenMW Config File (openmw.cfg)")[0]
        self.organiser.setPluginSetting(self.baseName(), "openmwcfgpath", str(manualPath))
        self.addText.setText(str(manualPath))

    def changePluginState(self):
        selected = []
        for x in range(self.groundcoverSelect.count()):
            p = self.groundcoverSelect.item(x)
            if p.checkState() == qtCheckState.Checked:
                selected.append(p.text())
        
        profile = self.organiser.profile().name()
        groundCoverCustom = self.openMWPlayer.paths.openMwGrassSettingsPath(profile)
        with groundCoverCustom.open("w") as custGrnd:
            for item in selected:
                custGrnd.write(item + "\n")

    def changeBsaState(self):
        selected = []
        for x in range(self.bsaSelect.count()):
            p = self.bsaSelect.item(x)
            if p.checkState() == qtCheckState.Checked:
                selected.append(p.text())
        
        profile = self.organiser.profile().name()
        bsaCustom = self.openMWPlayer.paths.openMwBsaSettingsPath(profile)
        with bsaCustom.open("w") as custGrnd:
            for item in selected:
                custGrnd.write(item + "\n")

    def getDialog(self):
        dialog = QtWidgets.QDialog()
        dialog.setObjectName("dialog")
        dialog.resize(475, 340)
        dialog.setWindowIcon(self.icons.openMwIcon())
        dialog.setWindowTitle("OpenMW Player")
        self.dialogLayout = QtWidgets.QVBoxLayout(dialog)
        self.dialogLayout.setContentsMargins(5, 5, 5, 5)
        self.dialogLayout.setSpacing(5)
        self.dialogLayout.setObjectName("dialogLayout")

        self.addWidget = QtWidgets.QWidget(dialog)
        self.addWidget.setObjectName("addWidget")
        self.addLayout = QtWidgets.QHBoxLayout(self.addWidget)
        self.addLayout.setContentsMargins(0, 0, 0, 0)
        self.addLayout.setSpacing(5)
        self.addLayout.setObjectName("addLayout")
        self.addText = QtWidgets.QLabel(self.addWidget)
        self.addText.setObjectName("addText")
        self.addButton = QtWidgets.QPushButton(self.addWidget)
        sizePolicy = QtWidgets.QSizePolicy(qtSizePolicy.Fixed, qtSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addButton.sizePolicy().hasHeightForWidth())
        self.addButton.setSizePolicy(sizePolicy)
        self.addButton.setIcon(self.icons.linkIcon())
        self.addButton.setObjectName("addButton")
        self.addButton.setText("OpenMW.cfg")
        self.addButton.clicked.connect(self.selectOpenMWCfg)

        self.importButton = QtWidgets.QPushButton(self.addWidget)
        sizePolicy = QtWidgets.QSizePolicy(qtSizePolicy.Fixed, qtSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.importButton.sizePolicy().hasHeightForWidth())
        self.importButton.setSizePolicy(sizePolicy)
        self.importButton.setIcon(self.icons.installIcon())
        self.importButton.setObjectName("importButton")
        self.importButton.setText("Import")
        self.importButton.clicked.connect(self.refreshCfgSettings)

        self.addLayout.addWidget(self.addButton)
        self.addLayout.addWidget(self.addText)
        self.addLayout.addWidget(self.importButton)
        self.dialogLayout.addWidget(self.addWidget)

        self.dummyWidget = QtWidgets.QWidget(dialog)
        self.dummyWidget.setObjectName("dummyWidget")
        self.dummyLayout = QtWidgets.QVBoxLayout(self.dummyWidget)
        self.dummyLayout.setContentsMargins(0, 0, 0, 0)
        self.dummyLayout.setSpacing(5)
        self.dummyLayout.setObjectName("dummyLayout")
        #self.dummyText = QtWidgets.QLabel(self.dummyWidget)
        #self.dummyText.setObjectName("dummyText")

        self.dummyCheck = QtWidgets.QCheckBox(self.dummyWidget)
        sizePolicy = QtWidgets.QSizePolicy(qtSizePolicy.Fixed, qtSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dummyCheck.sizePolicy().hasHeightForWidth())
        self.dummyCheck.setSizePolicy(sizePolicy)
        self.dummyCheck.setMinimumSize(QtCore.QSize(75, 0))
        self.dummyCheck.setObjectName("dummyCheck")
        self.dummyCheck.setText("Enable omwaddon and omwscripts support via esp files.")
        self.dummyCheck.clicked.connect(self.dummyEspCheck)
        self.dummyLayout.addWidget(self.dummyCheck)

        self.manageCheck = QtWidgets.QCheckBox(self.dummyWidget)
        sizePolicy = QtWidgets.QSizePolicy(qtSizePolicy.Fixed, qtSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.manageCheck.sizePolicy().hasHeightForWidth())
        self.manageCheck.setSizePolicy(sizePolicy)
        self.manageCheck.setMinimumSize(QtCore.QSize(75, 0))
        self.manageCheck.setObjectName("manageCheck")
        self.manageCheck.setText("Manage openmw.cfg settings through Mod Organizer.")
        self.manageCheck.clicked.connect(self.manageSettingsCheck)
        self.dummyLayout.addWidget(self.manageCheck)

        #self.dummyLayout.dummyWidget(self.dummyText)
        self.dialogLayout.addWidget(self.dummyWidget)

        #self.gcvWidget = QtWidgets.QWidget(dialog)
        #self.gcvWidget.setObjectName("gcvWidget")
        #self.gcvLayout = QtWidgets.QHBoxLayout(self.gcvWidget)
        #self.gcvLayout.setContentsMargins(0, 0, 0, 0)
        #self.gcvLayout.setSpacing(5)
        #self.gcvLayout.setObjectName("gcvLayout")
        #self.gcvText = QtWidgets.QLabel(self.gcvWidget)
        #self.gcvText.setText("Select Groundcover Plugins")
        #self.gcvText.setObjectName("gcvText")
        #self.gcvLayout.addWidget(self.gcvText)
        #self.dialogLayout.addWidget(self.gcvWidget)

        self.tabSelect = QtWidgets.QTabWidget(dialog)
        self.dialogLayout.addWidget(self.tabSelect)

        self.groundcoverSelect = QtWidgets.QListWidget(dialog)
        self.groundcoverSelect.setSelectionMode(qtItemView.MultiSelection)
        self.groundcoverSelect.setObjectName("groundcoverSelect")
        self.groundcoverSelect.itemChanged.connect(self.changePluginState)
        #self.dialogLayout.addWidget(self.groundcoverSelect)
        self.tabSelect.addTab(self.groundcoverSelect, "Groundcover")

        self.bsaSelect = QtWidgets.QListWidget(dialog)
        self.bsaSelect.setSelectionMode(qtItemView.MultiSelection)
        self.bsaSelect.setObjectName("bsaSelect")
        self.bsaSelect.itemChanged.connect(self.changeBsaState)
        #self.dialogLayout.addWidget(self.bsaSelect)
        self.tabSelect.addTab(self.bsaSelect, "Archives")

        self.settingsTable = QtWidgets.QTableWidget(dialog)
        self.settingsTable.setColumnCount(1)
        #self.dialogLayout.addWidget(self.settingsTable)
        self.tabSelect.addTab(self.settingsTable, "Settings")

        QtCore.QMetaObject.connectSlotsByName(dialog)

        return dialog