#!/usr/bin/env python
from functools import reduce

from PIL import Image


def weighted_average(channel):
    return sum(i * w for i, w in enumerate(channel)) // sum(channel)


def mean_color(image):
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


def get_mosaic_array(image, width, height):
    averaged_images = [[]]

    img_width, img_height = image.size
    column_count = img_width // width
    row_count = img_height // height

    row, col = 0, 0
    for i in subimages(image, width, height):
        averaged_images[row].append(Image.new(mode="RGB", size=(width, height), color=mean_color(i)))
        col += 1
        if col % column_count == 0:
            row += 1
            if row < row_count:
                averaged_images.append([])

    return averaged_images


def stitch_image_from_array(arr, full_size, sub_image_size):
    stitched = Image.new(mode="RGB", size=full_size)

    full_width, full_height = stitched.size
    sub_image_width, sub_image_height = sub_image_size

    column_count = full_width // sub_image_width
    row_count = full_height // sub_image_height

    row, col = 0, 0
    for j in range(0, full_height, sub_image_height):
        for i in range(0, full_width, sub_image_width):
            stitched.paste(arr[row][col], (i, j))
            col = (col + 1) % column_count
        row = (row + 1) % row_count

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


def main(filename, output):
    image = Image.open(filename)
    img_width, img_height = image.size

    width = get_user_factor_selection(img_width, "width")
    height = get_user_factor_selection(img_height, "height")

    averaged_images = get_mosaic_array(image, width, height)
    stitch_image_from_array(averaged_images, full_size=image.size, sub_image_size=(width, height)).save(output)


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2])

