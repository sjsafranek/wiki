import os
import zipfile
from io import BytesIO

def zipdir(source_dir):
    inMemoryFile = BytesIO()
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(inMemoryFile, 'w') as zipHandler:
        for root, dirs, files in os.walk(source_dir):
                # add directory (needed for empty dirs)
                zipHandler.write(root, os.path.relpath(root, relroot))
                for file in files:
                    filename = os.path.join(root, file)
                    if os.path.isfile(filename): # regular files only
                        arcname = os.path.join(os.path.relpath(root, relroot), file)
                        zipHandler.write(filename, arcname)
    inMemoryFile.seek(0)
    return inMemoryFile
