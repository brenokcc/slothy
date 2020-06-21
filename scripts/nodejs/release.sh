CURRENT_DIR=$(pwd)
BUILD_DIR="/tmp/slothy"
rm -rf $BUILD_DIR
mkdir $BUILD_DIR
cp slothy/test/frontend/static/js/slothy.js /tmp/slothy
cp scripts/nodejs/package.json /tmp/slothy
cd $BUILD_DIR
npm publish --access public
cd $CURRENT_DIR