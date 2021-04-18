"""
  create_gmail_file.py: Original work Copyright (C) 2021 by Blewett

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
import random

# the following three functions are small version of a corpus based
#   encryption system.  This version encodes only printable characters.
#   there is no backdoor to this.
# Blewett
def triple(p):
    # space through ~ - range of allowable characters
    charset_len = 126 - 32
    half_len = round(charset_len / 2)
    six_bits = 63
    seven_bits = 127
    eight_bits = 255

    x = 0
    for c in p:
        x = (x << 1) + ord(c)

    offset = (x & seven_bits)
    if offset < half_len:
        offset += half_len

    x = x >> 3
    reps = x & eight_bits
    if reps < half_len:
        reps += half_len

    x = x >> 3
    seed = (x & eight_bits) * offset * reps
    if seed < 2209:
        seed += half_len
        seed += seed * six_bits * offset * reps

#    print("s = " +  str(seed) + "  r = " +  str(reps) +
#          "  o = " +  str(offset))
    return seed, reps, offset

def encode(s, p):

    # space through ~ - range of allowable characters
    charset_len = 126 - 32

    (seed, reps, offset) = triple(p)

    random.seed(seed)
    for x in range(0, seed & 7):
        y = random.randint(32, 126)

    key = ""
    for x in range(0, reps):
        for c in (random.sample((range(32,127)), 127 - 32)):
            key = key + chr(c)
    keylen = len(key)
    if offset == 0 or offset >= keylen:
        offset = random.randint(0, keylen - 8)

    e = ""
    index = offset
    for c in s:
        x = index
        while True:
            if c == key[x]:
                ix = x - index
                # targets are no more than charset_len + delta apart
                #  where delta < charset_len
                if ix >= charset_len:
                    e = e + "~"
                    index += charset_len
                    ix = x - index
                e = e + chr(ix + 32)
                index = x
                break

            x += 1
            if x >= keylen:
                e = e + "~~"
                x = 0
                index = 0
    return e

def decode(e, p):
    # space to ~ - range of allowable characters
    charset_len = 126 - 32

    (seed, reps, offset) = triple(p)

    random.seed(seed)
    for x in range(0, seed & 7):
        y = random.randint(32, 126)

    key = ""
    for x in range(0, reps):
        for c in (random.sample((range(32,127)), 127 - 32)):
            key = key + chr(c)
    keylen = len(key)
    if offset == 0 or offset >= keylen:
        offset = random.randint(0, keylen - 8)

    d = ""
    index = offset
    lastc = ""
    for c in e:
        if c == '~':
            if lastc == '~':
                index = 0
                lastc = "check"
                continue
            else:
                index += charset_len
                lastc = c
            continue

        lastc = c
        x = index + ord(c) - 32
        d = d + key[x]
        index = x
    return d


def main():
    # read bits for gmail access file
    bits = { "filename":"","file password":"",
             "login name":"","password":""}

    prompts = { 
        "filename":"Enter the name of the file you want to hold your gmail login and password.",
        "file password":"Enter the password you want to use to secure the gmail file.",
        "login name":"Enter the login name that you use to login to your gmail account.",
        "password":"Enter the password for your gmail account.  We will encrypt it."
    }
    
    print("This program creates a secure file for holding your gmail login information.")
    print("The file created by this program can be used with the camera monitoring program.")
    print("You can run this program repeatedly with no negative effects.")
    
    w = "What do you want to use for your gmail account "

    # loop over the bits and collect the input
    keys = bits.keys()
    for key in keys:
        while bits[key] == "":
            print("")
            print(prompts[key])
            bits[key] = input(w + key + ": ")
            if (bits[key] == "" or len(bits[key]) < 8):
                print("The " + key + " needs to be at least 8 characters long.")
                bits[key] = ""
                continue
            yesno = input("Is \"" + bits[key] + "\" your " + key +
                          " choice? [y/n/q]: ")
            if yesno == "q" or yesno == "Q":
                exit(0)
            if yesno == "y" or yesno == "Y":
                break
            if (yesno == 'n' or yesno != "y" or yesno != "Y" or yesno != ""):
                bits[key] = ""
                continue
    
    # write the file
    f = open(bits["filename"], "w")
    f.write(encode("qux", bits["file password"]) + "\n")
    f.write(encode(bits["login name"], bits["file password"]) + "\n")
    f.write(encode(bits["password"], bits["file password"]) + "\n")
    f.close()
    
    # read the file
    f = open(bits["filename"], "r")
    lines = f.readlines()
    f.close()

    for l in lines:
        l = l.strip()
        print("encoded: " + l)
        print("decoded: " + decode(l, bits["file password"]))
    
    exit(0)

# end of main()

main()
