import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

# Carregar os dados
df = pd.read_csv('github_pr_dataset.csv')

# Pré-processamento
df['created_at'] = pd.to_datetime(df['created_at'])
df['closed_at'] = pd.to_datetime(df['closed_at'])
df['analysis_time'] = (df['closed_at'] - df['created_at']).dt.total_seconds() / 3600  # em horas
df['description_length'] = df['description_length'].fillna(0)

# Filtrar PRs com tempo de análise positivo
df = df[df['analysis_time'] > 0]

# Definir métricas
metrics = {
    'size': ['file_count', 'additions', 'deletions'],
    'time': ['analysis_time'],
    'description': ['description_length'],
    'interactions': ['participants_count', 'comments_count']
}

# Funções auxiliares
def calculate_median_by_status(df, metric_columns):
    return df.groupby('pr_state')[metric_columns].median()

def plot_correlation(x, y, xlabel, ylabel, title, filename):
    plt.figure(figsize=(10, 6))
    sns.regplot(x=x, y=y, scatter_kws={'alpha':0.3})
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.savefig(filename)  # Salvar figura como arquivo de imagem
    plt.close()

# Análise por RQ
def analyze_rqs(df):
    results = {}
    
    # RQ05: Tamanho vs Número de revisões
    for metric in metrics['size']:
        corr, pval = stats.spearmanr(df[metric], df['review_count'])
        filename = f'RQ05_{metric}_vs_Numero_de_revisoes.png'
        plot_correlation(df[metric], df['review_count'], f'Tamanho ({metric})', 'Número de revisões', f'RQ05: {metric} vs Número de revisões', filename)
    
    # RQ06: Tempo vs Número de revisões
    for metric in metrics['time']:
        corr, pval = stats.spearmanr(df[metric], df['review_count'])
        filename = f'RQ06_{metric}_vs_Numero_de_revisoes.png'
        plot_correlation(df[metric], df['review_count'], f'Tempo ({metric})', 'Número de revisões', f'RQ06: {metric} vs Número de revisões', filename)
    
    # RQ07: Descrição vs Número de revisões
    for metric in metrics['description']:
        corr, pval = stats.spearmanr(df[metric], df['review_count'])
        filename = f'RQ07_{metric}_vs_Numero_de_revisoes.png'
        plot_correlation(df[metric], df['review_count'], f'Descrição ({metric})', 'Número de revisões', f'RQ07: {metric} vs Número de revisões', filename)
    
    # RQ08: Interações vs Número de revisões
    for metric in metrics['interactions']:
        corr, pval = stats.spearmanr(df[metric], df['review_count'])
        filename = f'RQ08_{metric}_vs_Numero_de_revisoes.png'
        plot_correlation(df[metric], df['review_count'], f'Interações ({metric})', 'Número de revisões', f'RQ08: {metric} vs Número de revisões', filename)
    
    return results

# Executar análise
results = analyze_rqs(df)
