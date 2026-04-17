/**
 * D1 Baseball DRS Leaderboard Scraper
 *
 * Run in Chrome DevTools console on: https://d1baseball.com/synergy/
 *
 * Extracts: Player, Team, Position, DRS + 14 defensive components
 * Outputs: CSV file download (d1baseball_drs_{season}.csv)
 */
(async () => {
    const season = document.querySelector('.war-drs-season')?.value || '2026';
    console.log(`Scraping DRS leaderboard for ${season}...`);

    // Ensure DRS tab is selected
    const drsSelect = document.querySelector('.war-drs');
    if (drsSelect && drsSelect.value !== 'drs') {
        drsSelect.value = 'drs';
        drsSelect.dispatchEvent(new Event('change'));
        await new Promise(r => setTimeout(r, 3000));
    }

    // Click "Show All" in the DRS table pagination
    const drsTable = document.querySelector('#drs-leaderboard-stats');
    if (!drsTable) { console.error('DRS table not found. Make sure DRS tab is selected.'); return; }

    const lengthSelect = document.querySelector('#drs-leaderboard-stats_length select');
    if (lengthSelect) {
        lengthSelect.value = '-1';
        lengthSelect.dispatchEvent(new Event('change'));
        await new Promise(r => setTimeout(r, 2000));
    }

    // Extract headers
    const headerRow = drsTable.querySelector('thead tr');
    const headers = [...headerRow.querySelectorAll('th')].map(th => {
        const tooltip = th.querySelector('.tooltip');
        // Handle multi-line headers like "Framing\nRuns Saved"
        let text = tooltip ? tooltip.textContent.trim() : th.textContent.trim();
        return text.replace(/\n/g, ' ').replace(/\s+/g, ' ');
    });
    console.log('Headers:', headers.join(', '));

    // Extract all rows
    const rows = [];
    drsTable.querySelectorAll('tbody tr').forEach(tr => {
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
    a.download = `d1baseball_drs_${season}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    console.log(`Done! Downloaded ${rows.length} DRS entries as d1baseball_drs_${season}.csv`);
})();
