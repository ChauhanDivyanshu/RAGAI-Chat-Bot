"use client";

import confetti from "canvas-confetti";

export function useConfetti() {
  const fire = () => {
    const count = 200;
    const defaults = {
      origin: { y: 0.7 },
      colors: ["#a855f7", "#3b82f6", "#ec4899", "#10b981", "#f59e0b"],
    };

    function fireConfetti(particleRatio: number, opts: confetti.Options) {
      confetti({
        ...defaults,
        ...opts,
        particleCount: Math.floor(count * particleRatio),
      });
    }

    fireConfetti(0.25, {
      spread: 26,
      startVelocity: 55,
    });
    fireConfetti(0.2, {
      spread: 60,
    });
    fireConfetti(0.35, {
      spread: 100,
      decay: 0.91,
      scalar: 0.8,
    });
    fireConfetti(0.1, {
      spread: 120,
      startVelocity: 25,
      decay: 0.92,
      scalar: 1.2,
    });
    fireConfetti(0.1, {
      spread: 120,
      startVelocity: 45,
    });
  };

  return { fire };
}
