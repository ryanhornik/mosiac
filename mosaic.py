#!/usr/bin/env python

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


def stitch_image_from_array(arr, size):
    stitched = Image.new(mode="RGB", size=size)
    width, height = stitched.size

    col = 0
    row = 0
    for j in range(0, height, 144):
        for i in range(0, width, 256):
            stitched.paste(arr[row][col], (i, j))
            col = (col + 1) % 10
        row = (row + 1) % 10

    return stitched


def main(filename, output, width=256, height=144):
    image = Image.open(filename)

    averaged_images = get_mosaic_array(image, width, height)
    stitch_image_from_array(averaged_images, size=image.size).save(output)


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2])

