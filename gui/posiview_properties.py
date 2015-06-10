'''
Created on 30.01.2015

@author: jrenken
'''

import os
from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSlot, QModelIndex, pyqtSignal
from PyQt4.QtGui import QIcon, QStringListModel, QStandardItem, QColor,\
    QFileDialog, QStandardItemModel, QAbstractButton, QDialogButtonBox
from qgis.core import QgsPoint
from qgis.gui import QgsOptionsDialogBase
from hgext.histedit import applychanges



FORM_CLASS, BASE_CLASS = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '..', 'ui', 'posiview_properties_base.ui'), True)


class PosiviewProperties(QgsOptionsDialogBase, FORM_CLASS):
    '''
    GUI class classdocs for the Configuration dialog
    '''
    applyChanges = pyqtSignal()
  
    def __init__(self, project, parent = None):
        '''
        Setup dialog widgets with the project properties
        '''
        super(PosiviewProperties, self).__init__("PosiViewProperties", parent)
        self.setupUi(self)
        self.initOptionsBase(False)
        self.restoreOptionsBaseUi()
        self.project = project
        self.projectProperties = project.properties()
        self.mToolButtonLoad.setDefaultAction(self.actionLoadConfiguration)
        self.mToolButtonSave.setDefaultAction(self.actionSaveConfiguration)
        self.mobileModel = QStringListModel()
           
        self.mobileListModel = QStringListModel()
#         mobileList = self.project.movingItems.keys()
        self.mobileListModel.setStringList(self.projectProperties['Mobiles'].keys())
        self.mMobileListView.setModel(self.mobileListModel)
        self.mMobileListView.clicked.connect(self.editMobile)
        self.mobileProviderModel = QStandardItemModel()
        self.mobileProviderModel.setHorizontalHeaderLabels(('Provider', 'Filter'))
#         setHorHorizontalHeaderItem(0, QStandardItem('Provider'))
#         self.mobileProviderModel.setHorizontalHeaderItem(, QStandardItem('Provider'))
        self.mMobileProviderTableView.setModel(self.mobileProviderModel)
          
              
          
        self.providerListModel = QStringListModel()
        self.providerListModel.setStringList(self.projectProperties['Provider'].keys())
        self.mProviderListView.setModel(self.providerListModel)
        self.mProviderListView.clicked.connect(self.editProvider)
        self.providerPropertiesModel = QStandardItemModel()
        self.mProviderPropertiesTableView.setModel(self.providerPropertiesModel)
  
        self.comboBoxProviders.setModel(self.providerListModel)
        self.actionSaveConfiguration.triggered.connect(self.onActionSaveConfigurationTriggered)
        self.actionLoadConfiguration.triggered.connect(self.onActionLoadConfigurationTriggered)
      
#         self.toolButtonAddMobile.clicked.connect(self.addMobile)
#         self.toolButtonRemoveMobile.clicked.connect(self.removeMobile)
        
    @pyqtSlot(QAbstractButton, name = 'on_buttonBox_clicked')
    def onButtonBoxClicked(self, button):
        role = self.buttonBox.buttonRole(button)
        if role == QDialogButtonBox.ApplyRole or role == QDialogButtonBox.AcceptRole:
            self.applyChanges.emit()
        
        
    @pyqtSlot()
    def onActionSaveConfigurationTriggered(self):
        ''' Save the current configuration
        '''
        fn = QFileDialog.getSaveFileName(None, 'Save PosiView configuration', '', 'Configuration (*.ini, *.conf')
        self.project.store(fn)
  
    @pyqtSlot()
    def onActionLoadConfigurationTriggered(self):
        ''' Load configuration from file
        '''
        fn = QFileDialog.getOpenFileName(None, 'Save PosiView configuration', '', 'Configuration (*.ini, *.conf')
      
    @pyqtSlot(QModelIndex)
    def editMobile(self, index):
        ''' Populate the widgets with the selected mobiles properties
        '''
        props = self.projectProperties['Mobiles'][self.mobileListModel.data(index, Qt.DisplayRole)]
        self.lineEditMobileName.setText(props.get('Name'))
        self.comboBoxMobileType.setCurrentIndex(self.comboBoxMobileType.findText( props.setdefault('type', 'BOX').upper()))
        if props['type'] == 'SHAPE':
            self.lineEditMobileShape.setText(str(props['shape']))
            self.lineEditMobileShape.setEnabled(True)
        else:
            self.lineEditMobileShape.setEnabled(False)
            self.lineEditMobileShape.clear()
        self.doubleSpinBoxMobileLength.setValue(props.get('length', 20.0))
        self.doubleSpinBoxMobileWidth.setValue(props.get('width', 5.0))
        self.spinBoxZValue.setValue(props.get('zValue', 100))
        self.mColorButtonMobileColor.setColor(QColor(props.get('color', 'black')))
        self.mColorButtonMobileFillColor.setColor(QColor(props.get('fillColor', 'green')))
        self.spinBoxMobileTimeout.setValue(props.get('timeout', 3000) / 1000)
        self.spinBoxTrackLength.setValue(props.get('trackLength', 100))
        self.mColorButtonMobileTrackColor.setColor(QColor(props.get('trackColor', 'green')))
                 
        r = 0
        self.mobileProviderModel.removeRows(0, self.mobileProviderModel.rowCount())
        if props.has_key('provider'):
            for k, v in props['provider'].items():
                prov = QStandardItem(k)
                val = QStandardItem(str(v))
                self.mobileProviderModel.setItem(r, 0, prov)
                self.mobileProviderModel.setItem(r, 1, val)
                r += 1
      
    @pyqtSlot(str, name = 'on_comboBoxMobileType_indexChanged')
    def mobileTypeChanged(self, mType):
        if mType == 'SHAPE':
