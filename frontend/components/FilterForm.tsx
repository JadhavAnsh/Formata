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
  boolean: [{ value: 'equals', label: 'Equals' }],
};

export function FilterForm({
  columns = [],
  columnTypes = {},
  onSubmit,
  onClear,
}: FilterFormProps) {
  const [columnFilters, setColumnFilters] = useState<ColumnFilter[]>([]);
  const [simpleFilters, setSimpleFilters] = useState<SimpleFilters>({});

  const addColumnFilter = () => {
    setColumnFilters((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        column: columns[0] || '',
        operator: 'equals',
        value: '',
      },
    ]);
  };

  const removeColumnFilter = (id: string) => {
    setColumnFilters((prev) => prev.filter((f) => f.id !== id));
  };

  const updateColumnFilter = (id: string, updates: Partial<ColumnFilter>) => {
    setColumnFilters((prev) =>
      prev.map((f) => (f.id === id ? { ...f, ...updates } : f))
    );
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const filters: Record<string, any> = {};

    columnFilters.forEach((filter) => {
      if (!filter.column) return;
      const rule: any = { op: filter.operator };

      if (filter.operator === 'between') {
        rule.min = filter.min;
        rule.max = filter.max;
      } else if (filter.operator === 'range') {
        rule.start = filter.start;
        rule.end = filter.end;
      } else {
        rule.value = filter.value;
      }

      // Support multiple filters on the same column using arrays
      // Multiple filters on same column will use OR logic
      if (filters[filter.column]) {
        // If already exists, convert to array or add to existing array
        if (Array.isArray(filters[filter.column])) {
          filters[filter.column].push(rule);
        } else {
          filters[filter.column] = [filters[filter.column], rule];
        }
      } else {
        filters[filter.column] = rule;
      }
    });

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
  };

  const handleClear = () => {
    setColumnFilters([]);
    setSimpleFilters({});
    onClear?.();
  };

  const getOperators = (column: string) =>
    OPERATORS[columnTypes[column] || 'text'];

  const getColumnType = (column: string) => columnTypes[column] || 'text';

  return (
    <Card>
      <CardHeader>
        <CardTitle>Filter Data</CardTitle>
      </CardHeader>

      <CardContent className="p-6">
        <form onSubmit={handleSubmit} className="space-y-6">

          {/* QUICK FILTERS */}
          <div className="rounded-lg border bg-muted/30 p-4 space-y-4">
            <h3 className="text-sm font-semibold">Quick Filters</h3>

            <div>
              <Label>Text Search</Label>
              <Input
                className="mt-2"
                placeholder="Search across all columns..."
                value={simpleFilters.textSearch || ''}
                onChange={(e) =>
                  setSimpleFilters({ ...simpleFilters, textSearch: e.target.value })
                }
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <Label>Date Start</Label>
                <Input
                  className="mt-2"
                  type="date"
                  value={simpleFilters.dateRangeStart || ''}
                  onChange={(e) =>
                    setSimpleFilters({
                      ...simpleFilters,
                      dateRangeStart: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>Date End</Label>
                <Input
                  className="mt-2"
                  type="date"
                  value={simpleFilters.dateRangeEnd || ''}
                  onChange={(e) =>
                    setSimpleFilters({
                      ...simpleFilters,
                      dateRangeEnd: e.target.value,
                    })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <Label>Numeric Min</Label>
                <Input
                  className="mt-2"
                  type="number"
                  placeholder="Min"
                  value={simpleFilters.numericMin || ''}
                  onChange={(e) =>
                    setSimpleFilters({
                      ...simpleFilters,
                      numericMin: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>Numeric Max</Label>
                <Input
                  className="mt-2"
                  type="number"
                  placeholder="Max"
                  value={simpleFilters.numericMax || ''}
                  onChange={(e) =>
                    setSimpleFilters({
                      ...simpleFilters,
                      numericMax: e.target.value,
                    })
                  }
                />
              </div>
            </div>
          </div>

          {/* COLUMN FILTERS */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Column Filters</h3>
              <Button size="sm" variant="outline" type="button" onClick={addColumnFilter}>
                Add Filter
              </Button>
            </div>

            {columnFilters.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No column filters added.
              </p>
            )}

            {columnFilters.map((filter) => {
              const type = getColumnType(filter.column);
              const isBetween = filter.operator === 'between';
              const isRange = filter.operator === 'range';

              return (
                <div
                  key={filter.id}
                  className="relative rounded-lg border bg-background p-4"
                >
                  <button
                    type="button"
                    onClick={() => removeColumnFilter(filter.id)}
                    className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-4 w-4" />
                  </button>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div>
                      <Label>Column</Label>
                      <Select
                        value={filter.column}
                        onValueChange={(value) =>
                          updateColumnFilter(filter.id, {
                            column: value,
                            operator: 'equals',
                          })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select column" />
                        </SelectTrigger>
                        <SelectContent>
                          {columns.map((col) => (
                            <SelectItem key={col} value={col}>
                              {col}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label>Operator</Label>
                      <Select
                        value={filter.operator}
                        onValueChange={(value) =>
                          updateColumnFilter(filter.id, {
                            operator: value,
                            value: '',
                            min: '',
                            max: '',
                            start: '',
                            end: '',
                          })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {getOperators(filter.column).map((op) => (
                            <SelectItem key={op.value} value={op.value}>
                              {op.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {!isBetween && !isRange && (
                      <div className="md:col-span-2">
                        <Label>Value</Label>
                        <Input
                          type={
                            type === 'numeric'
                              ? 'number'
                              : type === 'datetime'
                              ? 'datetime-local'
                              : 'text'
                          }
                          value={filter.value || ''}
                          onChange={(e) =>
                            updateColumnFilter(filter.id, { value: e.target.value })
                          }
                        />
                      </div>
                    )}

                    {isBetween && (
                      <>
                        <div>
                          <Label>Min</Label>
                          <Input
                            type="number"
                            value={filter.min || ''}
                            onChange={(e) =>
                              updateColumnFilter(filter.id, { min: e.target.value })
                            }
                          />
                        </div>
                        <div>
                          <Label>Max</Label>
                          <Input
                            type="number"
                            value={filter.max || ''}
                            onChange={(e) =>
                              updateColumnFilter(filter.id, { max: e.target.value })
                            }
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
                            onChange={(e) =>
                              updateColumnFilter(filter.id, { start: e.target.value })
                            }
                          />
                        </div>
                        <div>
                          <Label>End</Label>
                          <Input
                            type="datetime-local"
                            value={filter.end || ''}
                            onChange={(e) =>
                              updateColumnFilter(filter.id, { end: e.target.value })
                            }
                          />
                        </div>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* ACTIONS */}
          <div className="flex gap-2 pt-2">
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
