import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Read the dataset
df = pd.read_csv('github_pr_dataset.csv')

# Calculate PR size (total changes)
df['pr_size'] = df['additions'] + df['deletions']

# Calculate analysis time in hours
df['created_at'] = pd.to_datetime(df['created_at'])
df['closed_at'] = pd.to_datetime(df['closed_at'])
df['analysis_time_hours'] = (df['closed_at'] - df['created_at']).dt.total_seconds() / 3600

print("Dataset loaded with", len(df), "pull requests")
print("Summary statistics:")
print(df[['pr_size', 'analysis_time_hours', 'description_length', 'review_count', 
         'comments_count', 'participants_count']].describe())

# Create derived metric for feedback final (assumed as comments_count + participants_count)
df['feedback_metric'] = df['comments_count'] + df['participants_count']

# Define independent variables for analysis
independent_vars = {'Tamanho dos PRs': 'pr_size',
                    'Tempo de análise (horas)': 'analysis_time_hours',
                    'Descrição dos PRs': 'description_length',
                    'Interações nos PRs': 'feedback_metric'}

# Create 'visualization' directory if it doesn't exist
os.makedirs('visualization', exist_ok=True)

# First set of questions: relationship with feedback final
for title, col in independent_vars.items():
    plt.figure(figsize=(8, 6))
    sns.regplot(x=df[col], y=df['feedback_metric'], scatter_kws={'alpha': 0.5})
    # Calculate Spearman correlation
    corr, pval = stats.spearmanr(df[col], df['feedback_metric'])
    plt.title(title + ' vs Feedback Final\nSpearman r = ' + str(round(corr, 2)) + ', p = ' + str(round(pval, 4)))
    plt.xlabel(title)
    plt.ylabel('Feedback Final (comments + participants)')
    plt.tight_layout()
    plt.savefig(f'visualization/feedback_final_{col}.png')  # Save the plot as an image in 'visualization'
    plt.close()

# Second set of questions: relationship with number of revisions (review_count)
for title, col in independent_vars.items():
    plt.figure(figsize=(8, 6))
    sns.regplot(x=df[col], y=df['review_count'], scatter_kws={'alpha': 0.5}, color='orange')
    # Calculate Spearman correlation
    corr, pval = stats.spearmanr(df[col], df['review_count'])
    plt.title(title + ' vs Nº de Revisões\nSpearman r = ' + str(round(corr, 2)) + ', p = ' + str(round(pval, 4)))
    plt.xlabel(title)
    plt.ylabel('Número de Revisões')
    plt.tight_layout()
    plt.savefig(f'visualization/revision_count_{col}.png')  # Save the plot as an image in 'visualization'
    plt.close()

print('Visualizações geradas e salvas na subpasta "visualization".')
