import csv
import json
import operator
import os
import string
from datetime import *

import nltk
import pandas as pd
import requests
import tweepy
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import stopwords

nltk.download('vader_lexicon')

sid = SentimentIntensityAnalyzer()

user_list = ["officialmcafee", "VitalikButerin", "SatoshiLite", "pmarca", "rogerkver", "aantonop", "ErikVoorhees",
             "NickSzabo4", "CryptoYoda1338", "bgarlinghouse", "BillGates", "JeffBezos", "elonmusk", "MrWarrenBuffet",
             "larryellison", "FloydMayweather", "LMatthaeus10", "aplusk", "MikeTyson", "iamjamiefoxx", "djkhaled",
             "GwynethPaltrow", "Redfoo", "OfficialMelB", "tyler", "cameron", "VentureCoinist", "Cointelegraph",
             "crypto", "PhilakoneCrypto", "laurashin", "cryptomanran", "Excellion", "AriDavidPaul", "iamjosephyoung",
             "JihanWu", "CoinDeskMarkets", "fluffypony", "lawmaster", "mdudas", "Timccopeland", "cz_binance",
             "woonomic", "fintechfrank"]

with open("credentials.json", "rb") as fp:
	credentials = json.loads(fp.read())

api_key = credentials['api_key']
api_secret_key = credentials['api_secret_key']
access_token = credentials['access_token']
access_token_secret = credentials['access_token_secret']
auth = tweepy.OAuthHandler(api_key, api_secret_key)

auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

os.environ['BEARER_TOKEN'] = "AAAAAAAAAAAAAAAAAAAAAF9fNQEAAAAA2ZxGw4tqhHzlAzSVIo3wkcenXd0" \
                             "%3DPSQrW1hTFnmS28lnVAUzbuaCYoSXse68fgQF44lYpbQd7RPAgg "


def auth():
	return os.environ['BEARER_TOKEN']


def get_crypto():
	with open("crypto.json") as fp:
		crypto = json.load(fp)
	return [("#" + crypt["name"].lower(), "#" + crypt["symbol"].lower()) for crypt in crypto["data"]]


def get_start_date():
	now = datetime.now().replace(microsecond=0)
	one_week_ago = now - timedelta(days=7)
	return one_week_ago.isoformat("T") + "Z"


def create_url(user, since_id):
	tweet_fields = "tweet.fields=text,author_id,created_at,referenced_tweets,public_metrics"
	query = "from:{}".format(user)
	if since_id != None:
		url = "https://api.twitter.com/2/tweets/search/recent?query={}&max_results=100&until_id={}&{}".format(query,
		                                                                                                      since_id,
		                                                                                                      tweet_fields)
	else:
		url = "https://api.twitter.com/2/tweets/search/recent?query={}&max_results=100&{}".format(query, tweet_fields)
	return url


def create_headers(bearer_token):
	headers = {"Authorization": "Bearer {}".format(bearer_token)}
	return headers


def connect_to_endpoint(url, headers):
	response = requests.request("GET", url, headers=headers)
	print(response.status_code)
	if response.status_code != 200:
		raise Exception(response.status_code, response.text)
	return response.json()


cryptocurrencies = []


def create_nodes_file():
	crypto = get_crypto()
	with open('node.csv', mode='w') as crypto_file:
		crypto_writer = csv.writer(crypto_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		crypto_writer.writerow(['id', 'cryptocurrency'])
		for i in range(len(crypto)):
			crypto_writer.writerow([str(i), crypto[i][0][1:]])
			cryptocurrencies.append(crypto[i][0][1:])


def load_dataset(file_path):
	return pd.read_csv(file_path)


def convert_article_to_lower_case(df_article):
	return df_article.apply(lambda x: x.lower())


def punctuation_removal(messy_str):
	punctuation = string.punctuation + "“’…–”‘"
	clean_str = messy_str.translate(str.maketrans('', '', punctuation))
	return clean_str


def clean_tweets(filename):
	pd.set_option('mode.chained_assignment', None)
	df = load_dataset('./tweets_csv_files/' + filename)
	# df['tweet_text'] = df['tweet_text'].str[1:]
	df['tweet_text'] = df['tweet_text'].str.replace(r'http\S+', '', regex=True)
	df['tweet_text'] = df['tweet_text'].str.replace(r'[^\x00-\x7F]+', '', regex=True)
	df['tweet_text'] = convert_article_to_lower_case(df['tweet_text'])
	df['tweet_text'] = df['tweet_text'].apply(punctuation_removal)
	stop = stopwords.stopwords
	stop.append('amp')
	df['tweet_without_stopwords'] = df['tweet_text'].apply(
		lambda x: ' '.join([word for word in x.split() if word not in stop]))
	wordfreq = {}
	for user in user_list:
		wordfreq_user = {}
		for sentence, username in zip(df['tweet_without_stopwords'], df['username']):
			if username == user:
				tokens = nltk.word_tokenize(sentence)
				for token in tokens:
					if token not in wordfreq_user.keys():
						wordfreq_user[token] = 1
					else:
						wordfreq_user[token] += 1
		wordfreq[user] = wordfreq_user
	with open('./freq_tweets/' + filename.replace('.csv', '.json'), 'w') as f:
		json.dump(wordfreq, f, indent=4)
	header = ['cryptocurrency', 'username', 'user_id', 'followers_count', 'tweet_without_stopwords', 'created_date',
	          'retweet_count', 'reply_count', 'like_count', 'sentiment']
	df.to_csv('./clean_tweets_csv_files/' + filename, encoding='utf-8-sig', columns=header, index=False)


def main():
	crypto = get_crypto()
	bearer_token = auth()
	headers = create_headers(bearer_token)
	with open('./tweets_csv_files/crypto_file_week4.csv', mode='w') as crypto_file:
		crypto_writer = csv.writer(crypto_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		crypto_writer.writerow(
			['cryptocurrency', 'username', 'user_id', 'followers_count', 'tweet_text', 'created_date', 'retweet_count',
			 'reply_count', 'like_count', 'sentiment'])
		for user in user_list:
			url = create_url(user, None)
			json_response = connect_to_endpoint(url, headers)
			while json_response["meta"]["result_count"] > 0:
				print(f"User {user}")
				json_data = [json for json in json_response['data'] if "referenced_tweets" not in json.keys()]
				for data in json_data:
					for crypt in crypto:
						if crypt[0] in data['text'].lower() or crypt[1] in data['text'].lower():
							sentiment_value = sid.polarity_scores(data['text'])
							del sentiment_value['compound']
							sentiment = max(sentiment_value.items(), key=operator.itemgetter(1))[0]
							crypto_writer.writerow(
								[crypt[0], user, data['author_id'], api.get_user(data['author_id']).followers_count,
								 data['text'].encode('ascii', 'ignore').decode('utf8'), data['created_at'],
								 data['public_metrics']['retweet_count'], data['public_metrics']['reply_count'],
								 data['public_metrics']['like_count'], sentiment])
				url = create_url(user, str(int(json_response["meta"]["oldest_id"]) - 1))
				json_response = connect_to_endpoint(url, headers)


if __name__ == "__main__":
	create_nodes_file()
	main()
	clean_tweets('crypto_file_week4.csv')
