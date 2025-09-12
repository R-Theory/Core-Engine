import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { factorial, permutation, combination } from '@/lib/logic-utils';

export default function CountingCalculator() {
  const [n, setN] = useState(5);
  const [r, setR] = useState(3);
  const [k, setK] = useState(2);
  
  const [sumRuleA, setSumRuleA] = useState(10);
  const [sumRuleB, setSumRuleB] = useState(15);
  const [productRuleA, setProductRuleA] = useState(4);
  const [productRuleB, setProductRuleB] = useState(6);

  const examples = [
    {
      title: "Arranging Books",
      problem: "In how many ways can 5 different books be arranged on a shelf?",
      solution: "5! = " + factorial(5),
      explanation: "This is a permutation of 5 objects taken all at once."
    },
    {
      title: "Selecting Committee",
      problem: "How many ways can we select 3 people from a group of 8?",
      solution: "C(8,3) = " + combination(8, 3),
      explanation: "This is a combination since order doesn't matter in selection."
    },
    {
      title: "License Plates",
      problem: "How many 3-digit license plates can be formed using digits 0-9?",
      solution: "10 × 10 × 10 = " + (10 * 10 * 10),
      explanation: "Product rule: each position has 10 choices independently."
    },
    {
      title: "Pizza Toppings",
      problem: "A pizza can have pepperoni OR mushrooms OR both. If 20 have pepperoni and 15 have mushrooms, with 8 having both, how many pizzas have at least one topping?",
      solution: "20 + 15 - 8 = " + (20 + 15 - 8),
      explanation: "Inclusion-exclusion principle: |A ∪ B| = |A| + |B| - |A ∩ B|"
    }
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Permutations & Combinations</CardTitle>
            <CardDescription>Calculate P(n,r) and C(n,r)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="n">n (total items)</Label>
                <Input
                  id="n"
                  type="number"
                  value={n}
                  onChange={(e) => setN(parseInt(e.target.value) || 0)}
                  min="0"
                />
              </div>
              <div>
                <Label htmlFor="r">r (items chosen)</Label>
                <Input
                  id="r"
                  type="number"
                  value={r}
                  onChange={(e) => setR(parseInt(e.target.value) || 0)}
                  min="0"
                />
              </div>
            </div>
            
            <Separator />
            
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                <div>
                  <div className="font-medium">Permutation P({n},{r})</div>
                  <div className="text-sm text-gray-600">Order matters</div>
                </div>
                <Badge variant="default" className="text-lg px-3 py-1">
                  {permutation(n, r)}
                </Badge>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <div>
                  <div className="font-medium">Combination C({n},{r})</div>
                  <div className="text-sm text-gray-600">Order doesn't matter</div>
                </div>
                <Badge variant="default" className="text-lg px-3 py-1">
                  {combination(n, r)}
                </Badge>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                <div>
                  <div className="font-medium">Factorial {n}!</div>
                  <div className="text-sm text-gray-600">All arrangements</div>
                </div>
                <Badge variant="default" className="text-lg px-3 py-1">
                  {factorial(n)}
                </Badge>
              </div>
            </div>
            
            <div className="text-xs text-gray-500 space-y-1">
              <div>P(n,r) = n! / (n-r)!</div>
              <div>C(n,r) = n! / (r! × (n-r)!)</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sum & Product Rules</CardTitle>
            <CardDescription>Fundamental counting principles</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-base font-medium">Sum Rule (OR)</Label>
              <div className="text-sm text-gray-600 mb-2">
                If A and B are mutually exclusive events
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label htmlFor="sumA">|A|</Label>
                  <Input
                    id="sumA"
                    type="number"
                    value={sumRuleA}
                    onChange={(e) => setSumRuleA(parseInt(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label htmlFor="sumB">|B|</Label>
                  <Input
                    id="sumB"
                    type="number"
                    value={sumRuleB}
                    onChange={(e) => setSumRuleB(parseInt(e.target.value) || 0)}
                  />
                </div>
              </div>
              <div className="p-3 bg-yellow-50 rounded-lg mt-2">
                <div className="font-medium">|A ∪ B| = |A| + |B| = {sumRuleA + sumRuleB}</div>
              </div>
            </div>
            
            <Separator />
            
            <div>
              <Label className="text-base font-medium">Product Rule (AND)</Label>
              <div className="text-sm text-gray-600 mb-2">
                If A and B are independent events
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label htmlFor="prodA">Choices for A</Label>
                  <Input
                    id="prodA"
                    type="number"
                    value={productRuleA}
                    onChange={(e) => setProductRuleA(parseInt(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label htmlFor="prodB">Choices for B</Label>
                  <Input
                    id="prodB"
                    type="number"
                    value={productRuleB}
                    onChange={(e) => setProductRuleB(parseInt(e.target.value) || 0)}
                  />
                </div>
              </div>
              <div className="p-3 bg-orange-50 rounded-lg mt-2">
                <div className="font-medium">Total ways = {productRuleA} × {productRuleB} = {productRuleA * productRuleB}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Counting Formulas Reference</CardTitle>
          <CardDescription>Essential formulas for counting problems</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="font-medium">Basic Formulas</h4>
              <div className="text-sm space-y-2">
                <div className="p-2 bg-gray-50 rounded">
                  <strong>Factorial:</strong> n! = n × (n-1) × ... × 2 × 1
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <strong>Permutation:</strong> P(n,r) = n!/(n-r)!
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <strong>Combination:</strong> C(n,r) = n!/(r!(n-r)!)
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <strong>Sum Rule:</strong> |A ∪ B| = |A| + |B| (if disjoint)
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <strong>Product Rule:</strong> |A × B| = |A| × |B|
                </div>
              </div>
            </div>
            <div className="space-y-3">
              <h4 className="font-medium">Advanced Formulas</h4>
              <div className="text-sm space-y-2">
                <div className="p-2 bg-gray-50 rounded">
                  <strong>Inclusion-Exclusion:</strong> |A ∪ B| = |A| + |B| - |A ∩ B|
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <strong>Circular Permutation:</strong> (n-1)!
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <strong>With Repetition:</strong> n^r
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <strong>Multiset:</strong> n!/(n₁!n₂!...nₖ!)
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <strong>Stars and Bars:</strong> C(n+k-1, k-1)
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Worked Examples</CardTitle>
          <CardDescription>Step-by-step solutions to common counting problems</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {examples.map((example, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="font-medium text-lg mb-2">{example.title}</div>
                <div className="text-gray-700 mb-2">
                  <strong>Problem:</strong> {example.problem}
                </div>
                <div className="p-3 bg-blue-50 rounded-lg mb-2">
                  <strong>Solution:</strong> {example.solution}
                </div>
                <div className="text-sm text-gray-600">
                  <strong>Explanation:</strong> {example.explanation}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}