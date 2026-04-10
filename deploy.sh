#!/bin/bash
set -e

REGISTRY_USER="botsman01"
VERSION=${1:-$(date +%Y%m%d-%H%M%S)}   # версия по умолчанию – штамп времени

echo "=== Сборка образов ==="
docker compose build api nginx

echo "=== Тегирование ==="
docker tag docker-lab-compose-api:latest $REGISTRY_USER/student-app-api:$VERSION
docker tag docker-lab-compose-api:latest $REGISTRY_USER/student-app-api:latest
docker tag docker-lab-compose-nginx:latest $REGISTRY_USER/student-app-nginx:$VERSION
docker tag docker-lab-compose-nginx:latest $REGISTRY_USER/student-app-nginx:latest

echo "=== Публикация в Docker Hub ==="
docker push $REGISTRY_USER/student-app-api:$VERSION
docker push $REGISTRY_USER/student-app-api:latest
docker push $REGISTRY_USER/student-app-nginx:$VERSION
docker push $REGISTRY_USER/student-app-nginx:latest

echo "=== Деплой (перезапуск стека) ==="
docker compose down
docker compose up -d

echo "✅ Готово. Версия $VERSION опубликована и развёрнута."
