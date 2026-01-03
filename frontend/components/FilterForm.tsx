'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { X } from 'lucide-react';

export interface ColumnFilter {
  id: string;
  column: string;
  operator: string;
  value?: string;
  min?: string;
  max?: string;
  start?: string;
  end?: string;
}

export interface SimpleFilters {
  textSearch?: string;
  dateRangeStart?: string;
  dateRangeEnd?: string;
  numericMin?: string;
  numericMax?: string;
}

interface FilterFormProps {
  columns?: string[];
  columnTypes?: Record<string, 'text' | 'numeric' | 'datetime' | 'boolean'>;
  onSubmit?: (filters: Record<string, any>) => void;
  onClear?: () => void;
}

const OPERATORS = {
  text: [
    { value: 'equals', label: 'Equals' },
    { value: 'contains', label: 'Contains' },
    { value: 'starts_with', label: 'Starts With' },
    { value: 'ends_with', label: 'Ends With' },
    { value: 'in', label: 'In (comma-separated)' },
  ],
  numeric: [
    { value: 'equals', label: 'Equals' },
    { value: '>', label: 'Greater Than' },
    { value: '>=', label: 'Greater Than or Equal' },
    { value: '<', label: 'Less Than' },
    { value: '<=', label: 'Less Than or Equal' },
    { value: 'between', label: 'Between' },
  ],
  datetime: [
    { value: 'equals', label: 'Equals' },
    { value: 'range', label: 'Date Range' },
  ],
  boolean: [
    { value: 'equals', label: 'Equals' },
  ],
};

