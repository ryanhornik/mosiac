#!/usr/bin/env python
import threading
from functools import reduce
from math import sqrt

from PIL import Image
import os


sample_images = []
without_replacement = True


def load_images(dir_path):
    images = filter(lambda f: os.path.isfile(f), ["{}/{}".format(dir_path, f) for f in os.listdir(dir_path)])
    for file in images:
        color_hex = file.split('#')[-1][:-4]
        color = (int(color_hex[:2], 16), int(color_hex[2:4], 16), int(color_hex[4:], 16))
        sample_images.append((file, color))


def color_distance(first, second):
    return sqrt(pow(first[0] - second[0], 2) +
                pow(first[1] - second[1], 2) +
                pow(first[2] - second[2], 2))


def weighted_average(channel):
    return sum(i * w for i, w in enumerate(channel)) // sum(channel)


def mean_color(image):
    if image.mode != "RGB":
        image = image.convert(mode="RGB")

    h = image.histogram()

    r = h[:256]
    g = h[256:256 * 2]
    b = h[256 * 2:256 * 3]

    return weighted_average(r), weighted_average(g), weighted_average(b)


def subimages(image, width, height):
    img_width, img_height = image.size
    if img_width % width != 0 or img_height % height != 0:
        print("Warning, Image will not evenly divide")

    for j in range(0, img_height, height):
        for i in range(0, img_width, width):
            box = (i, j, i + width, j + height)
            sub_img = image.crop(box)
            sub_img.load()
            yield sub_img


def get_average_color_matrix(image, sub_image_size):
    width, height = sub_image_size
    average_color_matrix = []

    img_width, img_height = image.size
    column_count = img_width // width

    row, col = -1, 0
    for i in subimages(image, width, height):
        if col % column_count == 0:
            row += 1
            average_color_matrix.append([])
        average_color_matrix[row].append(mean_color(i))
        col += 1

    return average_color_matrix


def thumbnail_no_preserve_aspect(image, size, resample=3):
    old_aspect = image.size[0]/image.size[1]
    new_aspect = size[0]/size[1]

    new_image = image

    if new_aspect < old_aspect:
        aspect_ratio_ratio = new_aspect / old_aspect
        new_width = aspect_ratio_ratio * image.size[0]
        per_side = (image.size[0] - round(new_width)) // 2
        new_image = new_image.crop(box=(per_side, 0, new_image.size[0] - per_side, new_image.size[1]))
    elif new_aspect > old_aspect:
        aspect_ratio_ratio = old_aspect / new_aspect
        new_height = aspect_ratio_ratio * image.size[1]
        per_side = (image.size[1] - round(new_height)) // 2
        new_image = new_image.crop(box=(0, per_side, new_image.size[0], new_image.size[1] - per_side))

    new_image.thumbnail(size, resample)
    return new_image


images_to_paste = []
threads = []


def other_thread(full_width, sub_image_width, sub_image_height, average_color_matrix, row, j):
    col = 0
    for i in range(0, full_width, sub_image_width):
        closest_img_idx = get_closest_image_index(average_color_matrix[row][col])
        closest_img_obj = Image.open(sample_images[closest_img_idx][0])

        closest_img_scaled = thumbnail_no_preserve_aspect(closest_img_obj, size=(sub_image_width, sub_image_height))
        images_to_paste.append((closest_img_scaled, (i, j)))


def stitch_image_from_array(arr, full_size, sub_image_size, average_color_matrix):
    stitched = Image.new(mode="RGB", size=full_size)

    full_width, full_height = stitched.size
    sub_image_width, sub_image_height = sub_image_size

    row_count = full_height // sub_image_height

    row, col = 0, 0
    for j in range(0, full_height, sub_image_height):
        thread = threading.Thread(target=other_thread,
                                  args=(full_width, sub_image_width, sub_image_height, average_color_matrix, row, j))
        thread.start()
        threads.append(thread)
        row = (row + 1) % row_count

    print("Attempting to Join")
    for t in threads:
        t.join()

    for i in images_to_paste:
        stitched.paste(i[0], i[1])

    return stitched


def factors(n):
    return set(reduce(list.__add__, ([i, n // i] for i in range(1, int(n ** 0.5) + 1) if n % i == 0)))


def get_user_factor_selection(n, name):
    n_factors = sorted(factors(n))
    i = 1
    for i, value in enumerate(n_factors):
        print("({0: >2}) {1: <12}".format(i, value), end="")
        if (i+1) % 5 == 0:
            print()
    return n_factors[int(input("{}Select a factor for sub-image {}\n".format("" if (i+1) % 5 == 0 else "\n", name)))]


def main(sample_directory, filename, output, scale=3):
    image = Image.open(filename)
    if scale != 1:
        image = image.resize((image.size[0]*scale, image.size[1]*scale))
    img_width, img_height = image.size

    load_images(sample_directory)

    width = get_user_factor_selection(img_width, "width")
    height = get_user_factor_selection(img_height, "height")

    mosaic(image, (width, height)).save(output)


def get_closest_image_index(color):
    smallest_value = 450  # pure white is 441.67 away from pure black
    smallest_index = None
    for i, (_, other_color) in enumerate(sample_images):
        value = color_distance(color, other_color)
        if value < smallest_value:
            smallest_value = value
            smallest_index = i

    if without_replacement:
        del sample_images[smallest_index]

    return smallest_index


def mosaic(image, sub_image_size, reblend=0.5):
    average_colors = get_average_color_matrix(image, sub_image_size)
    stitched = stitch_image_from_array(average_colors, image.size, sub_image_size, average_colors)
    return Image.blend(stitched, image, reblend)


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2], sys.argv[3])

