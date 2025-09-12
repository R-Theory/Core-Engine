import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import LogicExplorer from '@/components/LogicExplorer';
import LogicSimplifier from '@/components/LogicSimplifier';
import LogicTranslator from '@/components/LogicTranslator';
import SetExplorer from '@/components/SetExplorer';
import QuantifierExplorer from '@/components/QuantifierExplorer';
import CountingCalculator from '@/components/CountingCalculator';

export default function Index() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            Logic & Set Explorer
          </h1>
          <p className="text-lg text-gray-600">
            Interactive tool for mathematical reasoning, logic, and set theory
          </p>
        </div>

        <Tabs defaultValue="logic" className="w-full">
          <TabsList className="grid w-full grid-cols-6 mb-6">
            <TabsTrigger value="logic">Logic Explorer</TabsTrigger>
            <TabsTrigger value="simplifier">Simplifier</TabsTrigger>
            <TabsTrigger value="translator">Translator</TabsTrigger>
            <TabsTrigger value="sets">Set Explorer</TabsTrigger>
            <TabsTrigger value="quantifiers">Quantifiers</TabsTrigger>
            <TabsTrigger value="counting">Counting</TabsTrigger>
          </TabsList>

          <TabsContent value="logic">
            <Card>
              <CardHeader>
                <CardTitle>Logic Operations & Truth Tables</CardTitle>
                <CardDescription>
                  Create logical expressions and generate truth tables
                </CardDescription>
              </CardHeader>
              <CardContent>
                <LogicExplorer />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="simplifier">
            <Card>
              <CardHeader>
                <CardTitle>Logic Simplification</CardTitle>
                <CardDescription>
                  Simplify logical expressions step by step
                </CardDescription>
              </CardHeader>
              <CardContent>
                <LogicSimplifier />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="translator">
            <Card>
              <CardHeader>
                <CardTitle>English-Logic Translation</CardTitle>
                <CardDescription>
                  Convert between natural language and symbolic logic
                </CardDescription>
              </CardHeader>
              <CardContent>
                <LogicTranslator />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sets">
            <Card>
              <CardHeader>
                <CardTitle>Set Operations</CardTitle>
                <CardDescription>
                  Define sets and perform operations with visualization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SetExplorer />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="quantifiers">
            <Card>
              <CardHeader>
                <CardTitle>Quantifier Logic</CardTitle>
                <CardDescription>
                  Work with universal and existential quantifiers
                </CardDescription>
              </CardHeader>
              <CardContent>
                <QuantifierExplorer />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="counting">
            <Card>
              <CardHeader>
                <CardTitle>Counting Principles</CardTitle>
                <CardDescription>
                  Calculate permutations, combinations, and apply counting rules
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CountingCalculator />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}