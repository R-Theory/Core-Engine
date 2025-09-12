import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { generateTruthTable, LogicalExpression } from '@/lib/logic-utils';

export default function LogicExplorer() {
  const [expression, setExpression] = useState('A AND B');
  const [result, setResult] = useState<LogicalExpression | null>(null);
  const [error, setError] = useState<string>('');

  const handleGenerate = () => {
    try {
      setError('');
      const truthTable = generateTruthTable(expression);
      setResult(truthTable);
    } catch (err) {
      setError('Invalid expression. Please check your syntax.');
      setResult(null);
    }
  };

  const examples = [
    'A AND B',
    'A OR B',
    'NOT A',
    'A AND (B OR C)',
    '(A OR B) AND (C OR D)',
    'NOT (A AND B)',
    'A → B',
    'A ↔ B'
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Expression Input</CardTitle>
            <CardDescription>
              Enter a logical expression using variables A, B, C, D
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="expression">Logical Expression</Label>
              <Input
                id="expression"
                value={expression}
                onChange={(e) => setExpression(e.target.value)}
                placeholder="Enter expression (e.g., A AND B)"
                className="mt-1"
              />
            </div>
            
            <Button onClick={handleGenerate} className="w-full">
              Generate Truth Table
            </Button>
            
            {error && (
              <div className="text-red-600 text-sm">{error}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Operators Guide</CardTitle>
            <CardDescription>Supported logical operators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div><Badge variant="outline">AND</Badge> - Conjunction (∧)</div>
              <div><Badge variant="outline">OR</Badge> - Disjunction (∨)</div>
              <div><Badge variant="outline">NOT</Badge> - Negation (¬)</div>
              <div><Badge variant="outline">→</Badge> - Implication</div>
              <div><Badge variant="outline">↔</Badge> - Biconditional</div>
              <div><Badge variant="outline">( )</Badge> - Parentheses for grouping</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Example Expressions</CardTitle>
          <CardDescription>Click any example to try it</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {examples.map((example, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => setExpression(example)}
              >
                {example}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Truth Table for: {result.expression}</CardTitle>
            <CardDescription>
              Variables: {result.variables.join(', ')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  {result.variables.map(variable => (
                    <TableHead key={variable} className="text-center">
                      {variable}
                    </TableHead>
                  ))}
                  <TableHead className="text-center font-bold">
                    Result
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.truthTable.map((row, index) => (
                  <TableRow key={index}>
                    {result.variables.map(variable => (
                      <TableCell key={variable} className="text-center">
                        <Badge variant={row[variable] ? "default" : "secondary"}>
                          {row[variable] ? 'T' : 'F'}
                        </Badge>
                      </TableCell>
                    ))}
                    <TableCell className="text-center">
                      <Badge variant={row.result ? "default" : "destructive"}>
                        {row.result ? 'T' : 'F'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}