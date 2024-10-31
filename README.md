git clone https://github.com/zehevi/clockz
cd clockz
virtualenv .venv
source .venv/bin/activate
python setup.py sdist
pip install ./dist/clock-cli-0.2.tar.gz
clock --help
