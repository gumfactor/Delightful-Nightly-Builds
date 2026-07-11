class WeatherVisual {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.params = null;
    this.snapshot = null;
    this.particles = [];
    this.animationFrameId = null;
  }

  setParams(params, snapshot) {
    this.params = params;
    this.snapshot = snapshot;
    this.rebuildParticles();
    if (this.animationFrameId === null) {
      this.render();
    }
  }

  rebuildParticles() {
    const count = this.snapshot ? Math.round(20 + (this.snapshot.windSpeedKmh / 80) * 80) : 40;
    this.particles = Array.from({ length: count }, () => this.createParticle());
  }

  createParticle() {
    const width = this.canvas.width || 1;
    const height = this.canvas.height || 1;
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      speed: 0.5 + Math.random() * 1.5,
    };
  }

  backgroundColors() {
    if (!this.snapshot) return ['#101820', '#1b2a38'];
    const t = this.snapshot.temperatureC;
    if (t <= 0) return ['#0b1a2b', '#22384f'];
    if (t <= 15) return ['#10202c', '#2c4459'];
    if (t <= 25) return ['#241d33', '#5a3d5c'];
    return ['#2e1a12', '#7a3b1d'];
  }

  start() {
    const loop = () => {
      this.render();
      this.animationFrameId = window.requestAnimationFrame(loop);
    };
    this.animationFrameId = window.requestAnimationFrame(loop);
  }

  stop() {
    if (this.animationFrameId !== null) {
      window.cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  render() {
    const { ctx, canvas } = this;
    const [colorTop, colorBottom] = this.backgroundColors();
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, colorTop);
    gradient.addColorStop(1, colorBottom);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const wind = this.snapshot ? this.snapshot.windSpeedKmh : 0;
    const cloud = this.snapshot ? this.snapshot.cloudCoverPct : 0;
    const precip = this.params ? this.params.percussionDensity : 0;
    const opacity = 0.25 + (1 - cloud / 100) * 0.5;

    ctx.fillStyle = `rgba(255,255,255,${opacity.toFixed(2)})`;
    this.particles.forEach((particle) => {
      particle.x += (wind / 80) * particle.speed * 2;
      particle.y += precip * particle.speed * 3;
      if (particle.x > canvas.width) particle.x = 0;
      if (particle.y > canvas.height) particle.y = 0;
      const size = precip > 0.4 ? 1 : 2;
      ctx.fillRect(particle.x, particle.y, size, size * (precip > 0.4 ? 6 : 1));
    });
  }
}

export { WeatherVisual };
