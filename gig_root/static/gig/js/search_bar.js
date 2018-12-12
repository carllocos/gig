/**
search.js has as purpose to implement all function
related to search.

Some assumptions are made to correctly use this module:
1. jquery is being imported
2. bootstrap is being imported
3. The object `searchConfig` has been correctly intiated.
**/

var searchConfig = {
  csrfmiddlewaretoken: "ENTER VALUE",
  id_input: "enter id search input field",
  url_suggestions: "The url for search suggestions here",
  // url_search: "The url to where to perform the search request",
  id_search_group: "The id of the item where to display the suggestions",
}


function activateSuggestions(callb){
  /*Function that will bind to input field with id `searchConfig.id_input` a 'keyup' listener.
  Each time a user types a key, the backend get a request to find bands and events that matches the value of the field.
  The results are provided to a callback called 'callb'.
  */

  $(`#${searchConfig.id_input}`).keyup(function(){
    $query=$(`#${searchConfig.id_input}`);
    if($query.val() !=''){
      $.ajax({
        type: "GET",
        url: searchConfig.url_suggestions,
        data:{
          query: $query.val(),
          csrfmiddlewaretoken: searchConfig.csrfmiddlewaretoken,
        },
        dataType: 'json',
        success: callb
      });
    }
  });
}


function removeListGroup() {
  /*Function that will remove the children element of the element with id `searchConfig.id_search_group`
  */
  var $group=$(`#${searchConfig.id_search_group}`);
  $group.empty();

}

function addSuggestions(suggestions){
  /*Function that will transform the `suggestions` into li elements and append them to
  element with id `searchConfig.id_search_group`
  */
  var $group=$(`#${searchConfig.id_search_group}`);

  for(band_idx in suggestions.bands){
    var band=suggestions.bands[band_idx];
    var e = `<li class="list-group-item"><a href="${band.url}">${band.name}</a><p style="display:inline" class="font-italic">:band</p></li>`;
    $group.append(e);
  }

  for(event_idx in suggestions.events){
    var event = suggestions.events[event_idx];
    var e = `<li class="list-group-item"><a href="${event.url}">${event.name}</a><p style="display:inline" class="font-italic">:event</p></li>`;
    $group.append(e);
  }

  $group.css('display', 'block');

}
