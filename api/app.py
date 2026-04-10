from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from prometheus_flask_exporter import PrometheusMetrics
import redis
import os
import socket
import datetime
import json
from celery import Celery

app = Flask(__name__)

# Конфигурация из переменных окружения
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    decode_responses=True
)

# Prometheus метрики
metrics = PrometheusMetrics(app)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    path = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat(),
            'path': self.path
        }

# Создание таблиц при старте
with app.app_context():
    db.create_all()

# ---------- Celery ----------
def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672//'),
        backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)

@celery.task
def sample_task():
    """Пример задачи для демонстрации работы очереди"""
    return "Task executed"

@app.route('/celery-test')
def celery_test():
    """Тестовый эндпоинт для запуска задачи"""
    result = sample_task.delay()
    return jsonify({'task_id': result.id, 'status': 'queued'})
# -----------------------------

@app.route('/')
def home():
    # Запись визита
    visit = Visit(
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        path='/'
    )
    db.session.add(visit)
    db.session.commit()
    redis_client.incr('visits:total')
    redis_client.lpush('visits:recent', json.dumps({
        'ip': request.remote_addr,
        'time': datetime.datetime.now().isoformat()
    }))
    redis_client.ltrim('visits:recent', 0, 99)

    return jsonify({
        'service': 'API Service',
        'hostname': socket.gethostname(),
        'timestamp': datetime.datetime.now().isoformat(),
        'message': ' text312',
        'stats': {
            'total_visits': redis_client.get('visits:total') or 0,
            'db_visits': Visit.query.count()
        }
    })

@app.route('/health')
def health():
    status = {'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat(), 'services': {}}
    try:
        db.session.execute(text('SELECT 1'))
        status['services']['postgresql'] = 'ok'
    except Exception as e:
        status['services']['postgresql'] = f'error: {str(e)}'
        status['status'] = 'degraded'
    try:
        redis_client.ping()
        status['services']['redis'] = 'ok'
    except Exception as e:
        status['services']['redis'] = f'error: {str(e)}'
        status['status'] = 'degraded'
    return jsonify(status)

@app.route('/visits')
def get_visits():
    limit = request.args.get('limit', 10, type=int)
    db_visits = Visit.query.order_by(Visit.timestamp.desc()).limit(limit).all()
    recent_visits = redis_client.lrange('visits:recent', 0, limit-1)
    recent_visits = [json.loads(v) for v in recent_visits]
    return jsonify({
        'total_visits': redis_client.get('visits:total') or 0,
        'db_visits_count': Visit.query.count(),
        'recent_db_visits': [v.to_dict() for v in db_visits],
        'recent_redis_visits': recent_visits
    })

@app.route('/cache/<key>')
def get_cache(key):
    value = redis_client.get(f'cache:{key}')
    if value:
        return jsonify({'key': key, 'value': value, 'source': 'redis'})
    return jsonify({'error': 'Key not found'}), 404

@app.route('/cache/<key>', methods=['POST'])
def set_cache(key):
    data = request.get_json()
    value = data.get('value')
    ttl = data.get('ttl', 3600)
    if not value:
        return jsonify({'error': 'Value is required'}), 400
    redis_client.setex(f'cache:{key}', ttl, value)
    return jsonify({'key': key, 'value': value, 'ttl': ttl})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
# TEST HOT RELOAD
# test webhook
