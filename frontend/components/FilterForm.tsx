'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface FilterFormProps {
  onSubmit?: (filters: Record<string, any>) => void;
}

export function FilterForm({ onSubmit }: FilterFormProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const filters = Object.fromEntries(formData.entries());
    if (onSubmit) {
      onSubmit(filters);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="filter-name">Filter Name</Label>
        <Input id="filter-name" name="filterName" placeholder="Enter filter name" />
      </div>
      <Button type="submit">Apply Filters</Button>
    </form>
  );
}

