while inotifywait -e close_write ~/.config/polybar/config.ini; do
   ~/config/polybar/bin/launch.sh
done
