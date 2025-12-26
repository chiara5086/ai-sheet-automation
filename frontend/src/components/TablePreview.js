// TablePreview.js
// Modular component to display sheet preview with colored Price cells
// Colors and logic inspired by Aucto and Scraping Dashboard

import React from 'react';
import { Typography, Box } from '@mui/material';

/**
 * TablePreview
 * @param {Array} headers - Array of column headers
 * @param {Array} rows - Array of row data
 * @param {Object} priceStepMap - Map of row indices to process step names
 * @param {Object} stepColors - Map of process step names to cell colors
 * @param {number} previewCount - Number of rows to preview
 */
export default function TablePreview({ headers, rows, priceStepMap, stepColors, previewCount = 10 }) {
  // Find the index of the Price column (case-insensitive)
  const priceIdx = headers.findIndex(h => h.toLowerCase().includes('price'));

  return (
    <Box sx={{ overflowX: 'auto', my: 3, borderRadius: 2, boxShadow: 1, background: '#fff', maxHeight: '400px', overflowY: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, tableLayout: 'fixed' }}>
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} style={{ 
                border: '1px solid #d0e0f0', 
                padding: 6, 
                background: '#f5f6fa', 
                fontWeight: 700, 
                color: '#1a2746',
                fontSize: 12,
                position: 'sticky',
                top: 0,
                zIndex: 10
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, previewCount).map((row, rIdx) => (
            <tr key={rIdx}>
              {headers.map((_, cIdx) => {
                // Color Price cell based on process step
                let cellStyle = { 
                  border: '1px solid #eee', 
                  padding: 6,
                  maxWidth: '150px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  fontSize: 12
                };
                if (cIdx === priceIdx && row[cIdx]) {
                  const step = priceStepMap[rIdx + 3]; // row 3+ in sheet
                  if (step && stepColors[step]) {
                    cellStyle.background = stepColors[step];
                    cellStyle.fontWeight = 700;
                  }
                }
                const cellValue = row[cIdx] || '';
                // Truncate long text for preview (show first 100 chars)
                const displayValue = typeof cellValue === 'string' && cellValue.length > 100 
                  ? cellValue.substring(0, 100) + '...' 
                  : cellValue;
                return (
                  <td key={cIdx} style={cellStyle} title={cellValue}>
                    {displayValue}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <Typography variant="caption" color="textSecondary" sx={{ ml: 1 }}>
        Showing first {previewCount} rows
      </Typography>
    </Box>
  );
}
