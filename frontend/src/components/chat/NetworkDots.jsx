/**
 * NetworkDots — ambient moving-node network animation behind the empty-chat
 * welcome, echoing the app mark's own circuit/network motif. Purely
 * decorative and low-opacity; unmounts once the first message sends
 * (EmptyState itself unmounts), so it never runs during an active thread.
 */

import { useEffect, useRef } from 'react';
import './NetworkDots.css';

const DOT_COUNT = 22;
const LINK_DISTANCE = 130;
const SPEED = 0.15;

export default function NetworkDots() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let raf;
    let width, height;
    let dots = [];

    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      width = canvas.parentElement.clientWidth;
      height = canvas.parentElement.clientHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const init = () => {
      dots = Array.from({ length: DOT_COUNT }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * SPEED,
        vy: (Math.random() - 0.5) * SPEED,
      }));
    };

    const styles = getComputedStyle(document.documentElement);
    const dotColor = styles.getPropertyValue('--ksp-gold').trim() || '#E8A33D';
    const lineColor = styles.getPropertyValue('--stamp-ink').trim() || '#1F7A8C';

    const step = () => {
      ctx.clearRect(0, 0, width, height);

      for (const d of dots) {
        d.x += d.vx;
        d.y += d.vy;
        if (d.x < 0 || d.x > width) d.vx *= -1;
        if (d.y < 0 || d.y > height) d.vy *= -1;
      }

      for (let i = 0; i < dots.length; i++) {
        for (let j = i + 1; j < dots.length; j++) {
          const a = dots[i];
          const b = dots[j];
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          if (dist < LINK_DISTANCE) {
            ctx.strokeStyle = lineColor;
            ctx.globalAlpha = (1 - dist / LINK_DISTANCE) * 0.35;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      ctx.globalAlpha = 0.7;
      ctx.fillStyle = dotColor;
      for (const d of dots) {
        ctx.beginPath();
        ctx.arc(d.x, d.y, 2, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      raf = requestAnimationFrame(step);
    };

    resize();
    init();

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersReducedMotion) {
      raf = requestAnimationFrame(step);
    }

    const onResize = () => {
      resize();
      init();
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
    };
  }, []);

  return (
    <div className="network-dots" aria-hidden="true">
      <canvas ref={canvasRef} />
    </div>
  );
}
