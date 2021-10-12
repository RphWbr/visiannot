from PIL import Image
from argparse import ArgumentParser
from os.path import splitext

parser = ArgumentParser()

parser.add_argument(
    "img_path", type=str, help="path to the image file to convert"
)

parser.add_argument(
    "--icon_path", "-o", type=str,
    help="path to the output icon file, default same location and name as the input image",
    default=None
)

args = parser.parse_known_args()
img_path = args[0].img_path
icon_path = args[0].icon_path

if icon_path is None:
    name = splitext(img_path)[0]
    icon_path = "%s.ico" % name

img = Image.open(img_path)
img.save(icon_path, format='ICO', sizes=[(256, 256)])
