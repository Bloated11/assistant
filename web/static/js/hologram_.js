let scene, camera, renderer;
let hologramGroup;
let dataPoints = [];
let currentMode = 'idle';

function initHologram() {
    const container = document.getElementById('hologramContainer');
    if (!container) return;
    
    scene = new THREE.Scene();
    
    camera = new THREE.PerspectiveCamera(
        50,
        container.clientWidth / container.clientHeight,
        0.1,
        1000
    );
    camera.position.z = 8;
    
    renderer = new THREE.WebGLRenderer({
        canvas: document.getElementById('hologramCanvas'),
        alpha: true,
        antialias: true
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setClearColor(0x000000, 0);
    
    const ambientLight = new THREE.AmbientLight(0x87CEEB, 0.5);
    scene.add(ambientLight);
    
    const pointLight = new THREE.PointLight(0x87CEEB, 1, 100);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);
    
    createIdleHologram();
    
    window.addEventListener('resize', onWindowResize);
    
    animate();
}

function onWindowResize() {
    const container = document.getElementById('hologramContainer');
    if (!container) return;
    
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function createIdleHologram() {
    if (hologramGroup) {
        scene.remove(hologramGroup);
    }
    
    hologramGroup = new THREE.Group();
    
    const ringCount = 5;
    for (let i = 0; i < ringCount; i++) {
        const radius = 1 + i * 0.3;
        const geometry = new THREE.TorusGeometry(radius, 0.02, 16, 100);
        const material = new THREE.MeshPhongMaterial({
            color: 0x87CEEB,
            transparent: true,
            opacity: 0.6 - i * 0.1,
            emissive: 0x87CEEB,
            emissiveIntensity: 0.3
        });
        const ring = new THREE.Mesh(geometry, material);
        ring.rotation.x = Math.PI / 2;
        ring.userData.rotationSpeed = 0.001 + i * 0.0005;
        ring.userData.floatOffset = i * Math.PI / ringCount;
        hologramGroup.add(ring);
    }
    
    const coreGeometry = new THREE.SphereGeometry(0.3, 32, 32);
    const coreMaterial = new THREE.MeshPhongMaterial({
        color: 0x87CEEB,
        transparent: true,
        opacity: 0.8,
        emissive: 0x87CEEB,
        emissiveIntensity: 0.5
    });
    const core = new THREE.Mesh(coreGeometry, coreMaterial);
    hologramGroup.add(core);
    
    for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2;
        const x = Math.cos(angle) * 2.5;
        const z = Math.sin(angle) * 2.5;
        
        const pointGeometry = new THREE.SphereGeometry(0.05, 16, 16);
        const pointMaterial = new THREE.MeshPhongMaterial({
            color: 0x87CEEB,
            emissive: 0x87CEEB,
            emissiveIntensity: 0.5
        });
        const point = new THREE.Mesh(pointGeometry, pointMaterial);
        point.position.set(x, 0, z);
        
        const lineGeometry = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(x, 0, z)
        ]);
        const lineMaterial = new THREE.LineBasicMaterial({
            color: 0x87CEEB,
            transparent: true,
            opacity: 0.3
        });
        const line = new THREE.Line(lineGeometry, lineMaterial);
        
        hologramGroup.add(point);
        hologramGroup.add(line);
        
        dataPoints.push({point, line, angle, originalX: x, originalZ: z});
    }
    
    scene.add(hologramGroup);
}

function createDataHologram(dataValues = []) {
    if (hologramGroup) {
        scene.remove(hologramGroup);
    }
    
    hologramGroup = new THREE.Group();
    
    const values = dataValues.length > 0 ? dataValues : [0.5, 0.7, 0.3, 0.9, 0.6, 0.4, 0.8, 0.5];
    
    for (let i = 0; i < values.length; i++) {
        const angle = (i / values.length) * Math.PI * 2;
        const radius = 2;
        const height = values[i] * 2;
        
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;
        
        const barGeometry = new THREE.BoxGeometry(0.2, height, 0.2);
        const barMaterial = new THREE.MeshPhongMaterial({
            color: 0x87CEEB,
            transparent: true,
            opacity: 0.7,
            emissive: 0x87CEEB,
            emissiveIntensity: 0.4
        });
        const bar = new THREE.Mesh(barGeometry, barMaterial);
        bar.position.set(x, height / 2, z);
        
        const edgesGeometry = new THREE.EdgesGeometry(barGeometry);
        const edgesMaterial = new THREE.LineBasicMaterial({color: 0xffffff, opacity: 0.5, transparent: true});
        const edges = new THREE.LineSegments(edgesGeometry, edgesMaterial);
        edges.position.copy(bar.position);
        
        hologramGroup.add(bar);
        hologramGroup.add(edges);
    }
    
    const circleGeometry = new THREE.RingGeometry(1.8, 2.2, 32);
    const circleMaterial = new THREE.MeshBasicMaterial({
        color: 0x87CEEB,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.2
    });
    const circle = new THREE.Mesh(circleGeometry, circleMaterial);
    circle.rotation.x = Math.PI / 2;
    hologramGroup.add(circle);
    
    scene.add(hologramGroup);
}

