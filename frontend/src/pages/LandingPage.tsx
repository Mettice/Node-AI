/**
 * NodAI Landing Page
 * Enterprise-grade landing page with modular components
 */

import { Navbar } from '@/components/landing/Navbar';
import { Hero } from '@/components/landing/Hero';
import { VisualPainPoints } from '@/components/landing/VisualPainPoints';
import { VisualGenAIStack } from '@/components/landing/VisualGenAIStack';
import { VisualMultiAgent } from '@/components/landing/VisualMultiAgent';
import { InteractiveWorkflow } from '@/components/landing/InteractiveWorkflow';
import { BentoGrid } from '@/components/landing/BentoGrid';
import { IndustriesSection } from '@/components/landing/IndustriesSection';
import { ObservabilitySection } from '@/components/landing/ObservabilitySection';
import { TrustSection } from '@/components/landing/TrustSection';
import { ComparisonSection } from '@/components/landing/ComparisonSection';
import { EnterpriseSpecs } from '@/components/landing/EnterpriseSpecs';
import { PricingSection } from '@/components/landing/PricingSection';
import { Footer } from '@/components/landing/Footer';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white selection:bg-indigo-500/30">
      <Navbar />
      <main>
        <Hero />
        <VisualPainPoints />
        <VisualGenAIStack />
        <VisualMultiAgent />
        <BentoGrid />
        <InteractiveWorkflow />
        <IndustriesSection />
        <ObservabilitySection />
        <TrustSection />
        <ComparisonSection />
        <EnterpriseSpecs />
        <PricingSection />
      </main>
      <Footer />
    </div>
  );
}