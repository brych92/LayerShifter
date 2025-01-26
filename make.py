import os
import shutil
import zipfile


def zipdir(path, ziph):
    # ziph is zipfile handle
    print(path)
    for root, dirs, files in os.walk(path):
        # exclude subfolders .git __pycache__ and sources
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'sources']] 
        for file in files:
            if file != '.gitignore' and file != 'make.py':
                file_path = os.path.join(root, file)
                ziph.write(file_path, os.path.relpath(file_path, path))

if __name__ == '__main__':
    cwd = os.getcwd()
    desktop_path = os.path.join(os.path.expanduser('~'), 'OneDrive', 'Desktop')
    print(f"Desktop path: {desktop_path}")
    if not os.path.exists(desktop_path):
        print(f"Desktop path does not exist")
    zip_file_path = os.path.join(desktop_path, 'layer_shifter.zip')
    zipf = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
    zipdir(cwd, zipf)
    
    zipf.close()

    print(f'Created {zip_file_path}')

