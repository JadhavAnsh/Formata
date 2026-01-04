/**
 * Client-side file parsing utilities (temporary until backend API is ready)
 */

export interface ParsedData {
  records: Array<Record<string, any>>;
  columns: string[];
  totalRows: number;
}

/**
 * Parse CSV file content
 */
export function parseCSV(content: string): ParsedData {
  const lines = content.split('\n').filter(line => line.trim());
  if (lines.length === 0) {
    return { records: [], columns: [], totalRows: 0 };
  }

  // Parse header
  const header = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  
  // Parse rows
  const records: Array<Record<string, any>> = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    // Simple CSV parsing (handles quoted values)
    const values = parseCSVLine(line);
    if (values.length === header.length) {
      const record: Record<string, any> = {};
      header.forEach((col, idx) => {
        const value = values[idx]?.trim().replace(/^"|"$/g, '') || '';
        // Try to convert to number if possible
        const numValue = Number(value);
        if (value !== '' && !isNaN(numValue) && isFinite(numValue)) {
          record[col] = numValue;
        } else {
          record[col] = value;
        }
      });
      records.push(record);
    }
  }

  return {
    records,
    columns: header,
    totalRows: records.length,
  };
}

/**
 * Parse a single CSV line handling quoted values
 */
function parseCSVLine(line: string): string[] {
  const values: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      values.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  
  values.push(current);
  return values;
}

/**
 * Parse JSON file content
 */
export function parseJSON(content: string): ParsedData {
  try {
    const jsonData = JSON.parse(content);
    let records: Array<Record<string, any>> = [];

    // Handle different JSON structures
    if (Array.isArray(jsonData)) {
      records = jsonData;
    } else if (jsonData && typeof jsonData === 'object') {
      // Check for common wrapper keys
      if (jsonData.records && Array.isArray(jsonData.records)) {
        records = jsonData.records;
      } else if (jsonData.data && Array.isArray(jsonData.data)) {
        records = jsonData.data;
      } else if (jsonData.items && Array.isArray(jsonData.items)) {
        records = jsonData.items;
      } else {
        // Single object, wrap in array
        records = [jsonData];
      }
    }

    if (records.length === 0) {
      return { records: [], columns: [], totalRows: 0 };
    }

    // Extract columns from first record
    const columns = Object.keys(records[0]);

    return {
      records,
      columns,
      totalRows: records.length,
    };
  } catch {
    throw new Error('Failed to parse JSON file');
  }
}

/**
 * Parse uploaded file
 */
export async function parseFile(file: File): Promise<ParsedData> {
  const content = await file.text();
  const extension = file.name.split('.').pop()?.toLowerCase();

  if (extension === 'csv') {
    return parseCSV(content);
  } else if (extension === 'json') {
    return parseJSON(content);
  } else {
    throw new Error(`Unsupported file type: ${extension}`);
  }
}

/**
 * Apply filters to data client-side
 * Column keys do NOT start with '_' - only special filters like _textSearch, _dateRange, _numericRange start with '_'
 */
