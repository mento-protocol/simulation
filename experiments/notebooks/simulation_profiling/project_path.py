"""
Ensure the top level module is in sys.path
"""
import sys
import os

MODULE_PATH = os.path.abspath(os.path.join(os.pardir, os.pardir))
if MODULE_PATH not in sys.path:
    sys.path.append(MODULE_PATH)
