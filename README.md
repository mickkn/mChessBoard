### Dependencies and installations

Enable I2C in $ sudo raspi-config

apt-get install -y libffi-dev smbus-cffi python3-venv

Use a virtual environment:

cd src/
python3 -m venv venv

source ../src/venv/bin/activate