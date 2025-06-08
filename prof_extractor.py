import os
import json
import re
import pprint

output_data = {}


with open("Profiles.txt") as fd:
    family = None
    norm = None
    unit = None
    headers = None

    


    while True:
        line = fd.readline()

        if line == "":
            break

        elif line.startswith('#'):
            continue

        elif line == "\n":
            family = None
            norm = None
            unit = None
            headers = None

        elif line.startswith('*'):
            family = line.strip('*\n')
            norm = fd.readline().strip('*\n')
            unit = fd.readline().strip('*\n')
            headers = fd.readline().strip('*\n').split("/")

            output_data[family] = {
                "norm":norm,
                "unit":unit,
                "fillet":True,
                "sizes":{}
            }

            current_data = output_data[family]

        else:
            data_line = re.split(r'\t+', line.strip("\n").rstrip('\t'))
            data_line = [s.strip() for s in data_line]

            d = dict(zip(headers[1:], data_line[1:]))
            current_data['sizes'][data_line[0]] = d


with open("metal.json", "w") as fd:
    json.dump(output_data, fd, indent=4)
