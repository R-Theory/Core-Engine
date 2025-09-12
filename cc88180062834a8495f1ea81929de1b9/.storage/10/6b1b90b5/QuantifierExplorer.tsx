import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Domain {
  name: string;
  elements: string[];
}

interface Predicate {
  name: string;
  description: string;
  elements: string[];
}

export default function QuantifierExplorer() {
  const [domain, setDomain] = useState<Domain>({
    name: 'People',
    elements: ['Alice', 'Bob', 'Charlie', 'Diana']
  });
  
  const [predicates, setPredicates] = useState<Predicate[]>([
    { name: 'Smart(x)', description: 'x is smart', elements: ['Alice', 'Charlie'] },
    { name: 'Tall(x)', description: 'x is tall', elements: ['Bob', 'Charlie', 'Diana'] },
    { name: 'Student(x)', description: 'x is a student', elements: ['Alice', 'Bob', 'Diana'] }
  ]);

  const [selectedPredicate, setSelectedPredicate] = useState('Smart(x)');
  const [quantifierType, setQuantifierType] = useState<'universal' | 'existential'>('universal');
  const [customStatement, setCustomStatement] = useState('');
  
  const [domainInput, setDomainInput] = useState('Alice, Bob, Charlie, Diana');
  const [predicateInput, setPredicateInput] = useState('Alice, Charlie');

  const updateDomain = () => {
    const elements = domainInput.split(',').map(item => item.trim()).filter(item => item.length > 0);
    setDomain({ ...domain, elements });
  };

  const updatePredicate = () => {
    const elements = predicateInput.split(',').map(item => item.trim()).filter(item => item.length > 0);
    const updatedPredicates = predicates.map(p => 
      p.name === selectedPredicate 
        ? { ...p, elements }
        : p
    );
    setPredicates(updatedPredicates);
  };

  const evaluateUniversalQuantifier = (predicate: Predicate): boolean => {
    return domain.elements.every(element => predicate.elements.includes(element));
  };

  const evaluateExistentialQuantifier = (predicate: Predicate): boolean => {
    return domain.elements.some(element => predicate.elements.includes(element));
  };

  const getCurrentPredicate = (): Predicate => {
    return predicates.find(p => p.name === selectedPredicate) || predicates[0];
  };

  const examples = [
    {
      statement: '∀x Smart(x)',
      english: 'All people are smart',
      evaluation: evaluateUniversalQuantifier(getCurrentPredicate()),
      type: 'universal' as const
    },
    {
      statement: '∃x Smart(x)',
      english: 'Some people are smart',
      evaluation: evaluateExistentialQuantifier(getCurrentPredicate()),
      type: 'existential' as const
    },
    {
      statement: '∀x (Student(x) → Smart(x))',
      english: 'All students are smart',
      evaluation: domain.elements.every(element => {
        const isStudent = predicates.find(p => p.name === 'Student(x)')?.elements.includes(element);
        const isSmart = predicates.find(p => p.name === 'Smart(x)')?.elements.includes(element);
        return !isStudent || isSmart; // If not student OR is smart
      }),
      type: 'universal' as const
    },
    {
      statement: '∃x (Student(x) ∧ Tall(x))',
      english: 'There exists a student who is tall',
      evaluation: domain.elements.some(element => {
        const isStudent = predicates.find(p => p.name === 'Student(x)')?.elements.includes(element);
        const isTall = predicates.find(p => p.name === 'Tall(x)')?.elements.includes(element);
        return isStudent && isTall;
      }),
      type: 'existential' as const
    }
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Domain Definition</CardTitle>
            <CardDescription>Define the domain of discourse</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="domain">Domain Elements</Label>
              <Input
                id="domain"
                value={domainInput}
                onChange={(e) => setDomainInput(e.target.value)}
                placeholder="Enter domain elements separated by commas"
              />
            </div>
            <Button onClick={updateDomain} className="w-full">
              Update Domain
            </Button>
            <div className="p-3 bg-blue-50 rounded-lg">
              <div className="font-medium text-sm">Current Domain:</div>
              <div className="flex flex-wrap gap-1 mt-2">
                {domain.elements.map((element, index) => (
                  <Badge key={index} variant="outline">
                    {element}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Predicate Definition</CardTitle>
            <CardDescription>Define predicates and their truth values</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="predicate-select">Select Predicate</Label>
              <Select value={selectedPredicate} onValueChange={setSelectedPredicate}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {predicates.map((predicate) => (
                    <SelectItem key={predicate.name} value={predicate.name}>
                      {predicate.name} - {predicate.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="predicate-elements">Elements satisfying {selectedPredicate}</Label>
              <Input
                id="predicate-elements"
                value={predicateInput}
                onChange={(e) => setPredicateInput(e.target.value)}
                placeholder="Enter elements that satisfy the predicate"
              />
            </div>
            <Button onClick={updatePredicate} className="w-full">
              Update Predicate
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Predicate Truth Values</CardTitle>
          <CardDescription>Truth values for each predicate across the domain</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {predicates.map((predicate, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="font-medium mb-2">
                  {predicate.name}: {predicate.description}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {domain.elements.map((element, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-sm">{predicate.name.replace('x', element)}</span>
                      <Badge variant={predicate.elements.includes(element) ? "default" : "secondary"}>
                        {predicate.elements.includes(element) ? 'T' : 'F'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quantified Statements</CardTitle>
          <CardDescription>Evaluate quantified logical statements</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {examples.map((example, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <code className="font-bold">{example.statement}</code>
                  <Badge variant={example.evaluation ? "default" : "destructive"}>
                    {example.evaluation ? 'TRUE' : 'FALSE'}
                  </Badge>
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  <strong>English:</strong> {example.english}
                </div>
                <div className="text-xs text-gray-500">
                  <strong>Type:</strong> {example.type === 'universal' ? 'Universal Quantifier (∀)' : 'Existential Quantifier (∃)'}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quantifier Rules</CardTitle>
          <CardDescription>Important rules and equivalences</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-2">Universal Quantifier (∀)</h4>
              <div className="text-sm space-y-1">
                <div>• ∀x P(x) is true if P(x) is true for ALL x in domain</div>
                <div>• ∀x P(x) is false if P(x) is false for ANY x in domain</div>
                <div>• ¬∀x P(x) ≡ ∃x ¬P(x)</div>
                <div>• ∀x (P(x) ∧ Q(x)) ≡ ∀x P(x) ∧ ∀x Q(x)</div>
              </div>
            </div>
            <div>
              <h4 className="font-medium mb-2">Existential Quantifier (∃)</h4>
              <div className="text-sm space-y-1">
                <div>• ∃x P(x) is true if P(x) is true for AT LEAST ONE x in domain</div>
                <div>• ∃x P(x) is false if P(x) is false for ALL x in domain</div>
                <div>• ¬∃x P(x) ≡ ∀x ¬P(x)</div>
                <div>• ∃x (P(x) ∨ Q(x)) ≡ ∃x P(x) ∨ ∃x Q(x)</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}