const cloudContainer = document.getElementById('cloudContainer');
const smokeContainer = document.getElementById('smokeContainer');
const mouth = document.getElementById('mouth');

/**
 * Genera partículas de humo basadas en el diseño del usuario.
 */
const smokePositions = [
    { x: '30px', y: '70px', sx: '-35px', sy: '-40px' },
    { x: '20px', y: '90px', sx: '-40px', sy: '-25px' },
    { x: '35px', y: '110px', sx: '-28px', sy: '-50px' },
    { x: '15px', y: '80px', sx: '-50px', sy: '-35px' },
    { x: '190px', y: '70px', sx: '35px', sy: '-40px' },
    { x: '200px', y: '90px', sx: '42px', sy: '-28px' },
    { x: '185px', y: '110px', sx: '30px', sy: '-55px' },
    { x: '205px', y: '80px', sx: '48px', sy: '-30px' },
    { x: '100px', y: '30px', sx: '-10px', sy: '-55px' },
    { x: '130px', y: '25px', sx: '8px', sy: '-58px' },
    { x: '115px', y: '35px', sx: '0px', sy: '-60px' },
    { x: '90px', y: '165px', sx: '-15px', sy: '40px' },
    { x: '130px', y: '168px', sx: '15px', sy: '42px' },
];

smokePositions.forEach((p, i) => {
    const size = Math.floor(Math.random() * 30 + 28);
    const d = document.createElement('div');
    d.className = 'smoke';
    d.style.cssText = `
        width:${size}px; height:${size}px;
        left:${p.x}; top:${p.y};
        --sd:${(Math.random() * 2 + 2.5).toFixed(1)}s;
        --sdelay:${(Math.random() * 3).toFixed(1)}s;
        --sx:${p.sx}; --sy:${p.sy};
    `;
    smokeContainer.appendChild(d);
});

/**
 * Cambia el estado visual de la nube.
 */
function setState(state) {
    if (!cloudContainer) return;
    cloudContainer.classList.remove('state-listening', 'state-thinking', 'state-speaking');

    if (state === 'listening') {
        cloudContainer.classList.add('state-listening');
    } else if (state === 'thinking') {
        cloudContainer.classList.add('state-thinking');
    } else if (state === 'speaking') {
        cloudContainer.classList.add('state-speaking');
    }
}

/**
 * Animación de boca.
 */
function startTalking() {
    if (mouth) mouth.classList.add('talking');
}

function stopTalking() {
    if (mouth) mouth.classList.remove('talking');
}

window.setCloudState = setState;
window.startTalking = startTalking;
window.stopTalking = stopTalking;
