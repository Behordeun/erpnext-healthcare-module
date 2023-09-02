import pika, os, json
from dotenv import load_dotenv

load_dotenv()

params = pika.URLParameters(os.environ.get('RABBITMQ_URL'))
params.socket_timeout = 5
params.blocked_connection_timeout = 2000
params.heartbeat = 2000

connection = pika.BlockingConnection(params)

def producer(queue, body):
  try:
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
  except:
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
  channel.queue_declare(queue=queue)

  channel.basic_publish(exchange='', routing_key=queue, body=body)
  print ("[x] Message sent to consumer")
  # connection.close()