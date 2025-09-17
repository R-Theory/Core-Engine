'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/authStore'
import { 
  BookOpen, 
  Zap, 
  Bot, 
  Users, 
  TrendingUp, 
  ArrowRight,
  Sparkles,
  Globe,
  Shield,
  Rocket
} from 'lucide-react'

export default function HomePage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false)
      if (isAuthenticated) {
        router.push('/dashboard')
      }
    }, 1000)

    return () => clearTimeout(timer)
  }, [isAuthenticated, router])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 dark:from-slate-900 dark:via-slate-900 dark:to-indigo-900/20 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl animate-pulse mx-auto mb-4 flex items-center justify-center">
            <Sparkles className="h-8 w-8 text-white" />
          </div>
          <div className="loading-shimmer h-4 w-32 rounded mx-auto"></div>
        </div>
      </div>
    )
  }

  const features = [
    {
      icon: BookOpen,
      title: "Course Management", 
      description: "Organize and track your academic courses with AI-powered insights"
    },
    {
      icon: Bot,
      title: "AI Agents",
      description: "Multi-agent workflows with MetaGPT, Claude, and Perplexity integration"
    },
    {
      icon: Zap,
      title: "Workflow Automation",
      description: "Automate repetitive tasks with visual workflow builder"
    },
    {
      icon: Globe,
      title: "Plugin System",
      description: "Seamless integration with Canvas, GitHub, and Google Drive"
    },
    {
      icon: TrendingUp,
      title: "Analytics & Insights",
      description: "Track progress and get personalized learning recommendations"
    },
    {
      icon: Shield,
      title: "Secure & Private",
      description: "Enterprise-grade security with encrypted data and OAuth 2.0"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 dark:from-slate-900 dark:via-slate-900 dark:to-indigo-900/20">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-slate-200/50 dark:border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-900 dark:text-white">Core Engine</span>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => router.push('/auth/login')}
              className="btn-ghost"
            >
              Sign In
            </button>
            <button 
              onClick={() => router.push('/auth/register')}
              className="btn-primary"
            >
              Get Started
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-sm font-medium rounded-full mb-8">
            <Rocket className="h-4 w-4" />
            AI-Powered Learning Platform
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold text-slate-900 dark:text-white mb-6 tracking-tight">
            Your Personal
            <span className="bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent"> Academic</span>
            <br />Operating System
          </h1>
          
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto mb-12 leading-relaxed">
            Streamline your university studies with AI agents, automated workflows, and seamless integrations. 
            Built for computer science students who want to focus on learning, not logistics.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button 
              onClick={() => router.push('/auth/register')}
              className="btn-primary text-lg px-8 py-4 flex items-center gap-2"
            >
              Start Learning
              <ArrowRight className="h-5 w-5" />
            </button>
            <button 
              onClick={() => router.push('/dashboard')}
              className="btn-secondary text-lg px-8 py-4"
            >
              View Demo
            </button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
              Everything you need to excel academically
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-lg max-w-2xl mx-auto">
              Powerful features designed specifically for university computer science students
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className="glass-card-hover p-8 animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="w-14 h-14 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center mb-6">
                  <feature.icon className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="glass-card p-12 text-center bg-gradient-to-r from-indigo-500/10 to-purple-600/10">
            <Users className="h-16 w-16 text-indigo-500 mx-auto mb-6" />
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
              Ready to transform your studies?
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-lg mb-8 max-w-2xl mx-auto">
              Join thousands of students who are already using Core Engine to streamline their academic workflow
            </p>
            <button 
              onClick={() => router.push('/auth/register')}
              className="btn-primary text-lg px-8 py-4 inline-flex items-center gap-2"
            >
              Get started for free
              <ArrowRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}