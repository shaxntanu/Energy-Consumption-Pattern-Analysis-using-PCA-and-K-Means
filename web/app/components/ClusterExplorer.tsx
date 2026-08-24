'use client';

import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';

interface Cluster {
  id: number;
  name: string;
  color: string;
  size: number;
  peak_hour: number;
  description: string;
}

interface Consumer {
  id: number;
  cluster: number;
  x: number;
  y: number;
  z: number;
}

const CLUSTERS: Cluster[] = [
  {
    id: 0,
    name: 'Midday-Peaking',
    color: '#F5A524',
    size: 94,
    peak_hour: 13,
    description: 'Rises through morning to broad afternoon plateau'
  },
  {
    id: 1,
    name: 'Flat All-Day',
    color: '#3BC9DE',
    size: 57,
    peak_hour: 19,
    description: 'Close to level; weak peak near 7 pm'
  },
  {
    id: 2,
    name: 'Evening-Peaking',
    color: '#B085F5',
    size: 49,
    peak_hour: 20,
    description: 'Quiet by day, sharp peak near 8 pm'
  }
];

// Generate synthetic consumer data in 3D space (PCA components)
const generateConsumerData = (): Consumer[] => {
  const consumers: Consumer[] = [];
  let id = 0;

  CLUSTERS.forEach((cluster) => {
    for (let i = 0; i < cluster.size; i++) {
      const angle = (i / cluster.size) * Math.PI * 2;
      const radius = 10 + Math.random() * 5;
      const height = cluster.id * 15 + (Math.random() - 0.5) * 8;

      consumers.push({
        id: id++,
        cluster: cluster.id,
        x: Math.cos(angle) * radius + (Math.random() - 0.5) * 3,
        y: height,
        z: Math.sin(angle) * radius + (Math.random() - 0.5) * 3
      });
    }
  });

  return consumers;
};

export default function ClusterExplorer() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const pointsRef = useRef<THREE.Points | null>(null);
  const [hoveredCluster, setHoveredCluster] = useState<number | null>(null);
  const [rotation, setRotation] = useState({ x: 0, y: 0 });
  const isDraggingRef = useRef(false);
  const previousMouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!containerRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b0e14);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(
      75,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.set(0, 15, 40);
    camera.lookAt(0, 15, 0);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xffffff, 0.8);
    pointLight.position.set(50, 50, 50);
    scene.add(pointLight);

    // Generate consumer data
    const consumers = generateConsumerData();

    // Create points geometry
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(consumers.length * 3);
    const colors = new Float32Array(consumers.length * 3);

    consumers.forEach((consumer, i) => {
      positions[i * 3] = consumer.x;
      positions[i * 3 + 1] = consumer.y;
      positions[i * 3 + 2] = consumer.z;

      const cluster = CLUSTERS[consumer.cluster];
      const hexColor = parseInt(cluster.color.slice(1), 16);
      const r = ((hexColor >> 16) & 255) / 255;
      const g = ((hexColor >> 8) & 255) / 255;
      const b = (hexColor & 255) / 255;

      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    });

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // Create points material
    const material = new THREE.PointsMaterial({
      size: 0.8,
      vertexColors: true,
      transparent: true,
      opacity: 0.8
    });

    // Create points mesh
    const points = new THREE.Points(geometry, material);
    scene.add(points);
    pointsRef.current = points;

    // Add cluster center spheres
    CLUSTERS.forEach((cluster, i) => {
      const sphereGeometry = new THREE.SphereGeometry(2, 32, 32);
      const sphereMaterial = new THREE.MeshBasicMaterial({
        color: cluster.color,
        transparent: true,
        opacity: 0.3,
        wireframe: true
      });
      const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
      sphere.position.y = cluster.id * 15;
      scene.add(sphere);
    });

    // Add grid
    const gridHelper = new THREE.GridHelper(100, 10, 0x262e3d, 0x1b2230);
    gridHelper.position.y = -10;
    scene.add(gridHelper);

    // Mouse events
    const onMouseDown = (e: MouseEvent) => {
      isDraggingRef.current = true;
      previousMouseRef.current = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (isDraggingRef.current) {
        const deltaX = e.clientX - previousMouseRef.current.x;
        const deltaY = e.clientY - previousMouseRef.current.y;

        setRotation((prev) => ({
          x: prev.x + deltaY * 0.01,
          y: prev.y + deltaX * 0.01
        }));

        previousMouseRef.current = { x: e.clientX, y: e.clientY };
      }
    };

    const onMouseUp = () => {
      isDraggingRef.current = false;
    };

    renderer.domElement.addEventListener('mousedown', onMouseDown);
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);

      if (pointsRef.current) {
        pointsRef.current.rotation.x += rotation.x * 0.02;
        pointsRef.current.rotation.y += rotation.y * 0.02;
      }

      renderer.render(scene, camera);
    };

    animate();

    // Handle resize
    const handleResize = () => {
      if (!containerRef.current) return;
      const width = containerRef.current.clientWidth;
      const height = containerRef.current.clientHeight;

      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      renderer.domElement.removeEventListener('mousedown', onMouseDown);
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      containerRef.current?.removeChild(renderer.domElement);
    };
  }, [rotation]);

  return (
    <div className="w-full">
      <div
        ref={containerRef}
        className="w-full h-96 rounded-lg border border-[#262E3D] bg-[#0B0E14]"
      />
      
      <div className="mt-6 grid grid-cols-3 gap-4">
        {CLUSTERS.map((cluster) => (
          <div
            key={cluster.id}
            className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4 cursor-pointer hover:border-[#3BC9DE] transition"
            onMouseEnter={() => setHoveredCluster(cluster.id)}
            onMouseLeave={() => setHoveredCluster(null)}
          >
            <div className="flex items-center gap-2 mb-2">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: cluster.color }}
              />
              <p className="font-semibold text-[#EAECEF]">{cluster.name}</p>
            </div>
            <p className="text-xs font-mono text-[#8A93A6] mb-2">
              {cluster.size} consumers · peaks {cluster.peak_hour}:00
            </p>
            <p className="text-sm text-[#8A93A6]">{cluster.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
        <p className="text-xs font-mono text-[#3BC9DE] uppercase tracking-wider mb-2">Controls</p>
        <p className="text-sm text-[#8A93A6]">
          Drag to rotate the 3D cluster visualization. Each point represents one consumer, colored by cluster.
        </p>
      </div>
    </div>
  );
}
