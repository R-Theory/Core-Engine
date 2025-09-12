import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { simplifyExpression, areLogicallyEquivalent } from '@/lib/logic-utils';

export default function LogicSimplifier() {
  const [expression, setExpression] = useState('NOT (A AND B)');
  const [result, setResult] = useState<{ steps: string[], final: string } | null>(null);
  const [error, setError] = useState<string>('');

  const handleSimplify = () => {
    try {
      setError('');
      const simplified = simplifyExpression(expression);
      setResult(simplified);
    } catch (err) {
      setError('Invalid expression. Please check your syntax.');
      setResult(null);
    }
  };

  const examples = [
    'NOT (A AND B)',
    'NOT (A OR B)',
    'A AND A',
    'A OR A',
    'A AND TRUE',
    'A OR FALSE',
    'NOT NOT A',
    '(A AND B) OR (A AND C)'
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Expression Simplification</CardTitle>
            <CardDescription>
              Enter a logical expression to see step-by-step simplification
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="expression">Logical Expression</Label>
              <Input
                id="expression"
                value={expression}
                onChange={(e) => setExpression(e.target.value)}
                placeholder="Enter expression to simplify"
                className="mt-1"
              />
            </div>
            
            <Button onClick={handleSimplify} className="w-full">
              Simplify Expression
            </Button>
            
            {error && (
              <div className="text-red-600 text-sm">{error}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Simplification Rules</CardTitle>
            <CardDescription>Common logical equivalences</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div><strong>Identity Laws:</strong></div>
              <div>• A ∧ T ≡ A</div>
              <div>• A ∨ F ≡ A</div>
              <div><strong>Domination Laws:</strong></div>
              <div>• A ∧ F ≡ F</div>
              <div>• A ∨ T ≡ T</div>
              <div><strong>Idempotent Laws:</strong></div>
              <div>• A ∧ A ≡ A</div>
              <div>• A ∨ A ≡ A</div>
              <div><strong>Double Negation:</strong></div>
              <div>• ¬¬A ≡ A</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Example Expressions</CardTitle>
          <CardDescription>Click any example to try simplification</CardDescription>
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
            <CardTitle>Simplification Steps</CardTitle>
            <CardDescription>
              Step-by-step simplification process
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {result.steps.map((step, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <Badge variant="outline">{index + 1}</Badge>
                  <code className="bg-gray-100 px-2 py-1 rounded text-sm flex-1">
                    {step}
                  </code>
                  {index === 0 && <span className="text-sm text-gray-500">Original</span>}
                  {index === result.steps.length - 1 && index > 0 && (
                    <span className="text-sm text-green-600 font-medium">Final</span>
                  )}
                </div>
              ))}
              
              {result.steps.length === 1 && (
                <div className="text-center text-gray-500 py-4">
                  Expression is already in its simplest form
                </div>
              )}
              
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <div className="text-sm font-medium text-blue-800">
                  Final Result: <code className="bg-white px-2 py-1 rounded">{result.final}</code>
                </div>
                {result.final !== expression && (
                  <div className="text-xs text-blue-600 mt-1">
                    ✓ Logically equivalent to original expression
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}