from typing import Any, List, Literal
from dataclasses import dataclass, field, asdict, fields, is_dataclass
import numpy as np
from python_to_typescript_interfaces import Interface

@dataclass
class Field(Interface):
    name: str
    data_type: str
    title: str = None
    description: str = None
    sample_values: list[Any] = field(default_factory=list)
    missing_values_percent: float = None
    max_value: Any = None
    min_value: Any = None


@dataclass
class Resource(Interface):
    url: str
    file_format: str
    title: str = None
    fields: list[Field] = field(default_factory=list)
    row_count: int = None
    db_schema: str = None
    status: str = None
    status_selected: bool = False
    status_loaded: bool = False
    loading_error: str = None
    kind: str = 'base'
    content: str = None
    chunks: list[dict] = None

    def merge(self, updates: 'Resource'):
        for field in fields(self):
            field_name = field.name
            updates_value = getattr(updates, field_name, None)

            if bool(updates_value):
                setattr(self, field_name, updates_value)

    async def get_openable_url(self, ctx: str) -> str:
        return self.url


class Embedding(np.ndarray):
    pass


@dataclass
class Dataset(Interface):
    catalogId: str
    id: str
    title: str
    description: str = None
    publisher: str = None
    publisher_description: str = None
    resources: list[Resource] = field(default_factory=list)

    link: str = None

    summary: str = None
    better_title: str = None
    better_description: str = None
    status_embedding: bool = False
    improvement_score: float = None
    status_indexing: bool = False

    versions: dict = field(default_factory=dict)

    def storeId(self):
        return f"{self.catalogId}__{self.id}"
    
    def merge(self, updates: 'Dataset'):
        for field in fields(self):
            field_name = field.name
            self_value = getattr(self, field_name, None)
            updates_value = getattr(updates, field_name, None)

            if field_name == 'resources':
                self_urls = dict((r.url, r) for r in self_value)
                new_resources = []
                for update_r in updates_value:
                    if update_r.url not in self_urls:
                        new_resources.append(update_r)
                    else:
                        new_resources.append(self_urls[update_r.url].merge(update_r))
            else:
                if bool(updates_value):
                    setattr(self, field_name, updates_value)

@dataclass
class DataCatalog(Interface):
    id: str
    kind: str # Literal['CKAN', 'Socrata', 'data.json', 'other', 'website', 'arcgis']
    url: str | List[str]
    title: str
    description: str = None
    language: str = None
    geo: str = None 
    http_headers: dict = field(default_factory=dict)
    ignore_query: bool = None
    fetcher_proxy: str = None


@dataclass
class Deployment(Interface):
    id: str
    owner: str
    catalogIds: List[str]
    agentOrgName: str
    agentCatalogDescriptions: str
    uiLogoHtml: str
    uiDisplayHtml: str
    examples: List[str]