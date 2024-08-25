import random


def set_all_seeds(seed):
    '''Sets the seed of the entire notebook so results are the same every time we run.
    This is for reproducibility.'''
    import os

    import numpy as np
    np.random.seed(seed)
    random.seed(seed)
    # Set a fixed value for the hash seed
    os.environ['PYTHONHASHSEED'] = str(seed)
