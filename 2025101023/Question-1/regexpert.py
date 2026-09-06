import sys

def read_input():
    line1 = sys.stdin.readline()
    regex = line1.rstrip("\r\n")

    txt = sys.stdin.read()

    return regex, txt

regex, txt = read_input()
print("REGEX:",repr(regex))
print("TEXT:",repr(txt))