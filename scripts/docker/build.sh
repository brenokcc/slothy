CURRENT_DIR=$(pwd)
cd scripts/docker
docker build -t slothy .
cd $CURRENT_DIR