export function FilterForm({ columns = [], columnTypes = {}, onSubmit, onClear }: FilterFormProps) {
  const [columnFilters, setColumnFilters] = useState<ColumnFilter[]>([]);
  const [simpleFilters, setSimpleFilters] = useState<SimpleFilters>({});

  const addColumnFilter = useCallback(() => {
    const newFilter: ColumnFilter = {
      id: Date.now().toString(),
      column: columns[0] || '',
      operator: 'equals',
      value: '',
    };
    setColumnFilters([...columnFilters, newFilter]);
  }, [columnFilters, columns]);

  const removeColumnFilter = useCallback((id: string) => {
    setColumnFilters(columnFilters.filter((f) => f.id !== id));
  }, [columnFilters]);

  const updateColumnFilter = useCallback((id: string, updates: Partial<ColumnFilter>) => {
    setColumnFilters(columnFilters.map((f) => (f.id === id ? { ...f, ...updates } : f)));
  }, [columnFilters]);

  const handleSubmit = useCallback((e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    const filters: Record<string, any> = {};

    // Add column-based filters
    columnFilters.forEach((filter) => {
      if (filter.column) {
        const filterRule: any = { op: filter.operator };
        
        if (filter.operator === 'between') {
          filterRule.min = filter.min;
          filterRule.max = filter.max;
        } else if (filter.operator === 'range') {
          filterRule.start = filter.start;
          filterRule.end = filter.end;
        } else {
          filterRule.value = filter.value;
        }
        
        filters[filter.column] = filterRule;
      }
    });

    // Add simple filters
    if (simpleFilters.textSearch) {
      filters._textSearch = { op: 'contains', value: simpleFilters.textSearch };
    }
    if (simpleFilters.dateRangeStart || simpleFilters.dateRangeEnd) {
      filters._dateRange = {
        op: 'range',
        start: simpleFilters.dateRangeStart,
        end: simpleFilters.dateRangeEnd,
      };
    }
    if (simpleFilters.numericMin || simpleFilters.numericMax) {
      filters._numericRange = {
        op: 'between',
        min: simpleFilters.numericMin,
        max: simpleFilters.numericMax,
      };
    }

    onSubmit?.(filters);
  }, [columnFilters, simpleFilters, onSubmit]);

  const handleClear = useCallback(() => {
    setColumnFilters([]);
    setSimpleFilters({});
    onClear?.();
  }, [onClear]);

  const getOperatorsForColumn = (column: string) => {
    const type = columnTypes[column] || 'text';
    return OPERATORS[type] || OPERATORS.text;
  };

  const getColumnType = (column: string) => {
    return columnTypes[column] || 'text';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Filter Data</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Simple Filters */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Quick Filters</h3>
            
            <div>
              <Label htmlFor="text-search">Text Search (all columns)</Label>
              <Input
                id="text-search"
                type="text"
                placeholder="Search across all columns..."
                value={simpleFilters.textSearch || ''}
                onChange={(e) => setSimpleFilters({ ...simpleFilters, textSearch: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="date-start">Date Range Start</Label>
                <Input
                  id="date-start"
                  type="date"
                  value={simpleFilters.dateRangeStart || ''}
                  onChange={(e) => setSimpleFilters({ ...simpleFilters, dateRangeStart: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="date-end">Date Range End</Label>
                <Input
                  id="date-end"
                  type="date"
                  value={simpleFilters.dateRangeEnd || ''}
                  onChange={(e) => setSimpleFilters({ ...simpleFilters, dateRangeEnd: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="numeric-min">Numeric Range Min</Label>
                <Input
                  id="numeric-min"
                  type="number"
                  placeholder="Minimum value"
                  value={simpleFilters.numericMin || ''}
                  onChange={(e) => setSimpleFilters({ ...simpleFilters, numericMin: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="numeric-max">Numeric Range Max</Label>
                <Input
                  id="numeric-max"
                  type="number"
                  placeholder="Maximum value"
                  value={simpleFilters.numericMax || ''}
                  onChange={(e) => setSimpleFilters({ ...simpleFilters, numericMax: e.target.value })}
                />
              </div>
            </div>
          </div>

          {/* Column-based Filters */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Column Filters</h3>
              <Button type="button" variant="outline" size="sm" onClick={addColumnFilter}>
                Add Filter
              </Button>
            </div>

            {columnFilters.length === 0 && (
              <p className="text-sm text-muted-foreground">No column filters added. Click "Add Filter" to create one.</p>
            )}

            {columnFilters.map((filter) => {
              const columnType = getColumnType(filter.column);
              const operators = getOperatorsForColumn(filter.column);
              const isBetween = filter.operator === 'between';
              const isRange = filter.operator === 'range';

              return (
                <div key={filter.id} className="p-4 border rounded-lg space-y-3">
                  <div className="flex items-start gap-2">
                    <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div>
                        <Label>Column</Label>
                        <Select
                          value={filter.column}
                          onValueChange={(value) => updateColumnFilter(filter.id, { column: value, operator: 'equals', value: '' })}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {columns.map((col) => (
                              <SelectItem key={col} value={col}>
                                {col} {columnTypes[col] && `(${columnTypes[col]})`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Operator</Label>
                        <Select
                          value={filter.operator}
                          onValueChange={(value) => updateColumnFilter(filter.id, { operator: value, value: '', min: '', max: '', start: '', end: '' })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {operators.map((op) => (
                              <SelectItem key={op.value} value={op.value}>
                                {op.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      {!isBetween && !isRange && (
                        <div>
                          <Label>Value</Label>
                          <Input
                            type={columnType === 'numeric' ? 'number' : columnType === 'datetime' ? 'datetime-local' : 'text'}
                            placeholder="Enter value"
                            value={filter.value || ''}
                            onChange={(e) => updateColumnFilter(filter.id, { value: e.target.value })}
                          />
                        </div>
                      )}

                      {isBetween && (
                        <>
                          <div>
                            <Label>Min</Label>
                            <Input
                              type="number"
                              placeholder="Min value"
                              value={filter.min || ''}
                              onChange={(e) => updateColumnFilter(filter.id, { min: e.target.value })}
                            />
                          </div>
                          <div>
                            <Label>Max</Label>
                            <Input
                              type="number"
                              placeholder="Max value"
                              value={filter.max || ''}
                              onChange={(e) => updateColumnFilter(filter.id, { max: e.target.value })}
                            />
                          </div>
                        </>
                      )}

                      {isRange && (
                        <>
                          <div>
                            <Label>Start</Label>
                            <Input
                              type="datetime-local"
                              value={filter.start || ''}
                              onChange={(e) => updateColumnFilter(filter.id, { start: e.target.value })}
                            />
                          </div>
                          <div>
                            <Label>End</Label>
                            <Input
                              type="datetime-local"
                              value={filter.end || ''}
                              onChange={(e) => updateColumnFilter(filter.id, { end: e.target.value })}
                            />
                          </div>
                        </>
                      )}
                    </div>

                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeColumnFilter(filter.id)}
                      className="mt-6"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4">
            <Button type="submit">Apply Filters</Button>
            <Button type="button" variant="outline" onClick={handleClear}>
              Clear All
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
