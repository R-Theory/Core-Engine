import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

interface SetData {
  name: string;
  elements: string[];
}

export default function SetExplorer() {
  const [setA, setSetA] = useState<SetData>({ name: 'A', elements: ['1', '2', '3', '4'] });
  const [setB, setSetB] = useState<SetData>({ name: 'B', elements: ['3', '4', '5', '6'] });
  const [setC, setSetC] = useState<SetData>({ name: 'C', elements: ['2', '4', '6', '8'] });
  const [universe, setUniverse] = useState<string[]>(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']);
  
  const [inputA, setInputA] = useState('1, 2, 3, 4');
  const [inputB, setInputB] = useState('3, 4, 5, 6');
  const [inputC, setInputC] = useState('2, 4, 6, 8');
  const [inputUniverse, setInputUniverse] = useState('1, 2, 3, 4, 5, 6, 7, 8, 9, 10');

  const parseElements = (input: string): string[] => {
    return input.split(',').map(item => item.trim()).filter(item => item.length > 0);
  };

  const updateSets = () => {
    setSetA({ name: 'A', elements: parseElements(inputA) });
    setSetB({ name: 'B', elements: parseElements(inputB) });
    setSetC({ name: 'C', elements: parseElements(inputC) });
    setUniverse(parseElements(inputUniverse));
  };

  // Set operations
  const union = (set1: string[], set2: string[]): string[] => {
    return [...new Set([...set1, ...set2])].sort();
  };

  const intersection = (set1: string[], set2: string[]): string[] => {
    return set1.filter(item => set2.includes(item)).sort();
  };

  const difference = (set1: string[], set2: string[]): string[] => {
    return set1.filter(item => !set2.includes(item)).sort();
  };

  const complement = (set: string[], universe: string[]): string[] => {
    return universe.filter(item => !set.includes(item)).sort();
  };

  const isSubset = (set1: string[], set2: string[]): boolean => {
    return set1.every(item => set2.includes(item));
  };

  const operations = [
    { name: 'A ∪ B', result: union(setA.elements, setB.elements), description: 'Union of A and B' },
    { name: 'A ∩ B', result: intersection(setA.elements, setB.elements), description: 'Intersection of A and B' },
    { name: 'A - B', result: difference(setA.elements, setB.elements), description: 'A minus B (difference)' },
    { name: 'B - A', result: difference(setB.elements, setA.elements), description: 'B minus A (difference)' },
    { name: 'A\'', result: complement(setA.elements, universe), description: 'Complement of A' },
    { name: 'B\'', result: complement(setB.elements, universe), description: 'Complement of B' },
    { name: '(A ∪ B) ∩ C', result: intersection(union(setA.elements, setB.elements), setC.elements), description: 'Union of A and B, intersected with C' },
    { name: 'A ∩ (B ∪ C)', result: intersection(setA.elements, union(setB.elements, setC.elements)), description: 'A intersected with union of B and C' },
  ];

  const SetDisplay = ({ set }: { set: SetData }) => (
    <div className="text-center">
      <div className="font-bold text-lg mb-2">{set.name}</div>
      <div className="border-2 border-blue-300 rounded-lg p-4 min-h-[80px] bg-blue-50">
        <div className="flex flex-wrap gap-1 justify-center">
          {set.elements.map((element, index) => (
            <Badge key={index} variant="default" className="text-xs">
              {element}
            </Badge>
          ))}
        </div>
      </div>
      <div className="text-sm text-gray-600 mt-1">
        |{set.name}| = {set.elements.length}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Set Definition</CardTitle>
          <CardDescription>Define your sets and universe</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="setA">Set A</Label>
              <Input
                id="setA"
                value={inputA}
                onChange={(e) => setInputA(e.target.value)}
                placeholder="Enter elements separated by commas"
              />
            </div>
            <div>
              <Label htmlFor="setB">Set B</Label>
              <Input
                id="setB"
                value={inputB}
                onChange={(e) => setInputB(e.target.value)}
                placeholder="Enter elements separated by commas"
              />
            </div>
            <div>
              <Label htmlFor="setC">Set C</Label>
              <Input
                id="setC"
                value={inputC}
                onChange={(e) => setInputC(e.target.value)}
                placeholder="Enter elements separated by commas"
              />
            </div>
            <div>
              <Label htmlFor="universe">Universe U</Label>
              <Input
                id="universe"
                value={inputUniverse}
                onChange={(e) => setInputUniverse(e.target.value)}
                placeholder="Enter universe elements"
              />
            </div>
          </div>
          <Button onClick={updateSets} className="w-full">
            Update Sets
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Set Visualization</CardTitle>
          <CardDescription>Visual representation of your sets</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <SetDisplay set={setA} />
            <SetDisplay set={setB} />
            <SetDisplay set={setC} />
            <div className="text-center">
              <div className="font-bold text-lg mb-2">U</div>
              <div className="border-2 border-gray-400 rounded-lg p-4 min-h-[80px] bg-gray-50">
                <div className="flex flex-wrap gap-1 justify-center">
                  {universe.map((element, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {element}
                    </Badge>
                  ))}
                </div>
              </div>
              <div className="text-sm text-gray-600 mt-1">
                |U| = {universe.length}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Set Operations</CardTitle>
          <CardDescription>Results of various set operations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {operations.map((operation, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <code className="font-bold text-lg">{operation.name}</code>
                  <Badge variant="outline">
                    |{operation.result.length}|
                  </Badge>
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  {operation.description}
                </div>
                <div className="flex flex-wrap gap-1">
                  {operation.result.length > 0 ? (
                    operation.result.map((element, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {element}
                      </Badge>
                    ))
                  ) : (
                    <Badge variant="outline" className="text-xs">
                      ∅ (empty set)
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Set Relationships</CardTitle>
          <CardDescription>Subset and equality relationships</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="font-medium">Subset Relations:</div>
              <div>A ⊆ B: {isSubset(setA.elements, setB.elements) ? '✓ True' : '✗ False'}</div>
              <div>B ⊆ A: {isSubset(setB.elements, setA.elements) ? '✓ True' : '✗ False'}</div>
              <div>A ⊆ C: {isSubset(setA.elements, setC.elements) ? '✓ True' : '✗ False'}</div>
              <div>C ⊆ A: {isSubset(setC.elements, setA.elements) ? '✓ True' : '✗ False'}</div>
            </div>
            <div className="space-y-2">
              <div className="font-medium">Set Properties:</div>
              <div>A = B: {JSON.stringify(setA.elements.sort()) === JSON.stringify(setB.elements.sort()) ? '✓ True' : '✗ False'}</div>
              <div>A ∩ B = ∅: {intersection(setA.elements, setB.elements).length === 0 ? '✓ True' : '✗ False'}</div>
              <div>A ∪ B = U: {JSON.stringify(union(setA.elements, setB.elements).sort()) === JSON.stringify(universe.sort()) ? '✓ True' : '✗ False'}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}