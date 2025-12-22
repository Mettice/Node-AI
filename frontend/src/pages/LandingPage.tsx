/**
 * NodeAI Landing Page
 * Modern landing page matching the animated design
 */

import { Navbar } from '@/components/landing/Navbar';
import { AnimatedBackground } from '@/components/landing/AnimatedBackground';
import { Hero } from '@/components/landing/Hero';
import { LogosSection } from '@/components/landing/LogosSection';
import { ProblemSection } from '@/components/landing/ProblemSection';
import { AgentRoomsSection } from '@/components/landing/AgentRoomsSection';
import { FeaturesSection } from '@/components/landing/FeaturesSection';
import { UseCasesSection } from '@/components/landing/UseCasesSection';
import { IntegrationsSection } from '@/components/landing/IntegrationsSection';
import { EnterpriseSection } from '@/components/landing/EnterpriseSection';
import { CTASection } from '@/components/landing/CTASection';
import { Footer } from '@/components/landing/Footer';

export function LandingPage() {
  return (
    <div className="landing-page min-h-screen bg-[#030712] text-white selection:bg-amber-500/30 relative">
      <AnimatedBackground />
      <Navbar />
      <main className="relative z-10">
        <Hero />
        <LogosSection />
        <ProblemSection />
        <AgentRoomsSection />
        <FeaturesSection />
        <UseCasesSection />
        <IntegrationsSection />
        <EnterpriseSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}