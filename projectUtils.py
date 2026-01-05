######################################
## THIS FILE SHOULD NOT BE MODIFIED ##
######################################


import os
import argparse


def positiveInt(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive integer value")
    return ivalue


def validFile(value):
    if not os.path.isfile(value):
        raise argparse.ArgumentTypeError(f"{value} does not exist or is not a file")
    return value


def validFolder(value):
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError(f"{value} does not exist or is not a directory (you should create it before)")
    return value

