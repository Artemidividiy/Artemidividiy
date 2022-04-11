from asyncio import constants
import requests
import re
import json

def get_last_cf():
    try:
        f = open("./constants.json")
        r = requests.get(json.load(f)["codeforces_user_rating"])
        return r.json()['result'][-1]['newRating']
    finally:
        pass

def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r'<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->'.format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = '\n{}\n'.format(chunk)
    chunk = '<!-- {} starts -->{}<!-- {} ends -->'.format(marker, chunk, marker)
    return r.sub(chunk, content)

print(get_last_cf())