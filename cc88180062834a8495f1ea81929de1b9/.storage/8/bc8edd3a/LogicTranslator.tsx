import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, ArrowLeft } from 'lucide-react';

interface TranslationExample {
  english: string;
  logic: string;
  explanation: string;
}

export default function LogicTranslator() {
  const [englishText, setEnglishText] = useState('If it rains, then the ground is wet.');
  const [logicText, setLogicText] = useState('R → W');
  const [translationMode, setTranslationMode] = useState<'english-to-logic' | 'logic-to-english'>('english-to-logic');

  const examples: TranslationExample[] = [
    {
      english: "If it rains, then the ground is wet.",
      logic: "R → W",
      explanation: "Conditional statement: R (it rains) implies W (ground is wet)"
    },
    {
      english: "It is raining and the ground is wet.",
      logic: "R ∧ W",
      explanation: "Conjunction: Both R (raining) and W (wet ground) are true"
    },
    {
      english: "Either it's sunny or it's cloudy.",
      logic: "S ∨ C",
      explanation: "Disjunction: Either S (sunny) or C (cloudy) is true"
    },
    {
      english: "It is not raining.",
      logic: "¬R",
      explanation: "Negation: R (raining) is false"
    },
    {
      english: "If and only if it's sunny, then it's warm.",
      logic: "S ↔ W",
      explanation: "Biconditional: S (sunny) if and only if W (warm)"
    },
    {
      english: "All birds can fly.",
      logic: "∀x (Bird(x) → CanFly(x))",
      explanation: "Universal quantifier: For all x, if x is a bird, then x can fly"
    },
    {
      english: "Some students are smart.",
      logic: "∃x (Student(x) ∧ Smart(x))",
      explanation: "Existential quantifier: There exists an x such that x is a student and x is smart"
    }
  ];

  const translateEnglishToLogic = (text: string): string => {
    let result = text.toLowerCase();
    
    // Simple pattern matching for common logical structures
    if (result.includes('if') && result.includes('then')) {
      return "A → B (Conditional: If A then B)";
    } else if (result.includes('and')) {
      return "A ∧ B (Conjunction: A and B)";
    } else if (result.includes('or')) {
      return "A ∨ B (Disjunction: A or B)";
    } else if (result.includes('not')) {
      return "¬A (Negation: Not A)";
    } else if (result.includes('if and only if')) {
      return "A ↔ B (Biconditional: A if and only if B)";
    } else if (result.includes('all') || result.includes('every')) {
      return "∀x P(x) (Universal: For all x, P(x))";
    } else if (result.includes('some') || result.includes('there exists')) {
      return "∃x P(x) (Existential: There exists x such that P(x))";
    }
    
    return "Please use more specific logical language for better translation.";
  };

  const translateLogicToEnglish = (logic: string): string => {
    const simplified = logic.replace(/\s/g, '');
    
    if (simplified.includes('→')) {
      return "If A, then B";
    } else if (simplified.includes('∧') || simplified.includes('AND')) {
      return "A and B";
    } else if (simplified.includes('∨') || simplified.includes('OR')) {
      return "A or B";
    } else if (simplified.includes('¬') || simplified.includes('NOT')) {
      return "Not A";
    } else if (simplified.includes('↔')) {
      return "A if and only if B";
    } else if (simplified.includes('∀')) {
      return "For all x, if P(x) then Q(x)";
    } else if (simplified.includes('∃')) {
      return "There exists an x such that P(x)";
    }
    
    return "Please use standard logical notation for better translation.";
  };

  const handleTranslate = () => {
    if (translationMode === 'english-to-logic') {
      const translated = translateEnglishToLogic(englishText);
      setLogicText(translated);
    } else {
      const translated = translateLogicToEnglish(logicText);
      setEnglishText(translated);
    }
  };

  const loadExample = (example: TranslationExample) => {
    setEnglishText(example.english);
    setLogicText(example.logic);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>English Statement</CardTitle>
            <CardDescription>Natural language logical statement</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={englishText}
              onChange={(e) => setEnglishText(e.target.value)}
              placeholder="Enter an English logical statement..."
              className="min-h-[100px]"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Symbolic Logic</CardTitle>
            <CardDescription>Mathematical logical notation</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={logicText}
              onChange={(e) => setLogicText(e.target.value)}
              placeholder="Enter symbolic logic notation..."
              className="min-h-[100px]"
            />
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-center space-x-4">
        <Button
          onClick={() => {
            setTranslationMode('english-to-logic');
            handleTranslate();
          }}
          variant={translationMode === 'english-to-logic' ? 'default' : 'outline'}
        >
          <ArrowRight className="w-4 h-4 mr-2" />
          English → Logic
        </Button>
        
        <Button
          onClick={() => {
            setTranslationMode('logic-to-english');
            handleTranslate();
          }}
          variant={translationMode === 'logic-to-english' ? 'default' : 'outline'}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Logic → English
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Translation Examples</CardTitle>
          <CardDescription>Click any example to load it</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {examples.map((example, index) => (
              <div
                key={index}
                className="border rounded-lg p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => loadExample(example)}
              >
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="outline">Example {index + 1}</Badge>
                  <Button variant="ghost" size="sm">Load</Button>
                </div>
                <div className="space-y-2">
                  <div className="text-sm">
                    <strong>English:</strong> {example.english}
                  </div>
                  <div className="text-sm">
                    <strong>Logic:</strong> <code className="bg-gray-100 px-1 rounded">{example.logic}</code>
                  </div>
                  <div className="text-xs text-gray-600">
                    {example.explanation}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Logical Symbols Reference</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <strong>∧</strong> - AND (conjunction)
            </div>
            <div>
              <strong>∨</strong> - OR (disjunction)
            </div>
            <div>
              <strong>¬</strong> - NOT (negation)
            </div>
            <div>
              <strong>→</strong> - IF-THEN (implication)
            </div>
            <div>
              <strong>↔</strong> - IF AND ONLY IF (biconditional)
            </div>
            <div>
              <strong>∀</strong> - FOR ALL (universal quantifier)
            </div>
            <div>
              <strong>∃</strong> - THERE EXISTS (existential quantifier)
            </div>
            <div>
              <strong>( )</strong> - Grouping parentheses
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}