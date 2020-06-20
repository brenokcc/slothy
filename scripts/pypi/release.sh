CURRENT_DIR=$(pwd)
BUILD_DIR="/tmp/slothy"
rm -rf $BUILD_DIR
mkdir $BUILD_DIR
cp -r slothy $BUILD_DIR
cp scripts/pypi/setup.py $BUILD_DIR/
cp scripts/pypi/MANIFEST.in $BUILD_DIR/
cd $BUILD_DIR
python setup.py sdist
RELEASE=$(ls $BUILD_DIR/dist/)
echo "twine upload $BUILD_DIR/dist/$RELEASE"
cd $CURRENT_DIR

