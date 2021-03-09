from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.decorators import apply_defaults
class ExtractDataOperator(BaseOperator):

    @apply_defaults
    def __init__(self,
                 postgres_conn_id: str,
                 get_batch_task_id: str,
                 query: str,
                 *args, **kwargs):
        self.conn_id = postgres_conn_id
        self.get_batch_task_id = get_batch_task_id
        self.query = query
        super().__init__(*args, **kwargs)

    def execute(self, context):
        # request = "select * from users"
        request = self.query
        # pg_hook = PostgresHook('postgres_bluepi')
        pg_hook = PostgresHook(self.conn_id)
        connection = pg_hook.get_conn()
        cursor = connection.cursor()
        cursor.execute(request)
        sources = cursor.fetchall()
        for source in sources:
            print(f'source type : {type(source)}')
            print(f'Source : {source[0]} - activated : {source[1]} full :  {str(sources)}')
        print(type(sources))
        return sources

    def _to_json(self):

        pass
