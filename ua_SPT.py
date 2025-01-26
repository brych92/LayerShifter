from PyQt5.QtWidgets import QMenu, QToolBar


class uaSPT:
    """ 
    Збірка для уніфікування інтерфейсу плагінів від ініціативи
    "Відкриті інструменти просторового планування для України"


    """
    def tr(self, message):
        return self.iface.tr(message)

    def __init__(self, iface):
        self.iface = iface

    def getMenu(iface)->QMenu:
        '''
        Повертає меню ініціативи "Відкриті інструменти просторового планування для України"
        args:
            iface: QgsInterface
        return:
            ua_spt_menu - об'єкт QMenu з ідентифікатором "ua_spt_menu"
        '''
        menu = iface.pluginMenu()
        spt_menu = menu.findChild(QMenu, 'ua_spt_menu')
        
        if not spt_menu:
            spt_menu = menu.addMenu('Плагіни UA SPT')
            spt_menu.setObjectName('ua_spt_menu')
            spt_menu.setToolTip('Меню ініціативи "Відкриті інструменти просторового планування для України"')
        return spt_menu

    def getToolbar(iface)->QToolBar:
        '''
        Повертає панель ініціативи "Відкриті інструменти просторового планування для України"
        args:
            iface: QgsInterface
        return:
            ua_spt_toolbar - об'єкт QToolBar з ідентифікатором "ua_spt_panel"
        '''
        toolbar = iface.mainWindow().findChild(QToolBar, 'ua_spt_panel')
        if not toolbar:
            toolbar = iface.addToolBar("Панель UA SPT")
            toolbar.setObjectName('ua_spt_panel')
            toolbar.setToolTip('Панель ініціативи "Відкриті інструменти просторового планування для України"')
        
        return toolbar