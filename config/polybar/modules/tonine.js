
const DAY = 1000 * 60 * 60 * 24;

const today = new Date();
const yearBeginning = new Date(today.getFullYear(), 0, 1);
const september = new Date(today.getFullYear(), 8, 1);

const daysToToday = (today - yearBeginning) / DAY;
const daysToSeptember = (september - yearBeginning) / DAY;
const restDays = daysToSeptember - daysToToday;

const tonine = restDays / daysToSeptember * 100;

console.log(`${restDays ^ 0}/${Math.round(daysToSeptember)} (${daysToToday.toFixed(1)}, ${tonine.toFixed(2)}%)`);