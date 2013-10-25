# setup.py
from distutils.core import setup

try:
    import py2exe
    setup( 
        windows = [ 
            { 
                "script": "deffnet.py", 
                "icon_resources": [(1, "deffnet.ico")] 
            } 
        ], 
    ) 
except ImportError:
    try:
        import py2app
        setup(app=["deffnet.py"], options=dict(py2app=dict(plist='Info.plist', iconfile='icons/deffnet.icns')))
    except ImportError:
        pass
