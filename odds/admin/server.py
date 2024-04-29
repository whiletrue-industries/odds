from flask import Flask
from flask_admin import Admin
from flask_admin.model.form import InlineFormAdmin
from flask_admin.contrib.peewee import ModelView
from ..common.db.peewee.models import Dataset, Catalog, Resource
from wtforms.validators import DataRequired
from flask_admin.contrib.peewee.filters import BasePeeweeFilter
from flask import url_for
from markupsafe import Markup

app = Flask(__name__)

# set optional bootswatch theme
app.config['FLASK_ADMIN_SWATCH'] = 'journal'

admin = Admin(app, name='ODDS', template_mode='bootstrap4')

class CatalogView(ModelView):
        ...

class ResourceInlineForm(InlineFormAdmin):
    form_columns = ('url', 'file_format', 'title', 'row_count', 'db_schema', 'status_selected', 'status_loaded', 'loading_error')
    form_label = 'Resource'
    form_args = {
        'url': {
            'label': 'URL',
            'validators': [DataRequired()]
        },
        'file_format': {
            'label': 'Format'
        }
    }

def resource_link_formatter(view, context, model, name):
    # Construct the URL to the ResourceView with the filter for the dataset ID
    target_url = url_for('resource.index_view') + f'?flt1_4={model.id.replace('/', '%2F')}'
    return Markup(f'<a href="{target_url}">{model.title}</a>')

class DatasetView(ModelView):
        can_view_details = True
        column_exclude_list = ['description', 'better_description', 'catalogId', 'publisher_description', 'versions', 'id']
        column_searchable_list = ['title', 'better_title']
        column_filters = ['status_indexing', 'status_embedding']
        inline_models = (ResourceInlineForm(Resource),)
        column_labels = {
            'status_embedding': 'Embedded?',
            'status_indexing': 'Indexed?',
            'resources': 'Resources'
        }
        # column_list = ['title', 'resources']
        column_formatters = {
            'title': resource_link_formatter  # Applying to 'id' column or choose another
        }        


class FilterByDataset(BasePeeweeFilter):
    def apply(self, query, value):
        print('QQQQ', value)
        return query.where(self.column == value)

    def operation(self):
        return 'equals'


class ResourceView(ModelView):
    can_view_details = True
    column_filters = [
        'status_selected', 'status_loaded',
        FilterByDataset(column=Resource.dataset, name='Dataset', options=(lambda: [(dataset.id, dataset.title) for dataset in Dataset.select()])),
    ]
    column_exclude_list = ['url', 'db_schema']
    # column_searchable_list = ['dataset.id']

admin.add_view(CatalogView(Catalog))
admin.add_view(DatasetView(Dataset))
admin.add_view(ResourceView(Resource))

app.run(debug=True)