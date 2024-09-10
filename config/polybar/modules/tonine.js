const DAY = 1000 * 60 * 60 * 24;

const startDate = new Date(2024, 8, 1); 
const endDate = new Date(2025, 8, 1); 
const today = new Date();

const daysFromStart = (today - startDate) / DAY;
const totalDays = (endDate - startDate) / DAY;
const restDays = totalDays - daysFromStart;

const percentageElapsed = (daysFromStart / totalDays) * 100;

const $from = daysFromStart.toFixed(1);
const $total = Math.round(totalDays);
const $rest = restDays ^ 0;
const $percentage = percentageElapsed.toFixed(2);

console.log(`${$from}/${$total} (${$rest}, ${$percentage}%)`);
