import os
import random


def set_all_seeds(seed):
    '''Sets the seed of the entire notebook so results are the same every time we run.
    This is for reproducibility.'''

    import numpy as np
    np.random.seed(seed)
    random.seed(seed)
    # Set a fixed value for the hash seed
    os.environ['PYTHONHASHSEED'] = str(seed)

def print_directory_structure(path, level=0):
    # Iterate through all items in the given path
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        print('    ' * level + '|-- ' + item)  # Indent based on directory depth
        if os.path.isdir(item_path):
            print_directory_structure(item_path, level + 1)
