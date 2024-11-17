curl -X POST -F "image=@bird1.jpg" -F "sound=@test.wav" http://localhost:80/upload
curl -X POST -F "text=Testing" http://localhost:80/respond
