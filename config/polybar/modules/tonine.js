const DAY = 1000 * 60 * 60 * 24;

const startDate = new Date(2025, 8, 1); 
const endDate = new Date(2026, 8, 1); 
const today = new Date();

const daysFromStart = (today - startDate) / DAY;
const totalDays = (endDate - startDate) / DAY;
const restDays = totalDays - daysFromStart;

const percentageElapsed = (daysFromStart / totalDays) * 100;

const $cur = daysFromStart.toFixed(1);
const $total = Math.round(totalDays);
const $rest = Math.floor(restDays);
const $percentage = percentageElapsed.toFixed(2);

console.log(`${$cur}/${$total} (${$rest}, ${$percentage}%)`);
