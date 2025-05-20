docker build -t breath-server:latest .
docker run --restart always -d -p 80:80 --ulimit nofile=65536:65536 -v /opt/breath-server:/app/data --name breath-server breath-server
