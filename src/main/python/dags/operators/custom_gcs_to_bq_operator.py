import json

from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.utils.decorators import apply_defaults


class CustomGcsToBQOperator(GCSToBigQueryOperator):

    @apply_defaults
    def __init__(self,
                 schema_file: str,
                 *args, **kwargs):

        self.schema_file = schema_file
        with open(self.schema_file) as json_file:
            schema_fields = json.load(json_file)
        super().__init__(schema_fields=schema_fields, *args, **kwargs)



