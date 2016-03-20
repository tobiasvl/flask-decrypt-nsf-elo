#!/usr/bin/python

#from HTMLParser import HTMLParser
#from bs4 import BeautifulSoup
from flask import Flask, request, send_from_directory
import dateutil.parser
import urllib.request
import re
import os
import shutil
from zipfile import ZipFile

app = Flask(__name__)
#app = Flask(__name__, static_folder='public')
#app.config['DEBUG'] = settings['debug']
#app.config['DEBUG'] = True

def nsf_decrypt(row, cipher):
    plain = ""
    seed = ((row * 0x1E2F) + 0xFE64) & 0xFFFFFFFF
    for byte in bytes.fromhex(cipher):
        mask = (seed >> 8) & 0xFF
        plain += chr(byte ^ mask)
        seed = (((seed + byte) * 0x0E6C9AA0) + 0x196AAA91) & 0xFFFFFFFF
    plain = re.sub("[^0-9]", "", plain)
    return plain

def get_nsf_data():
    """Get the latest NSF ratings as a list of semicolon-separated values (the same format NSF uses).
       Also decrypts the unofficial rating."""
    nsf_location = 'http://www.sjakk.no/rating/siste.txt'
    tmp_location = 'tmp/siste.txt'
    location = 'rating/'
    last_nsf_file = location + 'siste.txt'
    last_decrypted_file = location + 'siste_decrypted.txt'
    enc = 'cp865'

    nsf_file = open(urllib.request.URLopener().retrieve(nsf_location, tmp_location)[0], 'r', encoding=enc)

    #nsf_file = urllib.request.urlopen('http://www.sjakk.no/rating/siste.txt')
    #nsf_date = dateutil.parser.parse(nsf_file.readline(), dayfirst=True).date()

    #try:
    #    infile = open(last_nsf_file, "r", encoding=enc)
    #except FileNotFoundError:
    #    # If we don't have a local file, NSF's is newer by default
    #    own_date = dateutil.parser.parse("01/01/70").date()
    #else:
    #    own_date = dateutil.parser.parse(infile.readline(), dayfirst=True).date()
    #    infile.close()

    #if nsf_date > own_date or not os.path.isfile(last_decrypted_file):
    if True:
        #try:
        #    os.replace(last_nsf_file, location + own_date.strftime("%Y-%m-%d") + ".txt")
        #except FileNotFoundError:
        #    pass

        #try:
        #    os.replace(last_decrypted_file, location + own_date.strftime("%Y-%m-%d") + "_decrypted.txt")
        #except FileNotFoundError:
        #    pass

        #try:
        #    shutil.copy(tmp_location, last_nsf_file)
        #except FileNotFoundError:
        #    pass

        #outfile_decrypted = open(last_decrypted_file, 'w+', encoding=enc)
        outfile_decrypted = []
        row = 0
        nsf_file.readline()
        #outfile_decrypted.write(nsf_date.strftime("%d/%m/%y") + '\n')
        for line in nsf_file.readlines():
            fields = line.split(";")
            fields[11] = nsf_decrypt(row, fields[11])
            #outfile_decrypted.write(";".join(fields))
            outfile_decrypted.append(';'.join(fields))
            row += 1

        nsf_file.close()
        #outfile_decrypted.close()

    #nsf_decrypted = open(last_decrypted_file, 'r', encoding=enc)
    #return nsf_decrypted.readlines()
    return outfile_decrypted

def get_fide_data():
    """Get the latest FIDE ratings as a list of whitespace-separated values (the same format FIDE uses)."""
    fide_dump = {'standard': [], 'rapid': [], 'blitz': []}
    tmp_location = 'tmp/'
    fide_location = 'http://ratings.fide.com/download/'
    fide_filenames = ('standard_rating_list.zip', 'rapid_rating_list.zip', 'blitz_rating_list.zip')
    for fide_zip in fide_filenames:
        urllib.request.URLopener().retrieve(fide_location + fide_zip, tmp_location + fide_zip)
        with ZipFile(tmp_location + '/' + fide_zip) as myzip:
             with myzip.open(fide_zip.replace('zip', 'txt')) as txt:
                 fide_dump[re.findall(r"[^_.]+", fide_zip)[0]] = txt.readlines()

    return fide_dump

import csv
import sqlite3
conn = sqlite3.connect('ratings.db')

fieldnames = ['nsf_id', 'name', 'sex', 'club', 'official_rating', 'games', 'ngp', 'birth_year', 'fide_id', 'year', 'birthdate', 'unofficial_rating', 'date']

# TODO lag schema med PK osv
#if not os.path.exists('ratings.db'):
try:
    conn.execute("CREATE TABLE players ({!s})".format(','.join([f for f in fieldnames if f != 'official_rating' and f != 'games' and f != 'ngp' and f != 'unofficial_rating' and f != 'date'])))
    conn.execute("CREATE TABLE nsf_ratings ({!s})".format(','.join(['nsf_id', 'official_rating', 'games', 'ngp', 'unofficial_rating', 'date'])))
except sqlite3.OperationalError:
    pass

#nsf_data = get_nsf_data()
#nsf_reader = csv.DictReader(nsf_data, fieldnames=fieldnames, delimiter=';')
#date = next(nsf_reader)['nsf_id']
#for row in nsf_reader:
#    row['name'] = '"' + row['name'] + '"'
#    row['club'] = '"' + row['club'] + '"'
#    row['sex'] = '"' + row['sex'] + '"'
#    row['ngp'] = '"' + row['ngp'] + '"'
#    for k in row:
#        if not row[k]:
#            row[k] = '0'
#    # hva hvis den finnes men data er forskjellig?
#    conn.execute("INSERT INTO players ({!s}) SELECT {!s} WHERE NOT EXISTS(SELECT 1 FROM players WHERE nsf_id = {!s});".format(','.join([f for f in fieldnames if f != 'official_rating' and f != 'games' and f != 'ngp' and f != 'unofficial_rating' and f != 'date']),
#                                                                    ','.join([row[f] for f in fieldnames if f != 'official_rating' and f != 'games' and f != 'ngp' and f != 'unofficial_rating' and f != 'date']), row['nsf_id']))
#    conn.execute("INSERT INTO nsf_ratings ({!s}) SELECT {!s} WHERE NOT EXISTS(SELECT 1 FROM nsf_ratings WHERE nsf_id = {!s} AND date = {!s})".format(','.join(['nsf_id', 'official_rating', 'games', 'ngp', 'unofficial_rating', 'date']), ','.join([row[fieldname] for fieldname in ['nsf_id', 'official_rating', 'games', 'ngp', 'unofficial_rating']]) + ',' + date, row['nsf_id'], date))
#conn.commit()
#conn.close()

fide_data = get_fide_data()
f = open('tmp/fide_std', 'w')
print(fide_data)
f.write('\n'.join([str(s) for s in fide_data['standard']]))
f.close()
f = open('tmp/fide_rpd', 'w')
f.write('\n'.join([str(s) for s in fide_data['rapid']]))
f.close()
f = open('tmp/fide_btz', 'w')
f.write('\n'.join([str(s) for s in fide_data['blitz']]))
f.close()
#
#csv.read(fide_data)
#
#
#if __name__ == "__main__":
#    main()
