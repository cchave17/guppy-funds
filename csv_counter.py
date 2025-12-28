import csv
from itertools import count

FILE_PATH = "/Users/guppy/Downloads/all_amex_10_30_25.csv"


# /Users/guppy/Github/cchavez/guppy-funds/backend/storage/3c1af5c5-f1dd-42a9-9cf3-bb17da1fb5fb.csv
def csv_counter(csv_file_path):
    """Count the number of rows/records in a CSV file."""
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        # Skip header row and count data rows
        next(reader, None)
        row_count = sum(1 for _ in reader)

    return row_count

how_many= count(csv_counter(FILE_PATH))
print(how_many)


