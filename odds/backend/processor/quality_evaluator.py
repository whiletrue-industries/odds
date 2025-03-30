from uuid import uuid4
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
    loaded_resources = [
        r for r in relevant_resources if r.status == 'loaded'
    ]
    tabular_resources = [
        r for r in loaded_resources if r.file_format in TABULAR_FORMATS
    ]
    good_number_of_rows = [
        r for r in tabular_resources if r.row_count and r.row_count > 10
    ]

    num_resources = len(dataset.resources)
    num_possible_resources = len(possible_resources)
    num_relevant_resources = len(relevant_resources)
    num_tabular_resources = len(tabular_resources)
    num_loaded_resources = len(loaded_resources)
    num_good_number_of_rows = len(good_number_of_rows)

    irrelevant_resource_penalty = num_resources - num_possible_resources
    irrelevant_resource_issues = []
    for r in dataset.resources:
        r.quality_issues = []
        if r not in possible_resources:
            issue = {
                'id': str(uuid4()),
                'issue': 'irrelevant_resource',
                'description': f'Possibly unusable resource: {r.title} ({r.file_format})'
            }
            irrelevant_resource_issues.append(issue)
            r.quality_issues.append(issue)
    corrupt_resource_penalty = num_relevant_resources - num_loaded_resources
    corrupt_resource_issues = []
    for r in relevant_resources:
        if r not in loaded_resources:
            issue = {
                'id': str(uuid4()),
                'issue': 'corrupt_resource',
                'description': f'Resource failed to load: {r.title} ({r.loading_error})'
            }
            corrupt_resource_issues.append(issue)
            r.quality_issues.append(issue)
    low_number_of_rows_penalty = num_tabular_resources - num_good_number_of_rows
    low_number_of_rows_issues = []
    for r in tabular_resources:
        if r not in good_number_of_rows:
            issue = {
                'id': str(uuid4()),
                'issue': 'low_number_of_rows',
                'description': f'Resource has very few rows: {r.title} ({r.row_count} rows)'
            }
            low_number_of_rows_issues.append(issue)
            r.quality_issues.append(issue)
    total_penalty = (
        irrelevant_resource_penalty +
        corrupt_resource_penalty +
        low_number_of_rows_penalty
    )
    explanation = f'''irrelevant_resource_penalty: {irrelevant_resource_penalty}
corrupt_resource_penalty: {corrupt_resource_penalty}
low_number_of_rows_penalty: {low_number_of_rows_penalty}
num_resources: {num_resources}
'''
    
    if num_resources > 0:
        total_penalty /= num_resources
    else:
        total_penalty = 0

    explanation += f'resources penalty: {total_penalty}\n'

    # Add penalty if improvement_score > 0
    total_penalty += improvement_score / 100.0
    if improvement_score > 0:
        metadata_can_be_improved_issue = [
            {
                'issue': 'metadata_can_be_improved',
                'description': f'Title & Description could be improved'
            }
        ]
        explanation += f'metadata_can_be_improved: {improvement_score} -> {total_penalty}\n'
    else:
        metadata_can_be_improved_issue = []

    dataset.quality_score = int((2-total_penalty) * 50.0)
    explanation += f'final score: {dataset.quality_score}\n'
    # Normalize the score to be between 0 and 100
    dataset.quality_score = max(0, min(dataset.quality_score, 100))
    dataset_quality_issues = [
        {
            'issue': 'dataset_quality',
            'description': explanation
        }
    ]
    dataset.quality_issues = (
        irrelevant_resource_issues +
        corrupt_resource_issues +
        low_number_of_rows_issues +
        metadata_can_be_improved_issue +
        dataset_quality_issues
    )
