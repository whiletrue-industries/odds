import math
from ...backend.settings import ALLOWED_FORMATS, TABULAR_FORMATS, UNPROCESSABLE_DOCUMENT_FORMATS
from ...common.datatypes import Dataset


def evaluate_quality(dataset: Dataset):
    # Plan for Quality score:
    # - Penalize resources that are not in ALLOWED_FORMATS or UNPROCESSABLE_DOCUMENT_FORMATS
    # - Of the rest, penalize resources that are not loaded
    # - Of the rest, penalize resources that have few rows
    # - Normalize the to (#resources / log(1 + #resources))
    # - Add penalty if improvement_score > 0 (100 is the worst score)

    improvement_score = dataset.improvement_score or 100
    possible_resources = [
        r for r in dataset.resources if r.file_format in ALLOWED_FORMATS + UNPROCESSABLE_DOCUMENT_FORMATS
    ]
    relevant_resources = [
        r for r in possible_resources if r.file_format in ALLOWED_FORMATS
    ]
    tabular_resources = [
        r for r in relevant_resources if r.file_format in TABULAR_FORMATS
    ]
    loaded_resources = [
        r for r in relevant_resources if r.status == 'loaded'
    ]
    good_number_of_rows = [
        r for r in loaded_resources if r.row_count > 10
    ]

    num_resources = len(relevant_resources)
    num_possible_resources = len(possible_resources)
    num_relevant_resources = len(relevant_resources)
    num_tabular_resources = len(tabular_resources)
    num_loaded_resources = len(loaded_resources)
    num_good_number_of_rows = len(good_number_of_rows)

    irrelevant_resource_penalty = num_resources - num_possible_resources
    irrelevant_resource_issues = [
        {
            'issue': 'irrelevant_resource',
            'description': f'Possibly unusable resource: {r.title} ({r.file_format})'
        }
        for r in dataset.resources
        if r not in possible_resources
    ]
    loaded_resource_penalty = num_relevant_resources - num_loaded_resources
    loaded_resource_issues = [
        {
            'issue': 'corrupt_resource',
            'description': f'Resource failed to load: {r.title} ({r.loading_error})'
        }
        for r in relevant_resources
        if r not in loaded_resources
    ]
    good_number_of_rows_penalty = num_tabular_resources - num_good_number_of_rows
    good_number_of_rows_issues = [
        {
            'issue': 'low_number_of_rows',
            'description': f'Resource has very few rows: {r.title} ({r.row_count} rows)'
        }
        for r in loaded_resources
        if r not in good_number_of_rows
    ]

    total_penalty = (
        irrelevant_resource_penalty +
        loaded_resource_penalty +
        good_number_of_rows_penalty
    )
    if num_resources > 0:
        total_penalty /= num_resources
        total_penalty *= math.log(1 + num_resources)
    else:
        total_penalty = 0

    # Add penalty if improvement_score > 0
    total_penalty += improvement_score / 20
    if improvement_score > 0:
        metadata_can_be_improved_issue = [
            {
                'issue': 'metadata_can_be_improved',
                'description': f'Title & Description could be improved'
            }
        ]
    else:
        metadata_can_be_improved_issue = []
    
    dataset.quality_score = math.exp(-total_penalty) * 100
    dataset.quality_issues = (
        irrelevant_resource_issues +
        loaded_resource_issues +
        good_number_of_rows_issues +
        metadata_can_be_improved_issue
    )
