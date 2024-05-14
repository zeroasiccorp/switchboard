import sys

infile = sys.argv[1]
outfile = sys.argv[2]

to_remove = sys.argv[3:]

with open(infile, 'r') as i:
    with open(outfile, 'w') as o:
        for line in i:
            for elem in to_remove:
                line = line.replace(elem, '')
            o.write(line)
