from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import time
import tweepy

n = 20            #only look at n most recent networks
minwin = 20
minpct = 55
waittime = 60     #redo as a cron job?

# Create variables for each key, secret, token
consumer_key = 
consumer_secret = 
access_token = 
access_token_secret = 

# Set up OAuth and integrate with API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

def win_loss_pct_calc(winloss):     #when 0:0, no % is given, so just return 0%
    spl = winloss.split()
    if len(spl)<4:
        return 0
    else:
        return float(spl[-1][1:-2])
    
def tweeter():

    html = urlopen("http://zero.sjeng.org/")
    soup = BeautifulSoup(html, 'html.parser')

    matches = soup.find( "table", {"class":"matches-table"} )
    best = soup.find( "table", {"class":"networks-table"} )

    df = pd.read_html(str(matches))[0].iloc[2:2+n]
    df.columns = ["date","hashes","winloss","games","sprt"]
    df['netw'] = df['hashes'].apply(lambda hash: hash.split()[0][:8])
    df['net_info'] = df['hashes'].apply(lambda hash: hash.split()[0][8:])
    df['wins'] = df['winloss'].apply(lambda wl: int(wl.split()[0]))
    df['losses'] = df['winloss'].apply(lambda wl: int(wl.split()[2]))
    df['pct'] = df['winloss'].apply(win_loss_pct_calc)

    saved = pd.read_csv('saved.csv',index_col=0)

    print('loaded saved.tail():')         #for testing, can remove
    print(saved.tail())


    #Checking current strongest

    curr_strongest = pd.read_html(str(best))[0].iloc[2,2]

    if curr_strongest not in saved.index:
        saved = saved.append(pd.DataFrame([[False,False]],columns=['promising','strongest'],index=[curr_strongest]))

    if saved['strongest'][curr_strongest]==False:
        info_winloss = df[df['netw']==curr_strongest].winloss.values[0]
        info_steps = df[df['netw']==curr_strongest].net_info.values[0]
        tweet = 'LeelaZ - New strongest: ' + info_winloss +'\nhash: ' + curr_strongest +' ('+info_steps+')\nSee zero.sjeng.org'

        print(tweet)
        api.update_status(status=tweet)
        saved['strongest'][curr_strongest]=True


    #Checking for promising networks  

    pr = df[(df['pct']>minpct)&(df['wins']>minwin)&(df['sprt']!='PASS')&(df['sprt']!='fail')]
    promising_list = set(pr['netw'])

    for i in promising_list:     
        if i not in saved.index:
            saved = saved.append(pd.DataFrame([[False,False]],columns=['promising','strongest'],index=[i]))

        if saved['promising'][i]==False:
            info_winloss = df[df['netw']==i].winloss.values[0]
            info_steps = df[df['netw']==i].net_info.values[0]
            tweet = 'LeelaZ - Promising network: '+info_winloss+'\nhash: '+ i +' ('+info_steps+')\nSee zero.sjeng.org'
            print(tweet)
            api.update_status(status=tweet)
            saved['promising'][i]=True

    saved.to_csv('saved.csv')

    print('saved.tail() is currently:')       #for testing, can remove
    print(saved.tail())  
            
while True:
    tweeter()
    print('scraped at: '+time.ctime())
    time.sleep(waittime)
