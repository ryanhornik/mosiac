#!/usr/bin/env python
import sys
from PIL import Image
from mosaic import mean_color
import os


def get_color(file):
    image = Image.open(file)
    color = mean_color(image)
    image.close()
    return color


def calculate_color_if_neccessary(file):
    if '#' in file:
        already_checked = file.split('#')[-1][:-4]
        try:
            color = (int(already_checked[:2], 16),
                     int(already_checked[2:4], 16),
                     int(already_checked[4:6], 16))
            return None
        except ValueError:
            color = get_color(file)
    else:
        color = get_color(file)
    return color


def rename_to_average_colors(dir_path):
    images = filter(lambda f: os.path.isfile(f), ["{}/{}".format(dir_path, f) for f in os.listdir(dir_path)])
    for file in images:
        try:
            color = calculate_color_if_neccessary(file)
            if not color:
                continue

            new_name = "{dir_path}/{orig}#{:02X}{:02X}{:02X}{ext}".format(*color,
                                                                          orig=file.split('/')[-1][:-4],
                                                                          ext=file[-4:],
                                                                          dir_path=dir_path)
            os.rename(file, new_name)
        except OSError:
            print("{} failed to be read completely, deleting".format(file))
            os.remove(file)
        except Exception as e:
            print("Unknown Error occurred \n{}".format(e))


if __name__ == "__main__":
    rename_to_average_colors(sys.argv[1])
