from kombu.serialization import register
from .decoders import data_dumps, data_loads


register('myjson', data_dumps, data_loads,
         content_type='application/x-myjson',
         content_encoding='utf-8')

# Tell celery to use your new serializer:
accept_content = ['myjson']
task_serializer = 'myjson'
result_serializer = 'myjson'