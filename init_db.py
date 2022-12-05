from pathlib import Path
import sqlite3

conn = sqlite3.connect('score_server/app/instance/scores.sqlite3')
c = conn.cursor()

identikeys = Path('identikeys.secret').read_text().splitlines()

for i in identikeys:
    c.execute('INSERT INTO students VALUES (?)', (i,))

conn.commit()
conn.close()