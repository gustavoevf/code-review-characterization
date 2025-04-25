import csv
import requests
import os
import time

# Define your GitHub token and API endpoint
GITHUB_TOKEN = 'TOKEN'
API_URL = 'https://api.github.com/graphql'

def fetch_pr_state(owner, repository, number):
    """Fetch the state of the pull request using GitHub GraphQL API."""
    while True:  # Loop until the request succeeds or rate limit resets
        print(f"Fetching PR state for Owner: {owner}, Repository: {repository}, PR Number: {number}...")
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
            repository(owner: $owner, name: $repo) {
                pullRequest(number: $number) {
                    state
                }
            }
        }
        """
        variables = {"owner": owner, "repo": repository, "number": number}
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

        response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=headers)

        if response.status_code == 200:
            rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 1))
            if rate_limit_remaining == 0:
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time()))
                wait_time = reset_time - time.time()
                print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
                time.sleep(max(0, wait_time))
                continue  # Retry after waiting
            data = response.json()
            if 'errors' not in data:
                print(f"Successfully fetched PR state: {data['data']['repository']['pullRequest']['state']}")
                return data['data']['repository']['pullRequest']['state']
            else:
                print("Error in response data:", data['errors'])
                return None
        else:
            if response.status_code == 403 and 'X-RateLimit-Reset' in response.headers:
                reset_time = int(response.headers['X-RateLimit-Reset'])
                wait_time = reset_time - time.time()
                print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
                time.sleep(max(0, wait_time))
                continue  # Retry after waiting
            print(f"Failed to fetch PR state: {response.status_code}, {response.text}")
            return None

def load_completed_rows(output_file):
    """Load rows already processed in the output file."""
    completed_rows = set()
    if os.path.exists(output_file):
        print(f"Reading existing output file: {output_file}...")
        with open(output_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                completed_rows.add((row['repository'], row['number']))
    else:
        print(f"No output file found. Starting fresh.")
    return completed_rows

def update_csv(input_file, output_file):
    """Read the input CSV file and update it while resuming from the last processed row."""
    completed_rows = load_completed_rows(output_file)

    print(f"Reading input CSV file: {input_file}...")
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, open(output_file, 'a', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['pr_state']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        # Write header if the file is empty
        if os.stat(output_file).st_size == 0:
            writer.writeheader()

        for index, row in enumerate(reader):
            repository_full = row['repository']
            number = row['number']

            # Parse the repository field to extract owner and repository
            try:
                owner, repository = repository_full.split('/')
            except ValueError:
                print(f"Invalid repository format in row {index + 1}: {repository_full}. Skipping.")
                continue

            if (repository_full, number) in completed_rows:
                print(f"Skipping row {index + 1}: Repository={repository_full}, PR Number={number} (already processed).")
                continue

            print(f"Processing row {index + 1}: Owner={owner}, Repository={repository}, PR Number={number}...")
            pr_state = fetch_pr_state(owner, repository, int(number))

            row['pr_state'] = pr_state or 'Unknown'

            # Write the processed row to the output file immediately
            writer.writerow(row)
            print(f"Updated row {index + 1} written to {output_file}.")

    print("CSV file update complete!")

# File paths
input_file = 'github_pr_dataset.csv'
output_file = 'github_pr_dataset_state.csv'

print("Starting script execution...")
update_csv(input_file, output_file)
print("Script execution finished!")
