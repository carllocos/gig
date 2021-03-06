/**
weather_util module are api calls to openweathermap service.
This module assumes that jquery is loaded and weather_config is correctly set.
**/


var weather_config = {'appid': "YOUR_APP_API", 'http_protocol': "httpOrHttps"};
var forecast_base_url = 'api.openweathermap.org/data/2.5/weather?';
var img_base_url = 'openweathermap.org/img/w/';


function make_url(long, lat){
  protocol=weather_config['http_protocol'];
  return protocol + forecast_base_url + 'lat=' + lat + '&lon='+long + '&appid='+weather_config['appid'];
}

function get_weahter_icon_url(icon_name){
  protocol=weather_config['http_protocol'];

  return protocol+ img_base_url + icon_name + '.png';
}

function get_minimal_forecast(long, lat, success_func, failure_func = default_failure) {
  //This function will send an ajax request to openweathermap and only fetch min, max, tem,
  url= make_url(long, lat);
  minimize_response = function(response){

    weather=response['weather'][0];
    main=response['main'];
    new_response ={
      'description': weather['description'],
      'weather_icon': get_weahter_icon_url(weather['icon']),
      'temp_min': kelvin_to_c(main["temp_min"]),
      'temp_max': kelvin_to_c(main["temp_max"]),
      'temp': kelvin_to_c(main["temp"]),
    }
    success_func(new_response);
  };

  sendRequest(url, minimize_response, failure_func);
}


function kelvin_to_c(k){
  var cel= k - 273.15;
  return cel.toFixed(2);
}


function get_forecast(long, lat, success_func, failure_func = default_failure) {
  url= make_url(long, lat);
  sendRequest(url, success_func, failure_func);
}



function sendRequest(url_l, success_func, failure_func  = default_failure){
  $.ajax({
    type: "GET",
    url: url_l,
    dataType: 'json',
    success: success_func,
    statusCode: {
      401: failure_func
    }
  });
}

function default_failure(response) {
  alert(response['message']);
}
