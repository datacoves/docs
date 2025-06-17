#!/usr/bin/env python3
import csv
import json
import sys

if __name__ == "__main__":
    program_name, *all_args = sys.argv

    if len(all_args) == 0:
        path = input("Please enter path to csv: ")
    else:
        path = all_args[0]

    delimiter = input("Specify delimiter char (default is ','): ") or ","
    quote = input("Specify quote char (default is '\"'): ") or '"'

    with open(path, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter, quotechar=quote)
        for row in reader:
            schema = {col: "string" for col in row}
            print(json.dumps(schema))
            break
