import csv

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
    return "; ".join(map(lambda row: " ".join(row), rows))

if __name__ == "__main__":
    print(parse_csv_text("./test.txt"))
