def classFactory(iface):
    from .layer_shifter import layerShifter
    return layerShifter(iface)
