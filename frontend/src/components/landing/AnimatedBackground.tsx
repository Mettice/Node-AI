import { useEffect, useRef } from 'react';

export function AnimatedBackground() {
  const gridRef = useRef<HTMLDivElement>(null);
  const glow1Ref = useRef<HTMLDivElement>(null);
  const glow2Ref = useRef<HTMLDivElement>(null);
  const glow3Ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = e.clientX / window.innerWidth;
      const y = e.clientY / window.innerHeight;

      if (glow1Ref.current) {
        glow1Ref.current.style.transform = `translate(${x * 50}px, ${y * 50}px)`;
      }
      if (glow2Ref.current) {
        glow2Ref.current.style.transform = `translate(${-x * 40}px, ${-y * 40}px)`;
      }
      if (glow3Ref.current) {
        glow3Ref.current.style.transform = `translate(${x * 30}px, ${-y * 30}px)`;
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <>
      {/* Grid Background */}
      <div
        ref={gridRef}
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Floating Glows */}
      <div
        ref={glow1Ref}
        className="fixed w-[800px] h-[800px] rounded-full blur-[100px] opacity-50 pointer-events-none z-0 top-[-200px] left-[-200px] transition-transform duration-1000 ease-out"
        style={{
          background: 'radial-gradient(circle, rgba(240, 180, 41, 0.15) 0%, transparent 70%)',
        }}
      />
      <div
        ref={glow2Ref}
        className="fixed w-[600px] h-[600px] rounded-full blur-[100px] opacity-50 pointer-events-none z-0 top-1/2 right-[-150px] transition-transform duration-1000 ease-out"
        style={{
          background: 'radial-gradient(circle, rgba(244, 114, 182, 0.12) 0%, transparent 70%)',
        }}
      />
      <div
        ref={glow3Ref}
        className="fixed w-[500px] h-[500px] rounded-full blur-[100px] opacity-50 pointer-events-none z-0 bottom-[-100px] left-[30%] transition-transform duration-1000 ease-out"
        style={{
          background: 'radial-gradient(circle, rgba(34, 211, 238, 0.1) 0%, transparent 70%)',
        }}
      />
    </>
  );
}

