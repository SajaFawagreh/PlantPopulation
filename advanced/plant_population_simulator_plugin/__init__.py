from .plugin import PPSPlugin

def classFactory(iface):
    return PPSPlugin(iface)