#             self.lineEditMobileShape.setText(str(props['shape']))
            self.lineEditMobileShape.setEnabled(True)
        else:
            self.lineEditMobileShape.setEnabled(False)
            self.lineEditMobileShape.clear()
            
        
        
    @pyqtSlot(name = 'on_toolButtonAddMobile_clicked')        
    def addMobile(self):
        if not self.lineEditMobileName.text() == '':
            props = dict()
            props['Name'] = self.lineEditMobileName.text()
            props['type'] = self.comboBoxMobileType.currentText()
            props['shape'] = (( 0.0, -0.5), (0.3, 0.5), (0.0, 0.2), (-0.5, 0.5))
            props['length'] = self.doubleSpinBoxMobileLength.value()   
            props['width'] = self.doubleSpinBoxMobileWidth.value()
            props['zValue'] = self.spinBoxZValue.value()
            props['color'] = self.mColorButtonMobileColor.color().name()
            props['fillColor'] = self.mColorButtonMobileFillColor.color().name()
            props['timeout'] = self.spinBoxMobileTimeout.value() * 1000
            props['trackLength'] = self.spinBoxTrackLength.value()
            props['trackColor'] = self.mColorButtonMobileTrackColor.color().name()
            provs = dict()
            for r in range(self.mobileProviderModel.rowCount()):
                try:
                    fil = int(self.mobileProviderModel.item(r, 1).data(Qt.DisplayRole))
                except:
                    fil = self.mobileProviderModel.item(r, 1).data(Qt.DisplayRole)
                provs[self.mobileProviderModel.item(r, 0).data(Qt.DisplayRole)] = fil;
            props['provider'] = provs    
            print "AddMobile ", props
            self.projectProperties['Mobiles'][props['Name']] = props
            self.mobileListModel.setStringList(self.projectProperties['Mobiles'].keys())
      
    @pyqtSlot(name = 'on_toolButtonRemoveMobile_clicked')        
    def removeMobile(self):
        idx = self.mMobileListView.currentIndex()
        if idx.isValid():
            self.projectProperties['Mobiles'].pop(self.mobileListModel.data(idx, Qt.DisplayRole))
            self.mobileListModel.setStringList(self.projectProperties['Mobiles'].keys())
  
    @pyqtSlot(name = 'on_toolButtonAddMobileProvider_clicked')
    def addMobileProvider(self):
        prov = self.comboBoxProviders.currentText()
        fil = None
        if self.lineEditProviderFilter.text() != '':
            fil = self.lineEditProviderFilter.text()
        items = self.mobileProviderModel.findItems(prov, Qt.MatchExactly, 0)
        if items:
            for item in items:
                self.mobileProviderModel.setItem(item.row(), 1, QStandardItem(fil))
        else:
            print prov, fil
            self.mobileProviderModel.appendRow([QStandardItem(prov), QStandardItem(fil)])
              
  
    @pyqtSlot(name = 'on_toolButtonRemoveMobileProvider_clicked')
    def removeMobileProvider(self):
        idx = self.mMobileProviderTableView.currentIndex()
        self.mobileProviderModel.removeRow(idx.row())
          
    @pyqtSlot(QModelIndex)
    def editProvider(self, index):        
        print "editProvider: ", self.providerListModel.data(index, Qt.DisplayRole)
        provider = self.project.dataProviders[self.providerListModel.data(index, Qt.DisplayRole)]
        r = 0
        self.providerPropertiesModel.clear()
        for k, v in provider.properties().items():
            par = QStandardItem(k)
            val = QStandardItem(str(v))
            self.providerPropertiesModel.setVerticalHeaderItem(r, par)
            self.providerPropertiesModel.setItem(r, 0, val)
            r += 1
          

# import os
#  
# FORM_CLASS, BASE_CLASS = uic.loadUiType(os.path.join(
#     os.path.dirname(__file__), '..', 'ui', 'posiview_properties_base.ui'), True)
#  
# print FORM_CLASS
# print BASE_CLASS
#  
# class PosiviewProperties(QgsOptionsDialogBase, FORM_CLASS):
#     '''
#     classdocs
#     '''
#  
#  
#     def __init__(self, parent = None):
#         '''
#         Constructor
#         '''
#         super(PosiviewProperties, self).__init__("PosiView", parent)
#         self.setupUi(self)
#         self.initOptionsBase(False)
#         self.restoreOptionsBaseUi()