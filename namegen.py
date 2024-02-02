import random

used_indexes = []

with open("./names.txt", 'r') as f:
    NAMES = f.readlines()

def assign_name():
    index = random.randint(0, len(NAMES) - 1)

    if len(used_indexes) == len(NAMES):
        return "NO MORE NAMES"

    while index in used_indexes:
        index = (index + 1) % len(NAMES)
    used_indexes.append(index)

    #                  vvvvv - Remove newline
    name = NAMES[index][:-1]

    return name

if __name__ == "__main__":
    for _ in range(104):
        print(assign_name())
