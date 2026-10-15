// Fiction can decorate a simulation but cannot replace its results.
export function fictionFor(dataset, scenario, index, series, sourceHash) {
  if (!dataset || dataset.kind !== 'fiction' || dataset.event_source_sha256 !== sourceHash || !series) return null;
  const row = dataset.cases?.[`${scenario.upperWinner}_${scenario.lowerWinner}_${index}`];
  if (!row || row.input.match_index !== index || JSON.stringify(row.input.series) !== JSON.stringify(series)) return null;
  return row;
}

export function aggregateFictionPlayers(reviews) {
  const players = new Map();
  for (const [index, review] of reviews.entries()) {
    if (!review) continue;
    for (const [id, value] of Object.entries(review.players)) {
      const [team, name] = id.split(':');
      const row = players.get(id) || { id, team, name, sum: 0, appearances: [] };
      row.sum += value.rating;
      row.appearances.push({ index, rating: value.rating, comment: value.comment });
      players.set(id, row);
    }
  }
  return [...players.values()].map(row => ({ ...row, rating: row.sum / row.appearances.length })).sort((a, b) => b.rating - a.rating || a.id.localeCompare(b.id));
}
