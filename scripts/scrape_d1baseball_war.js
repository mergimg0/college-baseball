/**
 * D1 Baseball WAR Leaderboard Scraper
 *
 * Run in Chrome DevTools console on: https://d1baseball.com/synergy/
 *
 * Extracts: Player, Team, Position, oRAR, oWAR, DRS, dWAR, pRAR, pWAR, WAR
 * Outputs: CSV file download (d1baseball_war_{season}.csv)
 */
(async () => {
    const season = document.querySelector('.war-drs-season')?.value || '2026';
    console.log(`Scraping WAR leaderboard for ${season}...`);

    // Select WAR type and show all entries
    const warSelect = document.querySelector('.war-drs');
    if (warSelect) warSelect.value = 'war';

    // Click "Show All" in the WAR table pagination
    const warTable = document.querySelector('#war-leaderboard-stats');
    if (!warTable) { console.error('WAR table not found. Are you on /synergy/?'); return; }

    const lengthSelect = document.querySelector('#war-leaderboard-stats_length select');
    if (lengthSelect) {
        lengthSelect.value = '-1'; // Show All
        lengthSelect.dispatchEvent(new Event('change'));
        await new Promise(r => setTimeout(r, 2000));
    }

    // Extract headers
    const headerRow = warTable.querySelector('thead tr');
    const headers = [...headerRow.querySelectorAll('th')].map(th => {
        const tooltip = th.querySelector('.tooltip');
        return tooltip ? tooltip.textContent.trim() : th.textContent.trim();
    });
    console.log('Headers:', headers.join(', '));

    // Extract all rows
    const rows = [];
    warTable.querySelectorAll('tbody tr').forEach(tr => {
        const cells = [...tr.querySelectorAll('td')].map(td => {
            const link = td.querySelector('a');
            return (link ? link.textContent : td.textContent).trim();
        });
        if (cells.length > 0 && cells[0] !== '') rows.push(cells);
    });

    console.log(`Extracted ${rows.length} players`);

    // Build CSV
    const csvHeader = headers.join(',');
    const csvRows = rows.map(row =>
        row.map(cell => '"' + cell.replace(/"/g, '""') + '"').join(',')
    );
    const csv = [csvHeader, ...csvRows].join('\n');

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `d1baseball_war_${season}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    console.log(`Done! Downloaded ${rows.length} WAR entries as d1baseball_war_${season}.csv`);
})();
