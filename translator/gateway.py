# -*- coding: utf-8 -*-
# Copyright (c) 2014, Mayo Clinic
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
#     Neither the name of the <ORGANIZATION> nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
import requests
import sys
import re
import argparse

auth_url = "https://datamarket.accesscontrol.windows.net/v2/OAuth2-13"
translate_url = "http://api.microsofttranslator.com/v2/Http.svc/Translate"

client_id = 'TBXform'
client_secret = 'uIBJDNcc5K21BCsK/w2DBQNE4ezCebif0oyiIWAep0Y='
default_from_language = 'it'
default_to_language = 'en'

# It is hardly worth using an XML parser for the simple response format
resp_value_re = re.compile('<string .*>(.*)</string>', re.MULTILINE)


class Gateway():
    def __init__(self):
        self.token = None
        self.expires_in = 0

    def renew_token(self):
        data={'client_id': client_id,
              'client_secret': client_secret,
              'scope': 'http://api.microsofttranslator.com',
              'grant_type': 'client_credentials'}
        response = requests.post(auth_url, data=data)
        if response.ok:
            data = response.json()
            self.token = data['access_token']
            self.expires_in = int(data['expires_in'])
        else:
            print("Translation access error: %s : %s" % (response.status_code, response.reason))

    def translate(self, text, from_language=default_from_language, to_language=default_to_language, asXML=False, inside=False):
        if not self.token:
            self.renew_token()
        if self.token:
            header = {'Authorization': 'Bearer ' + self.token}
            params = {'text': text, 'from': from_language, 'to': to_language}
            response = requests.get(translate_url, headers=header, params=params)
            if response.ok:
                return response.content.decode() if asXML else resp_value_re.sub('\\1', response.content.decode())
            elif response.status_code == 400 and not inside:
                self.token = None
                return self.translate(text, from_language=from_language, to_language=to_language, asXML=asXML, inside=True)
            else:
                print("Translation access error: %s : %s" % (response.status_code, response.reason))
                return '<string xmlns="http://schemas.microsoft.com/2003/10/Serialization/">' + text + '</string>'


def main(args):
    optparser = argparse.ArgumentParser(description="Translate text from one language to another")
    optparser.add_argument('term', help="Term to translate", nargs='+')
    optparser.add_argument('-f', '--frm', help="From language", default=default_from_language)
    optparser.add_argument('-t', '--to', help="To language", default=default_to_language)

    opts = optparser.parse_args(args)
    print(Gateway().translate(opts.term, from_language=opts.frm, to_language=opts.to))


if __name__ == '__main__':
    main(sys.argv[1:])
