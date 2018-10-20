from math import sin, asin, sqrt, pi


def in_tree_pixel(baf, img_width):
    # baf is the Basal Area factor
    # tree_width is the app measured tree pixel width

    theta = 2 * asin(sqrt(baf) / 100)  # radians
    min_tree_width = theta / (2*pi) * img_width  # also use rad(360) = 2 pi

    return min_tree_width


def max_baf(img_width, tree_width):

    return (100 * sin((pi * tree_width) / img_width)) ** 2

    
def plot_ba_calculator(baf, in_tree_num):

    return baf * in_tree_num