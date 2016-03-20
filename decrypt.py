#!/usr/bin/python

#from HTMLParser import HTMLParser
#from bs4 import BeautifulSoup
from flask import Flask, request, send_from_directory
import dateutil.parser
import urllib.request
import re
import os
import shutil

app = Flask(__name__)
#app = Flask(__name__, static_folder='public')
#app.config['DEBUG'] = settings['debug']
#app.config['DEBUG'] = True

def decrypt(row, cipher):
    plain = ""
    seed = ((row * 0x1E2F) + 0xFE64) & 0xFFFFFFFF
    for byte in bytes.fromhex(cipher):
        mask = (seed >> 8) & 0xFF
        plain += chr(byte ^ mask)
        seed = (((seed + byte) * 0x0E6C9AA0) + 0x196AAA91) & 0xFFFFFFFF
    plain = re.sub("[^0-9]", "", plain)
    return plain

@app.route('/siste.txt')
def static_from_root():
    return send_from_directory('rating', 'siste.txt')

@app.route("/siste_decrypted.txt")
def main():
    nsf_location = 'http://www.sjakk.no/rating/siste.txt'
    tmp_location = 'tmp/siste.txt'
    location = 'rating/'
    last_nsf_file = location + 'siste.txt'
    last_decrypted_file = location + 'siste_decrypted.txt'
    enc = 'cp865'

    return_data = ''

    print("henter tmp")
    nsf_file = open(urllib.request.URLopener().retrieve(nsf_location, tmp_location)[0], 'r', encoding=enc)

    #nsf_file = urllib.request.urlopen('http://www.sjakk.no/rating/siste.txt')
    nsf_date = dateutil.parser.parse(nsf_file.readline(), dayfirst=True).date()

    try:
        infile = open(last_nsf_file, "r", encoding=enc)
    except FileNotFoundError:
        # If we don't have a local file, NSF's is newer by default
        own_date = dateutil.parser.parse("01/01/70").date()
        print("har ikke lokal fildato, lager %s" % own_date)
    else:
        own_date = dateutil.parser.parse(infile.readline(), dayfirst=True).date()
        print("henter lokal fildato: %s" % own_date)
        infile.close()

    if nsf_date > own_date or not os.path.isfile(last_decrypted_file):
        print("la oss dekryptere")
        try:
            os.replace(last_nsf_file, location + own_date.strftime("%Y-%m-%d") + ".txt")
        except FileNotFoundError:
            pass

        try:
            os.replace(last_decrypted_file, location + own_date.strftime("%Y-%m-%d") + "_decrypted.txt")
        except FileNotFoundError:
            pass

        try:
            shutil.copy(tmp_location, last_nsf_file)
        except FileNotFoundError:
            pass

        outfile_decrypted = open(last_decrypted_file, 'w+', encoding=enc)

        row = 0
        outfile_decrypted.write(nsf_date.strftime("%d/%m/%y") + '\n')
        for line in nsf_file.readlines():
            fields = line.split(";")
            fields[11] = decrypt(row, fields[11])
            outfile_decrypted.write(";".join(fields))
            row += 1

        nsf_file.close()
        outfile_decrypted.close()

    return send_from_directory('rating', 'siste_decrypted.txt')

if __name__ == "__main__":
    main()
