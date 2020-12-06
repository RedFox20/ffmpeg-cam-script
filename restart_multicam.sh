sudo systemctl stop multicam

sudo cp multicam.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl start multicam
sudo systemctl status multicam

