import sys

from .asc import parse
from .pcad import convert as convert_pcad


def main():
    schem = parse(open(sys.argv[1]))
    if schem[0] == 'ACCEL_ASCII':
        print str(convert_pcad(schem))
    else:
        print >> sys.stderr, "Unrecognized file format"
