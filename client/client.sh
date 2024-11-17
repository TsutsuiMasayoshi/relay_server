curl -X POST -F "image=@bird1.png" -F "text=hello" http://localhost:80/upload
curl -X POST -F "text=world" http://localhost:80/respond
