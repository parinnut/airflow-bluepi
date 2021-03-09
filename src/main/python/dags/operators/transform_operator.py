# from airflow.models import BaseOperator
# # from airflow.utils.decorators import apply_defaults
# #
# #
# # class TransformDataOperator(BaseOperator):
# #
# #     @apply_defaults
# #     def __init__(self,
# #                  get_batch_task_id: str,
# #                  query: str,
# #                  column: dict,
# #                  *args, **kwargs):
# #         self.conn_id = postgres_conn_id
# #         self.get_batch_task_id = get_batch_task_id
# #         self.query = query
# #         super().__init__(*args, **kwargs)