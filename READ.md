<h1>Docker to hub</h1>

docker build -t nikishka/docxbot:arm64 .
docker build --platform linux/amd64 -t nikishka/docxbot:amd64 .


docker push nikishka/docxbot:arm64
docker push nikishka/docxbot:amd64

docker manifest create nikishka/docxbot:latest nikishka/docxbot:arm64 nikishka/docxbot:amd64

docker manifest push nikishka/docxbot:latest