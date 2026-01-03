'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface NormalizationFormProps {
  onSubmit?: (options: Record<string, any>) => void;
}

export function NormalizationForm({ onSubmit }: NormalizationFormProps) {
  const [typeConversion, setTypeConversion] = useState<string>('auto');

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const options = { typeConversion };
    if (onSubmit) {
      onSubmit(options);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="type-conversion">Type Conversion</Label>
        <Select value={typeConversion} onValueChange={setTypeConversion}>
          <SelectTrigger id="type-conversion" className="w-full">
            <SelectValue placeholder="Select conversion type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto">Auto-detect</SelectItem>
            <SelectItem value="string">String</SelectItem>
            <SelectItem value="number">Number</SelectItem>
            <SelectItem value="date">Date</SelectItem>
            <SelectItem value="boolean">Boolean</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Button type="submit">Apply Normalization</Button>
    </form>
  );
}

