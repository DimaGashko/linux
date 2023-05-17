while inotifywait -e close_write ~/config/dunst/dunstrc; do
   killall dunst

   notify-send "Lorem ipsum" "Dolor sit amet consectetur adipisicing elit"
   notify-send "Lorem ipsum, dolor sit amet consectetur adipisicing elit" "Lorem ipsum, dolor sit amet consectetur adipisicing elit. Officiis vel deserunt."
   notify-send "Lorem ipsum dolor sit" "Lorem ipsum, dolor sit amet consectetur adipisicing elit. Officiis vel deserunt."
   notify-send -u low "Lorem ipsum | Low" "Lorem ipsum, dolor sit amet consectetur adipisicing elit"
   notify-send -u normal "Lorem ipsum | Normal" "Lorem ipsum, dolor sit amet consectetur adipisicing elit"
   notify-send -u critical "Lorem ipsum | Critical" "Lorem ipsum, dolor sit amet consectetur adipisicing elit"

   notify-send -a "Firefox" "Lorem ipsum Giggster" "Lorem ipsum, dolor sit amet consectetur adipi sicing elit"

   notify-send -i firefox "Lorem ipsum" "Dolor sit amet consectetur adipi sicing elit"

   dunstify -h int:value:34 "Dunstify progress bar" "Dolor sit amet consectetur adipisicing elit"
done

# Lorem ipsum, dolor sit amet consectetur adipisicing elit. Officiis vel deserunt quo ipsa! Veritatis porro ipsa minima consectetur numquam eos temporibus explicabo non nostrum ullam. Quasi suscipit necessitatibus molestiae delectus nihil? Nihil modi a praesentium et voluptatum. Aut vel laudantium veniam odit voluptate esse commodi a? Officia, veniam? Praesentium, id.
