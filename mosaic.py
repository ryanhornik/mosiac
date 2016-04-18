from PIL import Image


def weighted_average(channel):
    return sum(i * w for i, w in enumerate(channel)) / sum(channel),


def mean_color(filename):
    i = Image.open(filename)
    h = i.histogram()

    r = h[:256]
    g = h[256:256 * 2]
    b = h[256 * 2:256 * 3]

    return weighted_average(r), weighted_average(g), weighted_average(b)

