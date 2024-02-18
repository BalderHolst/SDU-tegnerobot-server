import csv
import struct

class ParserError(Exception): pass

def pack_float(n: float) -> bytearray:
    return bytearray(struct.pack("d", n))  

def pack_csv_row(row):
    bytes_row = bytearray()
    for e in row:
        try:
            f = float(e)
        except ValueError:
            raise ParserError(f"Found invalid float: {e}")

        fba = pack_float(f)
        bytes_row.extend(fba)

    return bytes(bytes_row)

def parse_csv_text(text: str):
    lines = text.split('\n')
    rows = csv.reader(lines)

    # Stringify into something like this:
    # f1 f2 f3; f4 f5 f6; f7 f8 f9; f10 f11 f12
    #
    # Representing a table like this:
    # f1  f2  f3
    # f4  f5  f6
    # f7  f8  f8
    # f10 f11 f12
    return b"".join(map(pack_csv_row, rows))

if __name__ == "__main__":
    with open("./test.csv") as f:
        text = f.read()
    print(parse_csv_text(text))
