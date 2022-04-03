docker build -t breath-server:latest .

docker run --restart always -d -p 5000:5000 -v /opt/breath-server:/app/data --name breath-server breath-server
