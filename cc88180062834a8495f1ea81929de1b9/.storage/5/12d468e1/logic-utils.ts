// Logic utilities for parsing and evaluating logical expressions

export interface TruthTableRow {
  [variable: string]: boolean;
  result: boolean;
}

export interface LogicalExpression {
  expression: string;
  variables: string[];
  truthTable: TruthTableRow[];
}

// Parse variables from expression
export function extractVariables(expression: string): string[] {
  const matches = expression.match(/[A-Z]/g);
  return matches ? [...new Set(matches)].sort() : [];
}

// Generate all possible truth value combinations
export function generateTruthCombinations(variables: string[]): { [key: string]: boolean }[] {
  const combinations: { [key: string]: boolean }[] = [];
  const numCombinations = Math.pow(2, variables.length);
  
  for (let i = 0; i < numCombinations; i++) {
    const combination: { [key: string]: boolean } = {};
    for (let j = 0; j < variables.length; j++) {
      combination[variables[j]] = Boolean((i >> (variables.length - 1 - j)) & 1);
    }
    combinations.push(combination);
  }
  
  return combinations;
}

// Evaluate logical expression with given variable values
export function evaluateExpression(expression: string, values: { [key: string]: boolean }): boolean {
  let expr = expression.toUpperCase();
  
  // Replace logical operators with JavaScript equivalents
  expr = expr.replace(/\bAND\b/g, '&&');
  expr = expr.replace(/\bOR\b/g, '||');
  expr = expr.replace(/\bNOT\b/g, '!');
  expr = expr.replace(/→/g, '<='); // Implication: A → B is equivalent to !A || B
  expr = expr.replace(/↔/g, '=='); // Biconditional: A ↔ B is equivalent to A == B
  
  // Handle implication properly
  expr = expr.replace(/([A-Z])\s*<=\s*([A-Z])/g, '(!$1 || $2)');
  
  // Replace variables with their boolean values
  for (const [variable, value] of Object.entries(values)) {
    const regex = new RegExp(`\\b${variable}\\b`, 'g');
    expr = expr.replace(regex, value.toString());
  }
  
  try {
    // Use Function constructor for safe evaluation
    return new Function('return ' + expr)();
  } catch (error) {
    console.error('Error evaluating expression:', error);
    return false;
  }
}

// Generate complete truth table for an expression
export function generateTruthTable(expression: string): LogicalExpression {
  const variables = extractVariables(expression);
  const combinations = generateTruthCombinations(variables);
  
  const truthTable: TruthTableRow[] = combinations.map(combination => {
    const result = evaluateExpression(expression, combination);
    return { ...combination, result };
  });
  
  return {
    expression,
    variables,
    truthTable
  };
}

// Check if two expressions are logically equivalent
export function areLogicallyEquivalent(expr1: string, expr2: string): boolean {
  const table1 = generateTruthTable(expr1);
  const table2 = generateTruthTable(expr2);
  
  if (table1.variables.length !== table2.variables.length) {
    return false;
  }
  
  return table1.truthTable.every((row, index) => 
    row.result === table2.truthTable[index]?.result
  );
}

// Basic simplification rules
export function simplifyExpression(expression: string): { steps: string[], final: string } {
  const steps: string[] = [expression];
  let current = expression;
  
  // Apply basic simplification rules
  const rules = [
    // Double negation
    { pattern: /NOT\s+NOT\s+([A-Z])/g, replacement: '$1', name: 'Double Negation' },
    // Identity laws
    { pattern: /([A-Z])\s+AND\s+TRUE/g, replacement: '$1', name: 'Identity Law' },
    { pattern: /([A-Z])\s+OR\s+FALSE/g, replacement: '$1', name: 'Identity Law' },
    // Domination laws
    { pattern: /([A-Z])\s+AND\s+FALSE/g, replacement: 'FALSE', name: 'Domination Law' },
    { pattern: /([A-Z])\s+OR\s+TRUE/g, replacement: 'TRUE', name: 'Domination Law' },
    // Idempotent laws
    { pattern: /([A-Z])\s+AND\s+\1/g, replacement: '$1', name: 'Idempotent Law' },
    { pattern: /([A-Z])\s+OR\s+\1/g, replacement: '$1', name: 'Idempotent Law' },
  ];
  
  for (const rule of rules) {
    const simplified = current.replace(rule.pattern, rule.replacement);
    if (simplified !== current) {
      current = simplified;
      steps.push(current);
    }
  }
  
  return { steps, final: current };
}

// Factorial function for counting
export function factorial(n: number): number {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}

// Permutation calculation
export function permutation(n: number, r: number): number {
  if (r > n || r < 0) return 0;
  return factorial(n) / factorial(n - r);
}

// Combination calculation
export function combination(n: number, r: number): number {
  if (r > n || r < 0) return 0;
  return factorial(n) / (factorial(r) * factorial(n - r));
}