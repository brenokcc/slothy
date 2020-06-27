cd scripts/nodejs
docker run -it --rm --name slothy-nodejs -v "$PWD":/var/ -w /tmp node:alpine sh -c 'cp /var/test.js . && npm install slothy-nodejs && node test.js'