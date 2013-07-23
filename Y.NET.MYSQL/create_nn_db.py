#!/usr/bin/python
import MySQLdb
db = MySQLdb.connect(host="localhost", user="root", passwd="123qwe", db="nn", charset='utf8')
con = db.cursor()
con.execute('CREATE TABLE hiddennode (id MEDIUMINT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id), create_key VARCHAR(100))')
con.execute('CREATE INDEX idx_hiddennode ON hiddennode (create_key)')
con.execute('CREATE TABLE wordhidden(id MEDIUMINT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id), fromid INT NOT NULL, toid INT NOT NULL, strength FLOAT)')
con.execute('CREATE INDEX idx_wfromid ON wordhidden (fromid)')
con.execute('CREATE INDEX idx_wtoid ON wordhidden (toid)')
con.execute('CREATE TABLE hiddenurl(id MEDIUMINT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id), fromid INT NOT NULL, toid INT NOT NULL, strength FLOAT)')
con.execute('CREATE INDEX idx_ufromid ON hiddenurl (fromid)')
con.execute('CREATE INDEX idx_utoid ON hiddenurl (toid)')
db.commit()
