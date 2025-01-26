import os
from PyQt5.QtWidgets import (
    QToolBar, QAction, QPushButton, QGridLayout, QDialog, QWidget, 
    QVBoxLayout, QLineEdit, QFrame, QLabel, QMenu
    
)
from PyQt5.QtCore import Qt, QEvent, QCoreApplication, QTranslator
from PyQt5.QtGui import QIcon
import re
from qgis.core import QgsCoordinateReferenceSystem, QgsSettings, QgsProject

#from qgis.core import QgsVectorTileLayer, QgsProject, QgsMapLayer
#from qgis.gui import QgisInterface as interface

from typing import cast
from .ua_SPT import uaSPT



class layerShifter:
    def tr(self, message):
        return QCoreApplication.translate('LayerCrsShiter', message)

    def __init__(self, iface):
        self.iface = iface
        
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.folder_path=os.path.expanduser('~')
        self.locale = QgsSettings().value('locale/userLocale')[0:2]
        
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'layer_shifter_{}.qm'.format(self.locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        
        self.window = None
    
    def initGui(self):
        self.toolbar = uaSPT.getToolbar(self.iface)
        icon = QIcon(os.path.join(self.plugin_dir,"resources","icon.png"))
        self.main_button = QAction(icon, self.tr("Layer displacement..."))     
        self.main_button.triggered.connect(self.run)
        self.main_button.setEnabled(True)
        self.menu = self.iface.layerMenu()
        self.menu.addAction(self.main_button)
        if self.locale == 'uk':
            self.iface.addPluginToMenu("Плагіни UA SPT", self.main_button)
        #self.toolbar.addAction(self.main_button)

        self.add_to_layer_menu()

    def add_to_layer_menu(self):
        menu = cast(QMenu, self.iface.layerMenu())
        for item in menu.actions():
            if item.isSeparator():
                menu.insertAction(item, self.main_button)
                return
            

    def unload(self):
        if self.toolbar.children() == []:
            self.toolbar.deleteLater()
        
        if self.window is not None:
            self.window.close()
            self.window.deleteLater()

        if self.main_button:
            self.main_button.deleteLater()

    def run(self):
        self.window = Window(self.iface.mainWindow(), self)
        self.window.show()
        
class arrowPad(QWidget):
    def __init__(self, parent=None, plugin=None):
        super().__init__(parent)
        self.parent = parent
        self.plugin = plugin
        
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.button_layout = QGridLayout()
        #self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setFixedSize(180, 180)
        
        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setLayout(self.button_layout)
        self.mainLayout.addWidget(self.frame)

        self.stepField = QLineEdit('1')
        self.stepField.setPlaceholderText("-")
        self.stepField.setToolTip(self.tr("Displacement step in meters(approximate)"))
        self.stepField.setFixedSize(40, 40)
        self.stepField.setAlignment(Qt.AlignCenter)
        
        self.setEnabled(False)
    
        def on_scroll(event):            
            current_value = float(self.stepField.text())
            delta = event.angleDelta().y() / 120  # typical delta is 120 per notch
            if delta > 0:
                step = 0.01 if current_value < 0.1 else 0.1 if current_value < 1 else 1 if current_value < 10 else 10
            elif delta < 0:
                step = 0.01 if current_value <= 0.1 else 0.1 if current_value <= 1 else 1 if current_value <= 10 else 10
            
            new_value = max(0, current_value + delta*step)
            if new_value > 1000 or new_value < 0.01:
                return
            if new_value < 1:
                new_value = round(new_value, 2)
            else:
                new_value = int(new_value)
            
            self.stepField.setText(str(new_value))

        self.stepField.wheelEvent = on_scroll
        
        bUL = QPushButton("↖")
        bUL.setFixedSize(40, 40)
        bUL.clicked.connect(lambda: self.crs_shift('ul'))
        self.button_layout.addWidget(bUL, 0, 0)
        
        bU = QPushButton("↑")
        bU.setFixedSize(40, 40)
        bU.clicked.connect(lambda: self.crs_shift('u'))
        self.button_layout.addWidget(bU, 0, 1)

        bUR = QPushButton("↗")
        bUR.setFixedSize(40, 40)
        bUR.clicked.connect(lambda: self.crs_shift('ur'))
        self.button_layout.addWidget(bUR, 0, 2)

        bL = QPushButton("←")
        bL.setFixedSize(40, 40)
        bL.clicked.connect(lambda: self.crs_shift('l'))
        self.button_layout.addWidget(bL, 1, 0)
        
        self.button_layout.addWidget(self.stepField, 1, 1)

        bR = QPushButton("→")
        bR.setFixedSize(40, 40)
        bR.clicked.connect(lambda: self.crs_shift('r'))
        self.button_layout.addWidget(bR, 1, 2)
        
        bDL = QPushButton("↙")
        bDL.setFixedSize(40, 40)
        bDL.clicked.connect(lambda: self.crs_shift('dl'))
        self.button_layout.addWidget(bDL, 2, 0)
        
        bD = QPushButton("↓")
        bD.setFixedSize(40, 40)
        bD.clicked.connect(lambda: self.crs_shift('d'))
        self.button_layout.addWidget(bD, 2, 1)

        bDR = QPushButton("↘")
        bDR.setFixedSize(40, 40)
        bDR.clicked.connect(lambda: self.crs_shift('dr'))
        self.button_layout.addWidget(bDR, 2, 2)

    def crs_shift(self, direction:str, distance:float = 1.5):
        '''
        takes a direction and a distance and shifts the CRS
        takes crs proj string of active layer
        change shifting parameters
        apply it to current layer
        refresh layer
        '''
        layer = self.plugin.iface.activeLayer()
        if layer is None:
            self.parent.update()
            return
        

        crs = layer.crs()
        proj_val = crs.toProj()

        x_0 = re.search(r'x_0=(-?\d+(?:\.\d+)?)', proj_val)
        y_0 = re.search(r'y_0=(-?\d+(?:\.\d+)?)', proj_val)
        if x_0 is None or y_0 is None:
            self.parent.update()
            return
        
        x_0 = x_0.group(1)
        y_0 = y_0.group(1)

        distance = float(self.stepField.text())
        if not distance>0:
            distance = 1

        if 'l' in direction:
            proj_val = proj_val.replace(f'x_0={x_0}', f'x_0={float(x_0) + distance}')
        if 'r' in direction:
            proj_val = proj_val.replace(f'x_0={x_0}', f'x_0={float(x_0) - distance}')
        if 'u' in direction:
            proj_val = proj_val.replace(f'y_0={y_0}', f'y_0={float(y_0) - distance}')
        if 'd' in direction:
            proj_val = proj_val.replace(f'y_0={y_0}', f'y_0={float(y_0) + distance}')
            
        
        self.parent.initLayer(layer)
        layer.setCrs(crs.fromProj(proj_val))
        layer.triggerRepaint()
        self.plugin.iface.mapCanvas().refresh()
        self.parent.update()

class statusLabel(QLabel):
    def __init__(self, parent=None, plugin=None):
        super().__init__(parent = parent)
        self.plugin = plugin
        #self.mouseDoubleClickEvent(self.show_proj)
        self.updateStatus()

    def updateStatus(self):
        layer = self.plugin.iface.activeLayer()
        if layer is None:
            self.setText(self.tr("Layer is not selected"))
            return
        
        crs = layer.crs()
        current_proj = crs.toProj()
        x_0 = re.search(r'x_0=(-?\d+(?:\.\d+)?)', current_proj)
        y_0 = re.search(r'y_0=(-?\d+(?:\.\d+)?)', current_proj)
        if x_0 is None or y_0 is None:
            self.setText(self.tr("Layer CRS is not supported"))
            return

        x_0 = x_0.group(1)
        y_0 = y_0.group(1)
        self.setText(f"x_0={float(x_0):.2f}, y_0={float(y_0):.2f}")

class Window(QDialog):
    def __init__(self, parent, plugin):
        super().__init__(parent)
        self.setWindowIcon(QIcon(os.path.join(plugin.plugin_dir, "resources", "icon.png")))
        #self.parent = parent
        self.plugin = plugin
        self.setWindowTitle(self.tr("Displace CRS"))
        self.window_layout = QVBoxLayout()
        self.setLayout(self.window_layout)

        self.arrow_widget = arrowPad(self, self.plugin)

        self.current_proj = statusLabel(self, self.plugin)
        self.reset_btn = QPushButton("-")
        self.reset_btn.clicked.connect(self.resetCRS)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setEnabled(False)

        self.window_layout.addWidget(self.arrow_widget)
        self.window_layout.addWidget(self.reset_btn)
        self.window_layout.addWidget(separator)
        self.window_layout.addWidget(self.current_proj)
        self.update()
        self.layer_changed_con = self.plugin.iface.currentLayerChanged.connect(self.update)
        
        self.setFixedSize(self.sizeHint())

    def on_close(self):
        self.plugin.iface.currentLayerChanged.disconnect(self.layer_changed_con)
        
    def isInicialized(self, layer):
        """
        Checks if the layer has been already initialized
        args:
            layer: QgsMapLayer
        returns:
            bool
        """        
        if layer is None:
            return False        
        crs = layer.customProperty('original_crs', None)
        if crs:
            return True
        else:
            return False

    def isApplicable(self, layer):
        if layer is None:
            return False
        
        
        PROJ = layer.crs().toProj()
        x_0 = re.search(r'x_0=(-?\d+(?:\.\d+)?)', PROJ)
        y_0 = re.search(r'y_0=(-?\d+(?:\.\d+)?)', PROJ)
        if x_0 is None or y_0 is None:
            #print(f"Layer is not applicable")
            return False
        else:
            return True

    def initLayer(self, layer = None):        
        if layer is None:
            layer = self.plugin.iface.activeLayer()
        
        if not self.isApplicable(layer):
            return
        
        if self.isInicialized(layer):
            return
        
        PROJ = layer.crs().toProj()
        SRID = layer.crs().authid()

        if QgsCoordinateReferenceSystem(SRID).isValid():
            layer.setCustomProperty('original_crs', SRID)
            layer.setCrs(QgsCoordinateReferenceSystem.fromProj(PROJ))
            layer.triggerRepaint()
            self.update()
            return
            
        layer.setCustomProperty('original_crs', PROJ)
        self.update()

    def resetCRS(self):
        layer = self.plugin.iface.activeLayer()
        if not self.isInicialized(layer):
            return
        
        layer.setCrs(QgsCoordinateReferenceSystem(layer.customProperty('original_crs')))
        layer.removeCustomProperty('original_crs')
        layer.triggerRepaint()
        self.plugin.iface.mapCanvas().refresh()
        self.update()


    def enterEvent(self, event: QEvent):
        self.update()
        super().enterEvent(event)

    def update(self):
        layer = self.plugin.iface.activeLayer()
        if layer is None:
            self.reset_btn.setEnabled(False)
            self.reset_btn.setText("-")
            self.reset_btn.setToolTip(self.tr("Layer not selected"))
            self.arrow_widget.setEnabled(False)
            self.current_proj.updateStatus()
            return
        
        if not self.isApplicable(layer):
            self.reset_btn.setEnabled(False)
            self.reset_btn.setText("-")
            self.reset_btn.setToolTip(self.tr("Layer is not applicable\r\nPlease select layer with metric CRS"))
            self.arrow_widget.setEnabled(False)
            self.current_proj.updateStatus()
            return

        if not self.isInicialized(layer):
            self.reset_btn.setEnabled(True)
            self.reset_btn.setText(self.tr("Init layer!"))
            self.reset_btn.setToolTip(self.tr("Initialize layer\r\nSaving original CRS, to restore it later"))
            self.arrow_widget.setEnabled(False)
            self.reset_btn.clicked.disconnect()
            self.reset_btn.clicked.connect(lambda:self.initLayer())
        else:
            self.reset_btn.setText(self.tr("Reset CRS"))
            self.reset_btn.setToolTip(self.tr("Reset layer CRS to original!\r\nThis will set layer to its original position"))
            self.arrow_widget.setEnabled(True)
            self.reset_btn.clicked.disconnect()
            self.reset_btn.clicked.connect(self.resetCRS)
            if layer.customProperty('original_crs') == layer.crs().authid() or layer.customProperty('original_crs') == layer.crs().toProj():
                self.reset_btn.setEnabled(False)
            else:
                self.reset_btn.setEnabled(True)
        
        self.current_proj.updateStatus()
        
        

    