import csv
from typing import List
import sys


def detect_delimiter(file_path: str) -> str:
    """
    Detect the delimiter used in a CSV file.

    :param file_path: Path to the CSV file.
    :return: Detected delimiter.
    """
    with open(file_path, 'r') as file:
        line = file.readline()

    delimiters = [',', '\t', ';', ' ']
    delimiter_counts = {delim: line.count(delim) for delim in delimiters}

    # Return the delimiter with the highest count in the first line.
    return max(delimiter_counts, key=delimiter_counts.get)


def find_header_row(file_path: str) -> List[str]:
    """
    Identify the header row in the CSV file based on the maximum number of columns.

    :param file_path: Path to the CSV file.
    :return: List of header column names.
    """
    max_columns = 0
    header_row = []
    delimiter = detect_delimiter(file_path)

    with open(file_path, 'r') as file:
        reader = csv.reader(file, delimiter=delimiter)
        for row in reader:
            if len([x for x in row if x != ""]) > max_columns:
                max_columns = len([x for x in row if x != ""])
                header_row = row
    return header_row


def infer_data_type(value: str) -> str:
    """
    Infer the SQLite data type of a value.

    :param value: The value to infer the data type for.
    :return: Either "INTEGER", "REAL", or "TEXT".
    """
    try:
        int(value)
        return "INTEGER"
    except ValueError:
        try:
            float(value)
            return "REAL"
        except ValueError:
            return "TEXT"


def infer_column_types(file_path: str, header: List[str]) -> List[str]:
    """
    Infer the SQLite data type for each column based on sample data.

    :param file_path: Path to the CSV file.
    :param header: List of header column names.
    :return: List of inferred data types ("INTEGER", "REAL", or "TEXT").
    """
    column_types = ["TEXT"] * len(header)  # default to TEXT
    sample_size = 5  # number of rows to sample for type inference

    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            # Skip to header
            if row == header:
                break

        # Infer types based on the next rows
        for _ in range(sample_size):
            row = next(reader, None)
            if not row:
                break

            for index, value in enumerate(row):
                inferred_type = infer_data_type(value)
                if column_types[index] == "TEXT" and (inferred_type == "REAL" or inferred_type == "INTEGER"):
                    column_types[index] = inferred_type
                elif column_types[index] == "INTEGER" and inferred_type == "REAL":
                    column_types[index] = "REAL"
                elif inferred_type == "TEXT":
                    column_types[index] = "TEXT"

    return column_types


def generate_sqlite_schema(header: List[str], column_types: List[str], table_name: str = 'csv_table') -> str:
    """
    Generate an SQLite schema based on headers and their inferred data types.

    :param header: List of header column names.
    :param column_types: List of inferred data types.
    :param table_name: Desired name for the SQLite table.
    :return: SQLite schema as a string.
    """
    columns = ['"' + col + '"' + " " + ctype for col,
               ctype in zip(header, column_types)]
    schema = f"CREATE TABLE {table_name} ({', '.join(columns)});"
    return schema


def main(filepath: str, table_name: str = 'csv_table'):
    header = find_header_row(filepath)
    column_types = infer_column_types(filepath, header)
    schema = generate_sqlite_schema(header, column_types, table_name)
    print(schema)
    return schema


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sqlite_scheme_generator.py <path_to_csv_file> <table_name>")
        sys.exit(1)
    elif len(sys.argv) == 2:
        main(filepath=sys.argv[1])
    elif len(sys.argv) == 3:
        main(filepath=sys.argv[1], table_name=sys.argv[2])
