import sqlite3
from datetime import datetime
import time
import socket
import fcntl
import struct
import urllib2
import ConfigParser

db_file = "rpi-sprinklers.db"
test_url = "http://www.google.it"

def get_interface_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
        ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip

def internet_on():
    try:
        response = urllib2.urlopen(test_url, timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False

def setup_db():
    db_conn = sqlite3.connect(db_file)
    db_cursor = db_conn.cursor()

    db_cursor.execute("CREATE TABLE IF NOT EXISTS valves (id integer PRIMARY KEY, name text)")
    db_cursor.execute("CREATE TABLE IF NOT EXISTS irrigations (id integer PRIMARY KEY, valve_id integer, start_at integer, duration integer)")

    db_conn.commit()

def setup_config():
    config = ConfigParser.RawConfigParser()
    config.add_section('General')
    config.set('General', 'db_file', 'rpi-sprinklers.db')
    with open('config.ini', 'wb') as configfile:
        config.write(configfile)

def main(args):

    setup_config()
    setup_db()

    starttime = time.time()
    while True:

        db_conn = sqlite3.connect(db_file)
        db_cursor = db_conn.cursor()

        now = datetime.now()

        minute_start = datetime(now.year, now.month, now.day, now.hour, now.minute, 0)
        minute_stop = datetime(now.year, now.month, now.day, now.hour, now.minute, 59)

        values = (int(time.mktime(minute_start.timetuple())), int(time.mktime(minute_stop.timetuple())))
        print values
        db_cursor.execute('SELECT * FROM irrigations WHERE start_at >= ? AND start_at <= ?', values)
        db_conn.commit()
        rows = db_cursor.fetchall()
        print rows

        db_conn.close()
        time.sleep(6.0 - ((time.time() - starttime) % 6.0))

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
