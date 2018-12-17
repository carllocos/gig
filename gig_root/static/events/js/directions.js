var map = null;
var geocoder = null;
var user_location=null;
var mapBoxDirections=null;

mapboxgl.accessToken = 'pk.eyJ1IjoiYW50ZW1vb28iLCJhIjoiY2pwOTB5ZDBjMDJidzN1cWoxOWZncGdhdSJ9.dJg1hseRjqfD9aHXjXfNtA';

function createMap(id_map, options) {
	map = new mapboxgl.Map({
  	container: 'map_canvas', // HTML container id
  	style: 'mapbox://styles/mapbox/streets-v10', // style URL
  	center: [ options.longitude, options.latitude], // starting position as [lng, lat]
  	zoom: options.zoom
	});


	geocoder = new MapboxGeocoder({ accessToken: mapboxgl.accessToken });
	map.addControl(geocoder);
  createMarker(options);

  mapBoxDirections = new MapboxDirections({accessToken: mapboxgl.accessToken});
  map.addControl(mapBoxDirections, 'top-left');

  mapBoxDirections.setDestination([ options.longitude, options.latitude])

  populateOrigin();
}


function populateOrigin() {
  var onError = function(error) {
  };
	if(navigator.geolocation) {
	    navigator.geolocation.getCurrentPosition(
			function(position) {
				mapBoxDirections.setOrigin([position.coords.longitude, position.coords.latitude]);
			},
    	onError
		);
	}
}

function createMarker(opts){
	var contentString = "<div class='eventbox' id='marker_container'>" +
 '<br> <h4>'+ opts.title + "</h4>"+'<br/>'+ '<p>'+ opts.address+ "</p></div>";

	var popup = new mapboxgl.Popup()
	.setHTML(contentString);

  var lng_lat = new mapboxgl.LngLat(opts.longitude,opts.latitude);

  var marker = new mapboxgl.Marker()
	.setLngLat(lng_lat)
	.setPopup(popup)
	.addTo(map);
}
