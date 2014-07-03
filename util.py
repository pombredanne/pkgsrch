import os

def getDir(dirName):
    """Returns the absolute path of a directory."""
    return os.path.join(os.path.dirname(__file__), dirName)
