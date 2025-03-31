// Generated using python-to-typescript-interfaces.
// See https://github.com/NalyzeSolutions/python_to_typescript_interfaces

export interface Field {
    name: string;
    data_type: string;
    title: string;
    description: string;
    sample_values: Array<any>;
    missing_values_percent: number;
    max_value: any;
    min_value: any;
}

export interface Resource {
    url: string;
    file_format: string;
    title: string;
    fields: Array<Field>;
    row_count: number;
    db_schema: string;
    status: string;
    status_selected: boolean;
    status_loaded: boolean;
    loading_error: string;
    kind: string;
    content: string;
    quality_issues: {issue: string, description: string}[];
    chunks: Array<Record<any, any>>;
}

export interface Dataset {
    catalogId: string;
    id: string;
    title: string;
    description: string;
    publisher: string;
    publisher_description: string;
    resources: Array<Resource>;
    link: string;
    summary: string;
    better_title: string;
    better_description: string;
    status_embedding: boolean;
    improvement_score: number;
    quality_score: number;
    quality_issues: {issue: string, description: string}[];
    status_indexing: boolean;
    versions: Record<any, any>;
}

export interface DataCatalog {
    id: string;
    kind: string;
    url: string | string[];
    title: string;
    description: string;
    language: string;
    geo: string;
    http_headers: Record<any, any>;
    ignore_query: boolean;
    fetcher_proxy: string;

    deployment: Deployment;
}

export interface Deployment {
    id: string;
    catalogIds: Array<string>;
    agentOrgName: string;
    agentCatalogDescriptions: string;
    uiLogoHtml: string;
    uiDisplayHtml: string;
    examples: Array<string>;
}
