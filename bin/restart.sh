cd /home/pi/Desktop/weather-station
pkill -9 -f main.py

sleep 5

nohup python main.py &