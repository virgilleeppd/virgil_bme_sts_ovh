import settings
from types import *
from utils import *
from DataFetcher import DataFetcher
import pdb

from AlgoEngine import AlgoManager

"""
Testing file for the backend SQL connections
with the functions.

First, feature extraction is done and saved
to the server. 

Then (in the future) you can use this script
for similarity testing as well
"""
#Sample Test Subject Buffalo Cases 3
am = AlgoManager('3685295524',local=False)

# tests saving of STS and OVH
am.feature_extraction()
