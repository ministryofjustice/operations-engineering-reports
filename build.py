"""Downloads and extracts govuk-frontend files to static folders"""
from urllib.request import urlretrieve
from pathlib import Path
import shutil
import zipfile
import os

# pylint: disable-msg=C0103

print("start")
assets_js_path = Path("application/assets/js")
assets_css_path = Path("application/assets/css")
assets_image_path = Path("application/assets/images")

dirpath = Path("report_app/static")
css_path = dirpath / "stylesheets"
js_path = dirpath / "javascript"
image_path = dirpath / "images"
zip_file = "govuk_frontend.zip"
urlretrieve(
    (
        "https://github.com/alphagov/govuk-frontend/releases/download/"
        "v4.3.0/release-v4.3.0.zip"
    ),
    zip_file,
)
if dirpath.exists():
    shutil.rmtree(dirpath)
with zipfile.ZipFile(zip_file, "r") as zip_ref:
    zip_ref.extractall(dirpath)
assets_fonts_path = str(Path(dirpath) / "assets/fonts")
static_fonts_path = str(Path(dirpath) / "fonts")
shutil.move(assets_fonts_path, static_fonts_path)
assets_images_path = str(Path(dirpath) / "assets/images")
shutil.move(assets_images_path, image_path)
assets_path = str(dirpath / "assets")
shutil.rmtree(assets_path)

css_path.mkdir(parents=True, exist_ok=True)
for each_file in Path(dirpath).glob("*.css"):
    path = str(css_path / each_file.name)
    shutil.move(str(each_file), path)

# Rename asset to static in *.css files
for each_file in Path(css_path).glob("*.css"):
    print(each_file)
    with open(each_file, "r", encoding="utf-8") as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace("/assets", "/static")

    # Write the file out again
    with open(each_file, "w", encoding="utf-8") as file:
        file.write(filedata)

for each_file in Path(assets_css_path).glob("*.css"):
    shutil.copy(each_file, css_path / each_file.name)

js_path.mkdir(parents=True, exist_ok=True)
for each_file in Path(dirpath).glob("*.js"):
    path = str(js_path / each_file.name)
    shutil.move(str(each_file), path)

for each_file in Path(assets_js_path).glob("*.js"):
    shutil.copy(each_file, js_path / each_file.name)

for each_file in Path(assets_image_path).glob("*.png"):
    shutil.copy(each_file, image_path / each_file.name)

os.remove(zip_file)
print("Finished")
print("If version has changed update the versions in /report_app/templates/base.html")
