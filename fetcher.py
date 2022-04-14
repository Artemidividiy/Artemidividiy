from asyncio import constants
import requests
import re
import json
from rich.console import Console
from python_graphql_client import GraphqlClient

import feedparser
import httpx
import json
import pathlib
import re
import os

json_constants = open("./constants.json")
console = Console()
def get_last_cf():
    try:
        r = requests.get(json.load(json_constants)["codeforces_user_rating"])
        return str(r.json()['result'][-1]['newRating'])
    finally:
        pass

def fetch_writing():
    pass

root = pathlib.Path(__file__).parent.resolve()
client = GraphqlClient(endpoint="https://api.github.com/graphql")

def replace_chunk(content, marker, chunk):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    chunk = "<!-- {} starts -->\n{}\n<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)


def make_query(after_cursor=None):
    return """
query 
  {
  user(login: "Artemidividiy") {
    repositoriesContributedTo(
      last: 5
      contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, PULL_REQUEST_REVIEW, REPOSITORY]
      includeUserRepositories: true
    ) {
      nodes {
        name
        ... on Repository {
          defaultBranchRef {
            target {
              ... on Commit {
                history(first: 3, author: {id: "MDQ6VXNlcjQ0NDQ3Nzk4"}) {
                  edges {
                    node {
                      ... on Commit {
                        message
                        committedDate
                        committer {
                          date
                          email
                          name
                        }
                      }
                    }
                  }
                  totalCount
                }
              }
            }
          }
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
      totalCount
    }
  }
}
"""


def fetch_releases(oauth_token):
    repos = []
    releases = []
    repo_names = set()
    has_next_page = True
    after_cursor = None

    while has_next_page:
        data = client.execute(
            query=make_query(after_cursor),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )
        print()
        print(data)
        # print(json.dumps(data, indent=4))
        print()
        for repo in data["data"]["user"]["repositoriesContributedTo"]["nodes"]:
            if repo["name"]["totalCount"] and repo["name"] not in repo_names:
                repos.append(repo)
                repo_names.add(repo["name"])
                releases.append(
                    {
                        "repo": repo["name"],
                        "release": repo["releases"]["nodes"][0]["name"]
                        .replace(repo["name"], "")
                        .strip(),
                        "published_at": repo["releases"]["nodes"][0][
                            "publishedAt"
                        ].split("T")[0],
                        "url": repo["releases"]["nodes"][0]["url"],
                    }
                )
        has_next_page = data["data"]["viewer"]["repositories"]["pageInfo"][
            "hasNextPage"
        ]
        after_cursor = data["data"]["viewer"]["repositories"]["pageInfo"]["endCursor"]
    return releases



if __name__ == "__main__":
    readme = root / "README.md"
    releases = fetch_releases(json.load(json_constants)["github_auth_token"])
    releases.sort(key=lambda r: r["published_at"], reverse=True)
    md = "\n".join(
        [
            "* [{repo} {release}]({url}) - {published_at}".format(**release)
            for release in releases[:5]
        ]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(readme_contents, "recent_releases", md)
    readme.open("w").write(rewritten)

# if __name__ == "__main__":
#     print(get_last_cf())