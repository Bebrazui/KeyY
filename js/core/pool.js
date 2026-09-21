/**
 * Zero-GC Object Pool for particles and visual effects.
 * Eliminates garbage collection stutters during heavy gameplay.
 */

export class Particle {
    constructor() {
        this.active = false;
        this.x = 0;
        this.y = 0;
        this.vx = 0;
        this.vy = 0;
        this.size = 6;
        this.life = 0;
        this.maxLife = 1.0;
        this.color = '#ffffff';
        this.rgb = [255, 255, 255];
    }

    init(x, y, color, rgb, size = 6, speed = 300, maxLife = 0.4) {
        this.x = x;
        this.y = y;
        const angle = Math.random() * Math.PI * 2;
        const spd = (Math.random() * 0.7 + 0.3) * speed;
        this.vx = Math.cos(angle) * spd;
        this.vy = Math.sin(angle) * spd;
        this.size = size;
        this.life = maxLife;
        this.maxLife = maxLife;
        this.color = color;
        this.rgb = rgb || [255, 255, 255];
        this.active = true;
    }

    update(dt) {
        if (!this.active) return;
        this.x += this.vx * dt;
        this.y += this.vy * dt;
        this.vx *= 0.95;
        this.vy *= 0.95;
        this.life -= dt;
        if (this.life <= 0) {
            this.active = false;
        }
    }
}

export class ObjectPool {
    constructor(createFn, initialSize = 200) {
        this.pool = [];
        this.createFn = createFn;
        for (let i = 0; i < initialSize; i++) {
            this.pool.push(createFn());
        }
    }

    get() {
        for (let i = 0; i < this.pool.length; i++) {
            if (!this.pool[i].active) {
                return this.pool[i];
            }
        }
        // Expand if needed
        const item = this.createFn();
        this.pool.push(item);
        return item;
    }

    clear() {
        for (let i = 0; i < this.pool.length; i++) {
            this.pool[i].active = false;
        }
    }

    forEachActive(callback) {
        for (let i = 0; i < this.pool.length; i++) {
            if (this.pool[i].active) {
                callback(this.pool[i]);
            }
        }
    }
}
