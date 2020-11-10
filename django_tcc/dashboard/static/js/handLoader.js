if ( ! Detector.webgl ) Detector.addGetWebGLMessage();

var camera, scene, renderer;

init();

function init() {

  scene = new THREE.Scene();
  scene.add( new THREE.AmbientLight( 0x999999 ) );

  camera = new THREE.PerspectiveCamera( 75, 256 / 256, 0.1, 1000 );

  // Z is up for objects intended to be 3D printed.

  camera.up.set( 0, -5, 2 );
  camera.position.set( 0, -5, 3 );

  camera.add( new THREE.PointLight( 0xffffff, 0.8 ) );

  scene.add( camera );

  //var grid = new THREE.GridHelper( 25, 50, 0xffffff, 0x555555 );
  //grid.rotateOnAxis( new THREE.Vector3( 1, 0, 0 ), 90 * ( Math.PI/180 ) );
  //scene.add( grid );

  renderer = new THREE.WebGLRenderer( { antialias: true } );
  renderer.setClearColor( 0x999999 );
  renderer.setPixelRatio( window.devicePixelRatio );
  renderer.setSize( 256, 256 );
  document.body.appendChild( renderer.domElement );

  var loader = new THREE.STLLoader();


  // Binary files

  var material = new THREE.MeshPhongMaterial( { color: 0x2E4053, specular: 0x111111, shininess: 75 } );
  loader.load( '../../models/brain.stl', function ( geometry ) {
    var mesh = new THREE.Mesh( geometry, material );

    mesh.position.set( -3, 0, 0);
    mesh.rotation.set( 0, 0, -1 );
    mesh.scale.set( .02, .02, .02 );

    mesh.castShadow = true;
    mesh.receiveShadow = true;

    scene.add( mesh );
    render();
  });

  var controls = new THREE.OrbitControls( camera, renderer.domElement );
  controls.addEventListener( 'change', render );
  controls.target.set( 0, 1.2, 2 );
  controls.update();
  window.addEventListener( 'resize', onWindowResize, false );

}

function onWindowResize() {

  camera.aspect = 256 / 256;
  camera.updateProjectionMatrix();

  renderer.setSize( 256, 256 );

  render();

}

function render() {

  renderer.render( scene, camera );

}
