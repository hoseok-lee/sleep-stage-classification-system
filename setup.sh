brew install wget
wget -r -N -c -np https://physionet.org/files/slpdb/1.0.0/
python -m pip uninstall matplotlib
pip install -r requirements.txt
echo "Completed set-up"