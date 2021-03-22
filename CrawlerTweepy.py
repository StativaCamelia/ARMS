import json
import time
from datetime import date, timedelta

import tweepy

with open("credentials.json", "rb") as fp:
    credentials = json.loads(fp.read())

api_key = credentials['api_key']
api_secret_key = credentials['api_secret_key']
access_token = credentials['access_token']
access_token_secret = credentials['access_token_secret']
auth = tweepy.OAuthHandler(api_key, api_secret_key)

auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


def limit_handled(cursor, list_name):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            print("\nData points in list = {}".format(len(list_name)))
            print('Hit Twitter API rate limit.')
            for i in range(3, 0, -1):
                print("Wait for {} mins.".format(i * 5))
                time.sleep(5 * 60)
        except tweepy.error.TweepError:
            print('\nCaught TweepyError exception')


def get_start_date():
    today = date.today()
    week_ago = today - timedelta(days=7)
    print(week_ago.strftime("%Y-%m-%d"))
    return week_ago.strftime("%Y-%m-%d")


def get_user_timeline():
    tweets = []
    statuses = api.user_timeline("elonmusk", count=100)
    for status in statuses:
        tweets.append(status)
    print([tweet.created_at for tweet in tweets])
    print(len(tweets))


get_user_timeline()
