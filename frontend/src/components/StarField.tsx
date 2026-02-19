'use client';

import React, { useRef, useEffect } from 'react';

interface StarFieldProps {
    speed?: number;
    backgroundColor?: string;
    starColor?: string;
    count?: number;
}

export default function StarField({
    speed = 0.05,
    backgroundColor = 'transparent',
    starColor = '#ffffff',
    count = 800
}: StarFieldProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationFrameId: number;
        interface Star {
            x: number;
            y: number;
            z: number;
            o: number | string;
        }
        let stars: Star[] = [];

        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            initStars();
        };

        const initStars = () => {
            stars = [];
            for (let i = 0; i < count; i++) {
                stars.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    z: Math.random() * canvas.width,
                    o: '0.' + Math.floor(Math.random() * 99) + 1
                });
            }
        };

        const moveStars = () => {
            for (let i = 0; i < count; i++) {
                const star = stars[i];
                star.z -= speed;

                if (star.z <= 0) {
                    star.z = canvas.width;
                }
            }
        };

        const drawStars = () => {
            if (!ctx || !canvas) return;
            ctx.fillStyle = backgroundColor;
            ctx.fillRect(0, 0, canvas.width, canvas.height); // Clear or fill background

            for (let i = 0; i < count; i++) {
                const star = stars[i];
                const x = (star.x - canvas.width / 2) * (canvas.width / star.z);
                const y = (star.y - canvas.height / 2) * (canvas.width / star.z);
                const size = (1 - star.z / canvas.width) * 2.5; // Varies size by distance

                // Color fading
                const opacity = (1 - star.z / canvas.width);

                if (x + canvas.width / 2 > 0 && x + canvas.width / 2 < canvas.width &&
                    y + canvas.height / 2 > 0 && y + canvas.height / 2 < canvas.height) {

                    ctx.beginPath();
                    ctx.fillStyle = starColor;
                    ctx.globalAlpha = opacity;
                    ctx.arc(x + canvas.width / 2, y + canvas.height / 2, size, 0, 2 * Math.PI);
                    ctx.fill();
                }
            }
        };

        const render = () => {
            moveStars();
            drawStars();
            animationFrameId = requestAnimationFrame(render);
        };

        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();
        render();

        return () => {
            window.removeEventListener('resize', resizeCanvas);
            cancelAnimationFrame(animationFrameId);
        };
    }, [speed, backgroundColor, starColor, count]);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 z-0 pointer-events-none"
            style={{ background: backgroundColor }}
        />
    );
}