export function applyFiltersClientSide(
  data: Array<Record<string, any>>,
  filters: Record<string, any>
): Array<Record<string, any>> {
  if (!data || data.length === 0 || !filters || Object.keys(filters).length === 0) {
    return data;
  }

  let filtered = [...data];

  // Process all filters - multiple column filters can be applied
  Object.entries(filters).forEach(([key, rule]) => {
    if (!rule || typeof rule !== 'object' || !rule.op) return;

    // Special filters start with '_' (not column names)
    if (key.startsWith('_')) {
      // Handle special filters
      if (key === '_textSearch' && rule.value) {
        // Text search across all columns
        const searchTerm = String(rule.value).toLowerCase();
        filtered = filtered.filter(row => {
          return Object.values(row).some(val => 
            String(val).toLowerCase().includes(searchTerm)
          );
        });
      } else if (key === '_dateRange' && (rule.start || rule.end)) {
        // Date range filter (find first date column)
        if (filtered.length > 0) {
          const dateColumn = Object.keys(filtered[0] || {}).find(col => {
            const sample = filtered[0]?.[col];
            if (typeof sample === 'string') {
              const date = new Date(sample);
              return !isNaN(date.getTime());
            }
            return false;
          });

          if (dateColumn) {
            filtered = filtered.filter(row => {
              const dateValue = new Date(row[dateColumn]);
              if (isNaN(dateValue.getTime())) return false;
              if (rule.start && dateValue < new Date(rule.start)) return false;
              if (rule.end && dateValue > new Date(rule.end)) return false;
              return true;
            });
          }
        }
      } else if (key === '_numericRange' && (rule.min !== undefined || rule.max !== undefined)) {
        // Numeric range filter (find first numeric column)
        if (filtered.length > 0) {
          const numericColumn = Object.keys(filtered[0] || {}).find(col => {
            const sample = filtered[0]?.[col];
            return typeof sample === 'number';
          });

          if (numericColumn) {
            filtered = filtered.filter(row => {
              const numValue = Number(row[numericColumn]);
              if (isNaN(numValue)) return false;
              if (rule.min !== undefined && numValue < Number(rule.min)) return false;
              if (rule.max !== undefined && numValue > Number(rule.max)) return false;
              return true;
            });
          }
        }
      }
    } else {
      // Column-specific filter - key is the column name (doesn't start with '_')
      const column = key;
      
      // Check if column exists in the data (check first row if available)
      if (filtered.length > 0 && filtered[0] && column in filtered[0]) {
        // Support multiple rules for the same column (AND logic - all conditions must be met)
        const rules = Array.isArray(rule) ? rule : [rule];
        
        // Determine column type from first non-null value
        let columnType: 'numeric' | 'datetime' | 'boolean' | 'text' = 'text';
        let sampleValue: any = null;
        
        // Find first non-null value to determine type
        for (const row of filtered) {
          if (row[column] !== null && row[column] !== undefined) {
            sampleValue = row[column];
            break;
          }
        }
        
        if (sampleValue !== null && sampleValue !== undefined) {
          if (typeof sampleValue === 'boolean') {
            columnType = 'boolean';
          } else if (typeof sampleValue === 'number') {
            columnType = 'numeric';
          } else if (typeof sampleValue === 'string') {
            const dateValue = new Date(sampleValue);
            if (!isNaN(dateValue.getTime()) && sampleValue.length > 8) {
              columnType = 'datetime';
            }
          }
        }

        // Apply filters with AND logic - row matches if ALL rules match
        filtered = filtered.filter(row => {
          const value = row[column];
          
          // Handle null/undefined values
          if (value === null || value === undefined) {
            return false; // Exclude null/undefined values by default
          }
          
          // Check if ALL rules match (AND logic)
          return rules.every(ruleItem => {
            if (!ruleItem || typeof ruleItem !== 'object' || !ruleItem.op) {
              return false;
            }
            
            switch (ruleItem.op) {
              case 'equals':
              case '==':
                if (columnType === 'numeric') {
                  return Number(value) === Number(ruleItem.value);
                } else if (columnType === 'boolean') {
                  return Boolean(value) === Boolean(ruleItem.value);
                } else if (columnType === 'datetime') {
                  return new Date(value).getTime() === new Date(ruleItem.value).getTime();
                } else {
                  return String(value) === String(ruleItem.value);
                }
                
              case 'contains':
                return String(value).toLowerCase().includes(String(ruleItem.value).toLowerCase());
                
              case 'starts_with':
                return String(value).toLowerCase().startsWith(String(ruleItem.value).toLowerCase());
                
              case 'ends_with':
                return String(value).toLowerCase().endsWith(String(ruleItem.value).toLowerCase());
                
              case '>':
                if (columnType === 'numeric') {
                  return Number(value) > Number(ruleItem.value);
                } else if (columnType === 'datetime') {
                  return new Date(value).getTime() > new Date(ruleItem.value).getTime();
                }
                return false;
                
              case '>=':
                if (columnType === 'numeric') {
                  return Number(value) >= Number(ruleItem.value);
                } else if (columnType === 'datetime') {
                  return new Date(value).getTime() >= new Date(ruleItem.value).getTime();
                }
                return false;
                
              case '<':
                if (columnType === 'numeric') {
                  return Number(value) < Number(ruleItem.value);
                } else if (columnType === 'datetime') {
                  return new Date(value).getTime() < new Date(ruleItem.value).getTime();
                }
                return false;
                
              case '<=':
                if (columnType === 'numeric') {
                  return Number(value) <= Number(ruleItem.value);
                } else if (columnType === 'datetime') {
                  return new Date(value).getTime() <= new Date(ruleItem.value).getTime();
                }
                return false;
                
              case 'between':
                if (columnType === 'numeric') {
                  const numValue = Number(value);
                  return numValue >= Number(ruleItem.min) && numValue <= Number(ruleItem.max);
                }
                return false;
                
              case 'range':
                if (columnType === 'datetime') {
                  const dateValue = new Date(value);
                  return (!ruleItem.start || dateValue >= new Date(ruleItem.start)) &&
                         (!ruleItem.end || dateValue <= new Date(ruleItem.end));
                }
                return false;
                
              default:
                return false;
            }
          });
        });
      }
    }
  });

  return filtered;
}

