#!/bin/bash

# Создаем и используем новый builder
docker buildx create --name mybuilder --use

# Собираем и публикуем образ для обеих платформ
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t nikishka/docxbot-bot:latest \
  --push \
  . 