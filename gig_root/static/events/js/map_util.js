
L.mapbox.accessToken = 'pk.eyJ1IjoiYW50ZW1vb28iLCJhIjoiY2pwOTB5ZDBjMDJidzN1cWoxOWZncGdhdSJ9.dJg1hseRjqfD9aHXjXfNtA';
var geocoder=null;

function createGeocoder(){
  geocoder=L.mapbox.geocoder("mapbox.places");
  return geocoder;
}




function queryAddress(id_selector, callback){
  var address = $("#"+id_selector).val();
  if (address != ""){
    geocoder.query({query: address}, callback);
  }
  else {
    console.log("Nos search performed the query is empty");
  }
}


function queryAddressSync(id_selector){
  var address=$("#"+id_selector).val();
  var q=encodeURIComponent(address);
  var remote_url= "http://a.tiles.mapbox.com/geocoding/v5/mapbox.places/"+q +".json?access_token="+L.mapbox.accessToken;
  var response=$.ajax({ type: "GET", url: remote_url, async: false}).responseJSON;

  var match_feature=false;
  if (response.type === "FeatureCollection"){
    //search the most relevant match
    for (idx in response.features){
      var feature = response.features[idx];
      if (match_feature){
        if (match_feature.relevance < feature.relevance){
          match_feature=feature;
        }
      }
      else {
        match_feature=feature;
      }
    }
  }
  else{
    //case where the response is one relevant match
    match_feature=response;
  }

  return match_feature;
}
