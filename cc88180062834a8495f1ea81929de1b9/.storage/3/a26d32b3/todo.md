# Logic/Set Explorer Web App - MVP Implementation

## Core Features to Implement

### 1. Logic Operations Module (`src/components/LogicExplorer.tsx`)
- Input field for logical expressions (using AND, OR, NOT, IF-THEN)
- Truth table generator
- Support for variables A, B, C, D
- Display results in interactive table format

### 2. Logic Simplification Module (`src/components/LogicSimplifier.tsx`)
- Parse logical expressions
- Apply basic simplification rules (De Morgan's laws, distributive, etc.)
- Show step-by-step simplification process
- Display equivalent expressions

### 3. English-Logic Translation (`src/components/LogicTranslator.tsx`)
- Input field for English statements
- Convert to symbolic logic notation
- Reverse translation (symbolic to English)
- Common patterns recognition

### 4. Set Operations Module (`src/components/SetExplorer.tsx`)
- Define sets A, B, C with elements
- Visual representation using Venn diagrams
- Operations: union, intersection, difference, complement
- Interactive set manipulation

### 5. Quantifiers Module (`src/components/QuantifierExplorer.tsx`)
- Universal (∀) and existential (∃) quantifiers
- Domain definition and element checking
- Statement validation with quantifiers

### 6. Counting Principles (`src/components/CountingCalculator.tsx`)
- Permutation calculator (nPr)
- Combination calculator (nCr)
- Sum and product rule examples
- Interactive counting problems

## File Structure
1. `src/pages/Index.tsx` - Main dashboard with navigation tabs
2. `src/components/LogicExplorer.tsx` - Logic operations and truth tables
3. `src/components/LogicSimplifier.tsx` - Expression simplification
4. `src/components/LogicTranslator.tsx` - English-logic translation
5. `src/components/SetExplorer.tsx` - Set operations and visualization
6. `src/components/QuantifierExplorer.tsx` - Quantifier logic
7. `src/components/CountingCalculator.tsx` - Counting principles
8. `src/lib/logic-utils.ts` - Logic parsing and evaluation utilities

## Implementation Priority
1. Main dashboard with tab navigation
2. Logic Explorer with truth tables (core feature)
3. Set Explorer with basic operations
4. Logic Simplifier with basic rules
5. Counting Calculator
6. Logic Translator
7. Quantifier Explorer

## Technical Approach
- Use React with TypeScript for type safety
- Shadcn/ui components for consistent UI
- Custom parsing logic for expressions
- Canvas or SVG for Venn diagram visualization
- Local state management (no backend needed)