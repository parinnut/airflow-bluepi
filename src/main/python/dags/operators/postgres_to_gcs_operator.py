from airflow.models import BaseOperator
from airflow.providers.google.cloud.transfers.postgres_to_gcs import PostgresToGCSOperator
from airflow.utils.decorators import apply_defaults


class PostgresToGcsCustomOperator(BaseOperator):

    @apply_defaults
    def __init__(self,
                 get_batch_task_id: str,
                 sql: str,
                 bucket,
                 filename,
                 postgres_conn_id: str,
                 schema_filename=None,
                 approx_max_file_size_bytes=1900000000,
                 google_cloud_storage_conn_id='google_cloud_default',
                 *args, **kwargs):
        self.conn_id = postgres_conn_id
        self.get_batch_task_id = get_batch_task_id
        self.sql = sql
        self.bucket = bucket
        self.filename = filename
        self.schema_filename = schema_filename
        self.postgres_conn_id = postgres_conn_id
        self.approx_max_file_size_bytes = approx_max_file_size_bytes
        self.google_cloud_storage_conn_id = google_cloud_storage_conn_id
        super().__init__(*args, **kwargs)

    def execute(self, context):

        ptg = PostgresToGCSOperator(task_id="load_to_gcs",sql=self.sql,
                              bucket=self.bucket,
                              filename=self.filename,
                              postgres_conn_id=self.postgres_conn_id,
                              gcp_conn_id=self.google_cloud_storage_conn_id,export_format='csv')

        cursor = ptg.query()

        sources = cursor.fetchall()
        for source in sources:
            print(f'source type : {type(source)}')
            print(f'Source : {source[0]} - activated : {source[1]} full :  {str(sources)}')
        print(type(sources))

        # ptg.convert_type(sources)

        return sources