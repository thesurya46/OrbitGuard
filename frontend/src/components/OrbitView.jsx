import React, { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * Renders a schematic 3D view of Earth with two illustrative orbit paths
 * for the currently selected conjunction event.
 *
 * Note: this draws representative circular orbits (offset slightly so
 * both are visible), not the literal SGP4-propagated path — the backend
 * currently returns the scored closest-approach summary, not the full
 * per-timestep trajectory. If you want a literally accurate 3D replay,
 * extend ConjunctionEvent (or add a dedicated endpoint) to include the
 * position samples from PropagatedObject and feed those in here instead.
 */
export default function OrbitView({ event }) {
  const mountRef = useRef(null);
  const stateRef = useRef({});

  useEffect(() => {
    const mount = mountRef.current;
    const width = mount.clientWidth;
    const height = 360;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(0, 4, 11);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    // Earth
    const earthGeo = new THREE.SphereGeometry(2.2, 48, 48);
    const earthMat = new THREE.MeshStandardMaterial({
      color: 0x1b3a6b,
      roughness: 0.9,
      metalness: 0.1,
    });
    const earth = new THREE.Mesh(earthGeo, earthMat);
    scene.add(earth);

    const wireframe = new THREE.LineSegments(
      new THREE.WireframeGeometry(new THREE.SphereGeometry(2.21, 16, 12)),
      new THREE.LineBasicMaterial({ color: 0x2c4d7f, transparent: true, opacity: 0.4 })
    );
    scene.add(wireframe);

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const sun = new THREE.DirectionalLight(0xffffff, 1.0);
    sun.position.set(5, 3, 5);
    scene.add(sun);

    function orbitCurve(radius, inclinationDeg, raanOffsetDeg, color) {
      const points = [];
      const inclination = (inclinationDeg * Math.PI) / 180;
      const raan = (raanOffsetDeg * Math.PI) / 180;
      for (let i = 0; i <= 128; i++) {
        const theta = (i / 128) * Math.PI * 2;
        const x0 = radius * Math.cos(theta);
        const y0 = radius * Math.sin(theta);
        // tilt by inclination around x-axis, then rotate by RAAN around y-axis
        const x1 = x0;
        const y1 = y0 * Math.cos(inclination);
        const z1 = y0 * Math.sin(inclination);
        const x2 = x1 * Math.cos(raan) + z1 * Math.sin(raan);
        const z2 = -x1 * Math.sin(raan) + z1 * Math.cos(raan);
        points.push(new THREE.Vector3(x2, y1, z2));
      }
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({ color });
      const line = new THREE.LineLoop(geometry, material);
      scene.add(line);
      return points;
    }

    const orbitRadius = 3.4;
    const pathA = orbitCurve(orbitRadius, 51.6, 0, 0xff7a33);
    const pathB = orbitCurve(orbitRadius + 0.15, 51.6, 4, 0x4ec4ff);

    const markerA = new THREE.Mesh(
      new THREE.SphereGeometry(0.09, 16, 16),
      new THREE.MeshBasicMaterial({ color: 0xff7a33 })
    );
    const markerB = new THREE.Mesh(
      new THREE.SphereGeometry(0.09, 16, 16),
      new THREE.MeshBasicMaterial({ color: 0x4ec4ff })
    );
    scene.add(markerA, markerB);

    let frame = 0;
    let raf;
    const animate = () => {
      frame += 1;
      const idxA = frame % pathA.length;
      // Object B trails/leads slightly so the two markers visibly
      // converge and separate, echoing "closest approach" motion.
      const idxB = (frame + 6) % pathB.length;
      markerA.position.copy(pathA[idxA]);
      markerB.position.copy(pathB[idxB]);
      earth.rotation.y += 0.0015;
      renderer.render(scene, camera);
      raf = requestAnimationFrame(animate);
    };
    animate();

    stateRef.current = { renderer, mount };

    const handleResize = () => {
      const w = mount.clientWidth;
      camera.aspect = w / height;
      camera.updateProjectionMatrix();
      renderer.setSize(w, height);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", handleResize);
      mount.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, [event?.norad_id_a, event?.norad_id_b]);

  return (
    <div className="orbit-view">
      <div ref={mountRef} />
      <div className="orbit-legend">
        <span>
          <span className="legend-dot" style={{ background: "#ff7a33" }} />
          {event ? event.object_a : "Object A"}
        </span>
        <span>
          <span className="legend-dot" style={{ background: "#4ec4ff" }} />
          {event ? event.object_b : "Object B"}
        </span>
      </div>
    </div>
  );
}
