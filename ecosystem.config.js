module.exports = {
  apps : [{
    name: 'Resource Created Consumer',
    script: './lafia/api/services/brokers/consumers/consumer.py',
    autorestart: true,
    interpreter: 'python3',
    instances: 4,
    max_memory_restart: '1G',
  }, {
    script: './lafia/api/services/brokers/consumers/consumer.py',
    watch: ['./service-worker']
  }]
};
