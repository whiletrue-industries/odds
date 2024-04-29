from typing import Any
from dataclasses import asdict
import json

from ...common.datatypes import Dataset, Resource
from ...common.store import store

from .frontend_query import FrontendQueryRunner, FrontendQuery

INSTRUCTION = '''
Based on the provided DB schema, please create SQL query which would help determine the following data point: "{datapoint}".
The SQL query must be compatible with SQLite3.
Return the SQL Query only, in validated SQL format (without any other formatting or embellishments).
The query should be prefixed with a single comment explaining how the results of the query should be interpreted.
If no SQL query can be created, return "NO QUERY" only.

Example response:
```sql
-- The average age of all users in the database.
SELECT AVERAGE("Age") from table WHERE "Status" = 'User';
```

Some context about the data:
- Data set name: {dataset_name}
- Data set description: {dataset_description}
- File name: {resource_name}
- Number of records: {num_records}
- Information about the different columns:
{fields}

DB Schema:
{schema}
''' 


class ComposeQuery(FrontendQuery):

    def __init__(self, datapoint: str, resource: Resource, dataset: Dataset):
        super().__init__()
        self.datapoint = datapoint
        self.resource = resource
        self.dataset = dataset

    def prompt(self) -> list[tuple[str, str]]:
        fields = [
            {k:v for k,v in asdict(f).items() if v is not None}
            for f in self.resource.fields
        ]
        fields = [
            f'`{f.pop('name')}` ({f.pop('data_type')}): {json.dumps(f, ensure_ascii=False)}'
            for f in fields
        ]
        if len(fields) > 20:
            fields = fields[:15] + ['...'] + fields[-5:]
        fields = '\n'.join(f'  - {f}' for f in fields)
        dataset_name = self.dataset.better_title
        dataset_description = self.dataset.better_description
        resource_name = self.resource.title or 'Data'
        num_records = self.resource.row_count
        return [
            ('system', 'You are an experienced data analyst and DB master.'),
            ('user', INSTRUCTION.format(
                datapoint=self.datapoint,
                schema=self.resource.db_schema,
                fields=fields,
                dataset_name=dataset_name,
                dataset_description=dataset_description,
                resource_name=resource_name,
                num_records=num_records
            ))
        ]

    def handle_result(self, result: str) -> Any:
        if not result or 'NO QUERY' in result.upper():
            return None, None     
        if result.startswith('```sql'):
            result = result[6:]
        if result.endswith('```'):
            result = result[:-3]
        result = result.strip() 
        explanation = result.split('\n')[0]    
        if explanation.startswith('--'):
            explanation = explanation[2:].strip()
        return (result, explanation) if result else (None, None)
    
    def expects_json(self) -> bool:
        return False

compose_query = FrontendQueryRunner(ComposeQuery)

