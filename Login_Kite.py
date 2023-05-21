#import modules

from kiteconnect import KiteConnect

variables = {}
with open('Input_File.txt', 'r') as f:
    lines = f.readlines()



for line in lines:
    variable, value = line.strip().split('=')
    variables[variable] = value

key = variables['key']
secret = variables['secret']
req_tkn = variables['req_tkn']

#Initialize the KiteConnect to access methods and endpoints provided by KiteConnect API
kite = KiteConnect(api_key=key)

#Use below line to generate request token
# print(kite.login_url())

#Use below line to generate access_token
gen_ssn = kite.generate_session(request_token=req_tkn, api_secret=secret)
acc_tkn = gen_ssn['access_token']
print(acc_tkn)
#
