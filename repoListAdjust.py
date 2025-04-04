import pandas as pd

# Definir caminhos para os arquivos CSV
REPO_CSV_FILE = "github_repositories.csv"
PR_CSV_FILE = "github_pr_dataset.csv"

# Carregar o CSV de PRs e identificar repositórios coletados
print("Carregando lista de PRs...")
df_prs = pd.read_csv(PR_CSV_FILE)
repos_collected = df_prs["repository"].unique()  # Lista de repositórios já coletados

# Carregar o CSV de repositórios
print("Carregando lista de repositórios...")
df_repos = pd.read_csv(REPO_CSV_FILE)

# Atualizar campo "pr_collected" para repositórios já coletados
df_repos["pr_collected"] = df_repos["owner"] + "/" + df_repos["name"]
df_repos["pr_collected"] = df_repos["pr_collected"].isin(repos_collected)  # Marca como True se já coletado

# Salvar o CSV atualizado
df_repos.to_csv(REPO_CSV_FILE, index=False)
print(f"Atualização concluída! O arquivo '{REPO_CSV_FILE}' foi atualizado.")