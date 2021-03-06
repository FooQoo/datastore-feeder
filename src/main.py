from tweet import TweetAPI, ApiConfig
from rss import RssAPI, PaperAPI
from datastore import TweetDataStore, RssDataStore
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
from time import sleep

config = 'src/resources/.env'


def get_tweet(event, context):
    load_dotenv(config, verbose=True)

    tweet_datastore = TweetDataStore()

    latest_tweet = tweet_datastore.get_latest_tweet()
    latest_id = None if len(latest_tweet) == 0 else latest_tweet[0]['tweet_id']

    api_config = ApiConfig()
    api_key = api_config.get_key_from_env()
    wrapper = TweetAPI(
        api_key['CONSUMER_KEY'],
        api_key['CONSUMER_SECRET'],
        api_key['ACCESS_TOKEN'],
        api_key['ACCESS_TOKEN_SECRET'])

    tweets = wrapper.fetch_by_query(
        q='#福井県マスク在庫', since_id=latest_id)

    entities = []
    for tweet in tweets:
        for tag in list(set(tweet['hashtags'])):
            if tag != '福井県マスク在庫':
                entities.append({
                    'tweet_id': tweet['id_str'],
                    'shop': tag,
                    'created_at': tweet['created_at']
                })

    tweet_datastore.insert_tweets(entities)


def get_rss(event, context):
    def is_covid_article(html):
        if html == "":
            return False

        soup = BeautifulSoup(html, 'html.parser')
        context = ' '.join(
            [i.p.text for i in
             soup.find_all('div', {'class': 'article-body'})])
        return re.search(r'コロナ|感染', context) is not None

    def is_covid_title(title):
        return re.search(r'コロナ|感染', title) is not None

    load_dotenv(config, verbose=True)

    rss_datastore = RssDataStore()
    wrapper, paper_api = RssAPI(), PaperAPI()

    rss_docs = wrapper.fetch_rss()

    filtered_rss_docs = []
    for doc in rss_docs:
        if (is_covid_article(paper_api.fetch_paper(doc['link'])) or
                is_covid_title(doc['title'])):
            filtered_rss_docs.append(doc)

    rss_datastore.insert_rss_docs(filtered_rss_docs)


if __name__ == "__main__":
    #get_tweet(None, None)
    get_rss(None, None)
