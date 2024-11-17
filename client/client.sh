curl -X POST -F "image=@bird1.jpg" -F "sound=@test.wav" http://localhost:80/upload
curl -X GET http://localhost:80/retrieve
curl -X POST -F "text=Testing" http://localhost:80/respond


curl -X POST -F "image=@bird1.jpg" -F "sound=@test.wav" http://34.30.245.193:80/upload
curl -X GET http://34.30.245.193:80/retrieve
curl -X POST -F "text=Testing" http://34.30.245.193:80/respond