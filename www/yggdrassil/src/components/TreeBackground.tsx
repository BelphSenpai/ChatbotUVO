import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  size: number;
  speedY: number;
  speedX: number;
  opacity: number;
  life: number;
  maxLife: number;
  hue: number;
}

export default function TreeBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const dustParticlesRef = useRef<Particle[]>([]);
  const animFrameRef = useRef<number>(0);

  const getParticleTarget = (width: number) => {
    if (width >= 1600) return 180;
    if (width >= 1200) return 150;
    if (width >= 900) return 120;
    if (width >= 600) return 95;
    return 75;
  };

  const getDustParticleTarget = (width: number) => {
    if (width >= 1600) return 260;
    if (width >= 1200) return 210;
    if (width >= 900) return 170;
    if (width >= 600) return 130;
    return 95;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const spawnParticle = (): Particle => {
      const x = canvas.width * 0.5 + (Math.random() - 0.5) * canvas.width * 0.4;
      const y = canvas.height * 0.75 + Math.random() * canvas.height * 0.25;
      return {
        x,
        y,
        size: Math.random() * 2.5 + 0.5,
        speedY: -(Math.random() * 0.8 + 0.3),
        speedX: (Math.random() - 0.5) * 0.4,
        opacity: 0,
        life: 0,
        maxLife: Math.random() * 300 + 200,
        hue: Math.random() > 0.7 ? 48 : 140,
      };
    };

    const spawnDustParticle = (): Particle => {
      return {
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 1.1 + 0.25,
        speedY: -(Math.random() * 0.25 + 0.05),
        speedX: (Math.random() - 0.5) * 0.16,
        opacity: 0,
        life: 0,
        maxLife: Math.random() * 520 + 280,
        hue: Math.random() > 0.5 ? 48 : 140,
      };
    };

    const initialParticleCount = getParticleTarget(canvas.width);

    for (let i = 0; i < initialParticleCount; i++) {
      const p = spawnParticle();
      p.life = Math.random() * p.maxLife;
      particlesRef.current.push(p);
    }

    const initialDustCount = getDustParticleTarget(canvas.width);
    for (let i = 0; i < initialDustCount; i++) {
      const p = spawnDustParticle();
      p.life = Math.random() * p.maxLife;
      dustParticlesRef.current.push(p);
    }

    const drawTree = () => {
      const cx = canvas.width * 0.5;
      const baseY = canvas.height;
      const trunkHeight = canvas.height * 0.55;

      ctx.save();

      const drawBranch = (
        x: number,
        y: number,
        angle: number,
        length: number,
        depth: number,
        alpha: number
      ) => {
        if (depth === 0 || length < 8) return;

        const endX = x + Math.cos(angle) * length;
        const endY = y + Math.sin(angle) * length;

        const grad = ctx.createLinearGradient(x, y, endX, endY);
        grad.addColorStop(0, `rgba(180, 143, 64, ${alpha * 0.9})`);
        grad.addColorStop(0.5, `rgba(120, 180, 80, ${alpha * 0.6})`);
        grad.addColorStop(1, `rgba(180, 143, 64, ${alpha * 0.2})`);

        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = grad;
        ctx.lineWidth = Math.max(0.5, depth * 0.7);
        ctx.stroke();

        if (depth > 1) {
          const spread = 0.35 + (1 - depth / 8) * 0.2;
          drawBranch(endX, endY, angle - spread, length * 0.72, depth - 1, alpha * 0.85);
          drawBranch(endX, endY, angle + spread, length * 0.72, depth - 1, alpha * 0.85);
          if (depth > 4) {
            drawBranch(endX, endY, angle, length * 0.65, depth - 1, alpha * 0.7);
          }
        }
      };

      // Trunk
      const trunkGrad = ctx.createLinearGradient(cx, baseY, cx, baseY - trunkHeight);
      trunkGrad.addColorStop(0, 'rgba(180, 143, 64, 0.25)');
      trunkGrad.addColorStop(0.6, 'rgba(140, 100, 40, 0.15)');
      trunkGrad.addColorStop(1, 'rgba(180, 143, 64, 0.05)');

      ctx.beginPath();
      ctx.moveTo(cx - 8, baseY);
      ctx.quadraticCurveTo(cx - 4, baseY - trunkHeight * 0.5, cx, baseY - trunkHeight);
      ctx.quadraticCurveTo(cx + 4, baseY - trunkHeight * 0.5, cx + 8, baseY);
      ctx.closePath();
      ctx.fillStyle = trunkGrad;
      ctx.fill();

      // Main branches
      const branchY = baseY - trunkHeight;
      drawBranch(cx, branchY, -Math.PI / 2, trunkHeight * 0.42, 7, 0.18);
      drawBranch(cx, branchY + trunkHeight * 0.15, -Math.PI / 2 - 0.3, trunkHeight * 0.32, 6, 0.13);
      drawBranch(cx, branchY + trunkHeight * 0.15, -Math.PI / 2 + 0.3, trunkHeight * 0.32, 6, 0.13);
      drawBranch(cx, branchY + trunkHeight * 0.3, -Math.PI / 2 - 0.55, trunkHeight * 0.25, 5, 0.1);
      drawBranch(cx, branchY + trunkHeight * 0.3, -Math.PI / 2 + 0.55, trunkHeight * 0.25, 5, 0.1);

      // Root system
      const drawRoot = (x: number, y: number, angle: number, length: number, depth: number, alpha: number) => {
        if (depth === 0 || length < 6) return;
        const endX = x + Math.cos(angle) * length;
        const endY = y + Math.sin(angle) * length;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = `rgba(180, 143, 64, ${alpha})`;
        ctx.lineWidth = Math.max(0.3, depth * 0.5);
        ctx.stroke();
        drawRoot(endX, endY, angle - 0.3, length * 0.7, depth - 1, alpha * 0.7);
        drawRoot(endX, endY, angle + 0.3, length * 0.7, depth - 1, alpha * 0.7);
      };

      drawRoot(cx, baseY, Math.PI / 2 + 0.1, trunkHeight * 0.2, 5, 0.1);
      drawRoot(cx, baseY, Math.PI / 2 - 0.1, trunkHeight * 0.2, 5, 0.1);
      drawRoot(cx - 6, baseY, Math.PI / 2 + 0.4, trunkHeight * 0.18, 4, 0.08);
      drawRoot(cx + 6, baseY, Math.PI / 2 - 0.4, trunkHeight * 0.18, 4, 0.08);

      ctx.restore();
    };

    const drawGlow = () => {
      const cx = canvas.width * 0.5;
      const cy = canvas.height * 0.45;

      // Core radial glow
      const radGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, canvas.height * 0.55);
      radGrad.addColorStop(0, 'rgba(180, 143, 64, 0.06)');
      radGrad.addColorStop(0.3, 'rgba(100, 160, 60, 0.04)');
      radGrad.addColorStop(0.6, 'rgba(20, 50, 20, 0.02)');
      radGrad.addColorStop(1, 'rgba(0,0,0,0)');

      ctx.beginPath();
      ctx.arc(cx, cy, canvas.height * 0.55, 0, Math.PI * 2);
      ctx.fillStyle = radGrad;
      ctx.fill();

      // Bottom ground mist
      const mistGrad = ctx.createLinearGradient(0, canvas.height * 0.7, 0, canvas.height);
      mistGrad.addColorStop(0, 'rgba(10, 30, 12, 0)');
      mistGrad.addColorStop(0.5, 'rgba(10, 30, 12, 0.15)');
      mistGrad.addColorStop(1, 'rgba(5, 15, 6, 0.4)');

      ctx.fillStyle = mistGrad;
      ctx.fillRect(0, canvas.height * 0.7, canvas.width, canvas.height * 0.3);
    };

    const tick = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      drawGlow();
      drawTree();

      // Update and draw particles
      particlesRef.current = particlesRef.current.filter(p => p.life < p.maxLife);
      dustParticlesRef.current = dustParticlesRef.current.filter(p => p.life < p.maxLife);

      const targetParticleCount = getParticleTarget(canvas.width);
      while (particlesRef.current.length < targetParticleCount) {
        particlesRef.current.push(spawnParticle());
      }

      const targetDustParticleCount = getDustParticleTarget(canvas.width);
      while (dustParticlesRef.current.length < targetDustParticleCount) {
        dustParticlesRef.current.push(spawnDustParticle());
      }

      particlesRef.current.forEach(p => {
        p.life++;
        p.x += p.speedX;
        p.y += p.speedY;
        p.speedX += (Math.random() - 0.5) * 0.04;

        const progress = p.life / p.maxLife;
        p.opacity = progress < 0.15
          ? progress / 0.15
          : progress > 0.8
            ? (1 - progress) / 0.2
            : 1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);

        if (p.hue === 48) {
          ctx.fillStyle = `rgba(220, 190, 95, ${p.opacity * 0.92})`;
          if (p.size > 1.8) {
            ctx.shadowBlur = 11;
            ctx.shadowColor = 'rgba(220, 190, 95, 0.75)';
          }
        } else {
          ctx.fillStyle = `rgba(130, 235, 150, ${p.opacity * 0.7})`;
          if (p.size > 1.8) {
            ctx.shadowBlur = 9;
            ctx.shadowColor = 'rgba(130, 235, 150, 0.65)';
          }
        }
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      dustParticlesRef.current.forEach(p => {
        p.life++;
        p.x += p.speedX;
        p.y += p.speedY;
        p.speedX += (Math.random() - 0.5) * 0.01;

        const progress = p.life / p.maxLife;
        p.opacity = progress < 0.2
          ? progress / 0.2
          : progress > 0.85
            ? (1 - progress) / 0.15
            : 1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        if (p.hue === 48) {
          ctx.fillStyle = `rgba(230, 205, 130, ${p.opacity * 0.36})`;
          ctx.shadowBlur = 4;
          ctx.shadowColor = 'rgba(230, 205, 130, 0.3)';
        } else {
          ctx.fillStyle = `rgba(150, 230, 170, ${p.opacity * 0.28})`;
          ctx.shadowBlur = 3;
          ctx.shadowColor = 'rgba(150, 230, 170, 0.24)';
        }
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      animFrameRef.current = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animFrameRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}
