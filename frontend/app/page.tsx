import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function Page() {
  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Formata</h1>
        <p className="text-xl text-muted-foreground mb-8">
          Data Transformation Tool
        </p>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Upload, process, normalize, and convert your data files with ease.
          Transform CSV and JSON files, apply filters, and validate your data.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Upload & Process</CardTitle>
            <CardDescription>
              Upload your data files and process them with filters and normalization
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/ingest">
              <Button className="w-full">Get Started</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>File Converter</CardTitle>
            <CardDescription>
              Convert between CSV and JSON formats quickly and easily
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/convert">
              <Button variant="outline" className="w-full">Convert Files</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}