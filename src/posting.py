import tweepy
from src.card import make_card

def post_thread(client: tweepy.Client, api_v1: tweepy.API, thread: list[str],
                card_title: str, card_project: str, card_footer: str,
                self_reply_enabled: bool, self_reply_text: str) -> str:
    card = make_card(card_title, card_project, card_footer)
    media = api_v1.media_upload(filename=str(card))

    root = client.create_tweet(text=thread[0], media_ids=[media.media_id_string])
    root_id = root.data["id"]

    prev = root_id
    for t in thread[1:]:
        r = client.create_tweet(text=t, in_reply_to_tweet_id=prev)
        prev = r.data["id"]

    if self_reply_enabled and self_reply_text:
        try:
            client.create_tweet(text=self_reply_text[:275], in_reply_to_tweet_id=root_id)
        except Exception:
            pass

    return str(root_id)
