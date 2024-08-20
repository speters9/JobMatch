import datetime
import functools
import hashlib
import logging
import random
import re
import sys
import time
import uuid
from typing import Any

# Below are global functions

def current_time():
    '''
    creates datetime stamp when printing
    '''
    current_time = time.ctime()
    # formatting weekday, dd mmm yyy, time
    custom_format = "%a %d %b %Y, %H:%M:%S"
    # parsing and reformatting current time
    formatted_time = time.strftime(custom_format, time.strptime(current_time))

    return formatted_time


def filesave_time():
    '''
    creates datetime stamp when printing
    '''
    current_time = time.ctime()
    # formatting weekday, dd mmm yyy, time
    custom_format = "%Y_%m_%d_T%H%M"
    # parsing and reformatting current time
    formatted_time = time.strftime(custom_format, time.strptime(current_time))

    return formatted_time


def reset_logger(level = "warning"):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set the logging level to WARNING to reduce verbosity
    if level == "info":
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    elif level == "warning":
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)
    else:
        print("Logger not set. Please use info or warning")



def generate_uuid():
    '''
    used to generate unique identifiers
    '''
    return str(uuid.uuid4())


def get_key(val,dict_in):
    '''
    Returns the key of a dictionary given a value
    '''
    for key, value in dict_in.items():
        if val == value:
            return key
    return None


def getMD5(file_name):
    md5_hash = hashlib.md5()
    with open(file_name, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()


def set_all_seeds(seed):
    '''Sets the seed of the entire notebook so results are the same every time we run.
    This is for REPRODUCIBILITY.'''
    import os

    import numpy as np
    import torch
    np.random.seed(seed)
    torch.manual_seed(seed)
    random.seed(seed)
    torch.cuda.manual_seed(seed)
    # When running on the CuDNN backend, two further options must be set
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    # Set a fixed value for the hash seed
    os.environ['PYTHONHASHSEED'] = str(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class MyTimer:
    '''
    Context manager for time to completion for any function or calcuation
    '''
    def __enter__(self):
        self.start = time.time()

    def __exit__(self,type,value,traceback):
        end = time.time()
        print(f'\nCalculation took {(end-self.start)/60:.2f} minutes to execute')


# utility functions
def graceful_exit(func):
    """Gracefully exit a longrunning script."""
    @functools.wraps(func)
    def wrapper_graceful_exit(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("Keyboard Interrupt detected. Exiting gracefully...")
            sys.exit(0)
    return wrapper_graceful_exit
