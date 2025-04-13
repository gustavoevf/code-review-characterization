import requests
import pandas as pd
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Defina seu token do GitHub
TOKEN = "TOKEN"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
GRAPHQL_URL = "https://api.github.com/graphql"
REPO_CSV_FILE = "github_repositories.csv"
PR_CSV_FILE = "github_pr_dataset.csv"

# Função para coletar os repositórios mais populares
def get_repositories():
    if os.path.exists(REPO_CSV_FILE):
        print(f"Arquivo '{REPO_CSV_FILE}' encontrado. Carregando repositórios do CSV...")
        df = pd.read_csv(REPO_CSV_FILE)
        return df.to_dict(orient="records")

    print("Iniciando busca pelos repositórios mais populares...")
    query = """
    query ($cursor: String) {
      search(query: "stars:>10000", type: REPOSITORY, first: 50, after: $cursor) {
        pageInfo {
          endCursor
          hasNextPage
        }
        edges {
          node {
            ... on Repository {
              name
              owner {
                login
              }
            }
          }
        }
      }
    }
    """
    repos = []
    cursor = None

    while True:
        response = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query, "variables": {"cursor": cursor}})
        if response.status_code != 200:
            print(f"Erro na requisição. Código: {response.status_code}")
            print("Cabeçalho da resposta:")
            print(response.headers)
            print("Corpo da resposta:")
            print(response.text)
            break


        data = response.json()
        search_data = data["data"]["search"]

        for edge in search_data["edges"]:
            repo_data = {
                "name": edge["node"]["name"],
                "owner": edge["node"]["owner"]["login"],
                "pr_collected": False
            }
            repos.append(repo_data)
            save_to_csv([repo_data], REPO_CSV_FILE)

        cursor = search_data["pageInfo"]["endCursor"]
        if not search_data["pageInfo"]["hasNextPage"] or len(repos) >= 200:
            break

        print("Pausando por 2 segundos para evitar limites da API...")
        time.sleep(2)

    print(f"Coleta de repositórios concluída! Total coletado: {len(repos)}")
    return repos

# Configure retry mechanism
session = requests.Session()
retry = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))

def get_pull_requests(owner, name):
    print(f"Iniciando busca por PRs no repositório: {owner}/{name}...")
    query = """
    query ($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        pullRequests(first: 40, states: [MERGED, CLOSED], after: $cursor) {
          pageInfo {
            endCursor
            hasNextPage
          }
          edges {
            node {
              number
              title
              createdAt
              mergedAt
              closedAt
              bodyText
              reviews { totalCount }
              files { totalCount }
              additions
              deletions
              comments { totalCount }
              participants { totalCount }
              state
            }
          }
        }
      }
    }
    """
    cursor = None
    prs = []

    while True:
        try:
            response = session.post(GRAPHQL_URL, headers=HEADERS, json={"query": query, "variables": {"owner": owner, "name": name, "cursor": cursor}}, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors
        except requests.exceptions.RequestException:
            print(f"Erro na requisição. Código: {response.status_code}")
            print("Cabeçalho da resposta:")
            print(response.headers)
            print("Corpo da resposta:")
            print(response.text)
            break

        data = response.json()
        pr_data = data["data"]["repository"]["pullRequests"]

        for edge in pr_data["edges"]:
            pr_node = edge["node"]
            created_at = pr_node["createdAt"]
            closed_at = pr_node.get("closedAt") or pr_node.get("mergedAt")
            if pr_node["reviews"]["totalCount"] > 0 and closed_at:
                review_time = (pd.to_datetime(closed_at) - pd.to_datetime(created_at)).total_seconds() / 3600
                if review_time > 1:
                    prs.append({
                        "repository": f"{owner}/{name}",
                        "number": pr_node["number"],
                        "title": pr_node["title"],
                        "created_at": created_at,
                        "closed_at": closed_at,
                        "state": pr_node["state"],
                        "review_count": pr_node["reviews"]["totalCount"],
                        "description_length": len(pr_node["bodyText"]),
                        "file_count": pr_node["files"]["totalCount"],
                        "additions": pr_node["additions"],
                        "deletions": pr_node["deletions"],
                        "comments_count": pr_node["comments"]["totalCount"],
                        "participants_count": pr_node["participants"]["totalCount"]
                    })

        cursor = pr_data["pageInfo"]["endCursor"]
        if not pr_data["pageInfo"]["hasNextPage"]:
            break

        print("Pausando por 3 segundos para evitar limites da API...")
        time.sleep(3)

    print(f"Coleta de PRs concluída para {owner}/{name}! Total coletado: {len(prs)}")
    save_to_csv(prs, PR_CSV_FILE)
    return len(prs) > 0

# Função para salvar dados no CSV progressivamente
def save_to_csv(data, file_name):
    df = pd.DataFrame(data)
    if not os.path.exists(file_name):
        df.to_csv(file_name, index=False)
    else:
        df.to_csv(file_name, mode='a', header=False, index=False)

# Atualiza o status de coleta dos repositórios no CSV
def update_repo_csv(repo_name, repo_owner):
    df = pd.read_csv(REPO_CSV_FILE)
    df.loc[(df["name"] == repo_name) & (df["owner"] == repo_owner), "pr_collected"] = True
    df.to_csv(REPO_CSV_FILE, index=False)

# Carregar repositórios e buscar PRs apenas para aqueles ainda pendentes
repositories = get_repositories()

for repo in repositories:
    if not repo.get("pr_collected", False):  # Apenas busca PRs se ainda não coletado
        pr_found = get_pull_requests(repo["owner"], repo["name"])
        if pr_found:
            update_repo_csv(repo["name"], repo["owner"])

print(f"Coleta finalizada. Dados salvos em '{REPO_CSV_FILE}' e '{PR_CSV_FILE}'.")
