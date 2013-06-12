import os
import time
import urllib2
from HTMLParser import HTMLParser

url = 'http://donate.osm.org/comments/'

class DonationHTMLParser(HTMLParser):
    donations = []
    keys = ['name', 'when', 'amount']
    key = -1
    value = ""
    object = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self.key = (self.key +1) % len(self.keys)
            self.value = ""
        elif tag == 'br':
            self.value += "\n"
    def handle_endtag(self, tag):
        if tag == 'td':
            self.object[self.keys[self.key]] = self.value.strip()
            if self.key +1 == len(self.keys):
                self.donations.append(self.object)
                self.object = {}
    def handle_data(self, data):
        self.value += data

rateCache = {}
def toGBP(raw):
    urlPattern = 'http://finance.yahoo.com/d/quotes.csv?e=.csv&f=sl1d1t1&s=%sGBP=X'
    otherCur, otherValue = raw.split(' ')
    if not rateCache.has_key(otherCur):
        print "Getting exchange rate for %s" % otherCur
        rateCache[otherCur] = float(urllib2.urlopen(urlPattern % otherCur).read().split(',')[1].replace(',', ''))
    return float(otherValue.replace(',', '')) * rateCache[otherCur]

def readState(filename):
    # Read the state.txt
    sf = open(filename, 'r')

    state = {}
    for line in sf:
        if line[0] == '#':
            continue
        (k, v) = line.split('=')
        state[k] = v.strip().replace("\\:", ":")

    sf.close()

    return state

last_donation_date = None

if not os.path.exists('donation_state.txt'):
    print "No donation_state file found to poll donation feed."

while True:
    notes_state = readState('donation_state.txt')
    last_donation_date = notes_state.get('last_donation_date', None)

    print "Requesting %s" % url
    try:
        parser = DonationHTMLParser()
        result = urllib2.urlopen(url)
        for data in result:
            parser.feed(data)
        result.close()
        donations = parser.donations
        donations.reverse()
        for donation in donations:
            if donation['when'] > last_donation_date:
                name = donation['name'].split('\n')
                if name[0] == "Anonymous":
                    name[0] = "A generous donor"
                money = donation['amount']
                gbp = "GBP %.2f" % toGBP(money)
                if money != gbp:
                    money += " (%s)" % gbp
                if len(name) == 1:
                    print "%s just donated %s to OSMF" % (name[0], money)
                else:
                    print "%s just donated %s to OSMF: %s" % (name[0], money, name[1])
                last_donation_date = donation['when']

    except urllib2.URLError, e:
        print "Error getting donation page"

    with open('donation_state.txt', 'w') as f:
        f.write('last_donation_date=%s\n' % last_donation_date)

    time.sleep(60)

