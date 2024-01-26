
const DAY = 1000 * 60 * 60 * 24;

const today = new Date();
const yearBeginning = new Date(today.getFullYear(), 0, 1);
const september = new Date(today.getFullYear(), 8, 1);

const daysToToday = (today - yearBeginning) / DAY;
const daysToSeptember = (september - yearBeginning) / DAY;
const restDays = daysToSeptember - daysToToday;

const tonine = (1 - restDays / daysToSeptember) * 100;

console.log(`${daysToToday.toFixed(1)}/${Math.round(daysToSeptember)} (${restDays ^ 0}, ${tonine.toFixed(2)}%)`);