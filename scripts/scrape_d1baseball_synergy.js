/**
 * D1 Baseball Synergy Plate Discipline Scraper
 *
 * Run in Chrome DevTools console on: https://d1baseball.com/synergy/
 *
 * Iterates through ALL metric × pitch type combinations for batting and pitching.
 * Batting metrics:  Contact%, Z-Contact%, Whiff%, Chase%  (4)
 * Pitching metrics: Strike%, Chase%, Whiff%, Z-Contact%, Zone%, Shadow Zone%  (6)
 * Pitch types:      All, Fastball, Slider, Changeup, Curveball, Cutter  (6)
 * Total AJAX calls: (4 × 6) + (6 × 6) = 60
 *
 * Outputs: Single CSV with all combinations (d1baseball_synergy_{season}.csv)
 * Format:  Player, Team, Season, Type, PitchType, Metric, Value, Rank
 */
(async () => {
    const season = document.querySelector('.synergy-season')?.value || '2026';
    const ajaxUrl = '/wp-admin/admin-ajax.php';
    const allRows = [];
    const delay = ms => new Promise(r => setTimeout(r, ms));

    const battingMetrics = [
        { value: 'contact_pct', label: 'Contact%' },
        { value: 'z_contact_pct', label: 'Z-Contact%' },
        { value: 'whiff_pct', label: 'Whiff%' },
        { value: 'chase_pct', label: 'Chase%' },
    ];

    const pitchingMetrics = [
        { value: 'strike_pct', label: 'Strike%' },
        { value: 'chase_pct', label: 'Chase%' },
        { value: 'whiff_pct', label: 'Whiff%' },
        { value: 'z_contact_pct', label: 'Z-Contact%' },
        { value: 'zone_pct', label: 'Zone%' },
        { value: 'shadow_zone_pct', label: 'Shadow Zone%' },
    ];

    const pitchTypes = ['all', 'fastball', 'slider', 'changeup', 'curveball', 'cutter'];

    async function fetchLeaderboard(type, metric, pitchType, minPitches) {
        const params = new URLSearchParams({
            action: 'd1_synergy_leaderboard',
            type: type,
            season: season,
            pitch_type: pitchType,
            metric: metric.value,
            pitches: String(minPitches),
        });

        const response = await fetch(ajaxUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params.toString(),
        });
        return await response.text();
    }

    function parseTableHtml(html, type, metric, pitchType) {
        const parser = new DOMParser();
        const doc = parser.parseFromString('<table>' + html + '</table>', 'text/html');
        const rows = doc.querySelectorAll('tr');
        const entries = [];

        rows.forEach(tr => {
            const cells = [...tr.querySelectorAll('td')].map(td => {
                const link = td.querySelector('a');
                return (link ? link.textContent : td.textContent).trim();
            });
            // Expected: [Rank, Player, Team, MetricValue]
            if (cells.length >= 4 && cells[0] !== '') {
                entries.push({
                    Player: cells[1],
                    Team: cells[2],
                    Season: season,
                    Type: type,
                    PitchType: pitchType,
                    Metric: metric.label,
                    Value: cells[3],
                    Rank: cells[0],
                });
            }
        });
        return entries;
    }

    // Scrape batting metrics
    const battingCombos = battingMetrics.length * pitchTypes.length;
    let done = 0;
    console.log(`Scraping ${battingCombos} batting combinations...`);

    for (const metric of battingMetrics) {
        for (const pt of pitchTypes) {
            const minPitches = (pt === 'all') ? 150 : 50;
            try {
                const html = await fetchLeaderboard('batting', metric, pt, minPitches);
                const entries = parseTableHtml(html, 'batting', metric, pt);
                allRows.push(...entries);
                done++;
                console.log(`  [${done}/${battingCombos + pitchingMetrics.length * pitchTypes.length}] batting/${metric.label}/${pt}: ${entries.length} players`);
            } catch (e) {
                console.warn(`  Failed: batting/${metric.label}/${pt}:`, e.message);
            }
            await delay(500); // Rate limit
        }
    }

    // Scrape pitching metrics
    const pitchingCombos = pitchingMetrics.length * pitchTypes.length;
    console.log(`Scraping ${pitchingCombos} pitching combinations...`);

    for (const metric of pitchingMetrics) {
        for (const pt of pitchTypes) {
            const minPitches = (pt === 'all') ? 150 : 50;
            try {
                const html = await fetchLeaderboard('pitching', metric, pt, minPitches);
                const entries = parseTableHtml(html, 'pitching', metric, pt);
                allRows.push(...entries);
                done++;
                console.log(`  [${done}/${battingCombos + pitchingCombos}] pitching/${metric.label}/${pt}: ${entries.length} players`);
            } catch (e) {
                console.warn(`  Failed: pitching/${metric.label}/${pt}:`, e.message);
            }
            await delay(500);
        }
    }

    console.log(`\nTotal: ${allRows.length} entries across ${done} combinations`);

    // Build CSV
    const csvHeaders = 'Player,Team,Season,Type,PitchType,Metric,Value,Rank';
    const csvRows = allRows.map(r =>
        [r.Player, r.Team, r.Season, r.Type, r.PitchType, r.Metric, r.Value, r.Rank]
            .map(v => '"' + String(v).replace(/"/g, '""') + '"')
            .join(',')
    );
    const csv = [csvHeaders, ...csvRows].join('\n');

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `d1baseball_synergy_${season}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    console.log(`\nDone! Downloaded d1baseball_synergy_${season}.csv (${allRows.length} rows)`);
})();