function createNetworkHologram() {
    if (hologramGroup) {
        scene.remove(hologramGroup);
    }
    
    hologramGroup = new THREE.Group();
    
    const nodes = [];
    const nodeCount = 12;
    
    for (let i = 0; i < nodeCount; i++) {
        const theta = (i / nodeCount) * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        const radius = 2;
        
        const x = radius * Math.sin(phi) * Math.cos(theta);
        const y = radius * Math.sin(phi) * Math.sin(theta);
        const z = radius * Math.cos(phi);
        
        const nodeGeometry = new THREE.SphereGeometry(0.08, 16, 16);
        const nodeMaterial = new THREE.MeshPhongMaterial({
            color: 0x87CEEB,
            emissive: 0x87CEEB,
            emissiveIntensity: 0.6
        });
        const node = new THREE.Mesh(nodeGeometry, nodeMaterial);
        node.position.set(x, y, z);
        hologramGroup.add(node);
        nodes.push({x, y, z});
    }
    
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            if (Math.random() > 0.6) {
                const points = [
                    new THREE.Vector3(nodes[i].x, nodes[i].y, nodes[i].z),
                    new THREE.Vector3(nodes[j].x, nodes[j].y, nodes[j].z)
                ];
                const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
                const lineMaterial = new THREE.LineBasicMaterial({
                    color: 0x87CEEB,
                    transparent: true,
                    opacity: 0.2
                });
                const line = new THREE.Line(lineGeometry, lineMaterial);
                hologramGroup.add(line);
            }
        }
    }
    
    scene.add(hologramGroup);
}

function setHologramMode(mode, data = []) {
    currentMode = mode;
    
    switch(mode) {
        case 'idle':
            createIdleHologram();
            break;
        case 'data':
            createDataHologram(data);
            break;
        case 'network':
            createNetworkHologram();
            break;
    }
}

function animate() {
    requestAnimationFrame(animate);
    
    if (hologramGroup) {
        const time = Date.now() * 0.001;
        
        if (currentMode === 'idle') {
            hologramGroup.rotation.y += 0.002;
            
            hologramGroup.children.forEach((child, index) => {
                if (child.geometry && child.geometry.type === 'TorusGeometry') {
                    child.rotation.z += child.userData.rotationSpeed;
                    child.position.y = Math.sin(time * 2 + child.userData.floatOffset) * 0.1;
                }
            });
            
            dataPoints.forEach((item, index) => {
                const pulseSpeed = time * 2 + item.angle;
                const pulseMagnitude = 0.2;
                const scale = 1 + Math.sin(pulseSpeed) * pulseMagnitude;
                
                item.point.position.x = item.originalX * scale;
                item.point.position.z = item.originalZ * scale;
                item.point.position.y = Math.sin(time * 3 + index) * 0.3;
                
                const positions = item.line.geometry.attributes.position;
                positions.setXYZ(1, item.point.position.x, item.point.position.y, item.point.position.z);
                positions.needsUpdate = true;
            });
        } else if (currentMode === 'data') {
            hologramGroup.rotation.y += 0.003;
        } else if (currentMode === 'network') {
            hologramGroup.rotation.y += 0.001;
            hologramGroup.rotation.x = Math.sin(time * 0.5) * 0.2;
        }
    }
    
    renderer.render(scene, camera);
}

function updateAvatarPulse(intensity) {
    const avatar = document.getElementById('avatarCore');
    if (avatar) {
        avatar.style.boxShadow = `0 0 ${40 + intensity * 40}px rgba(135, 206, 250, ${0.4 + intensity * 0.4})`;
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHologram);
} else {
    initHologram();
}
