

/**
convenience function to update tags to express success or fail messages.
selectors: a list of selectors for elements to be updated.
remove_cl: a class to remove e.g. text-danger in bootstrap
add_cl: a clas to add to a element e.g. text-success to express success
msgs: list of messages. The text value of the element will be replaced by a msg
**/
function updateHelpMessage(selectors, remove_cl, add_cl, msgs){
  var i = 0;
  for(i; i< selectors.length; i++){

    selector = selectors[i];
    $(selector).each(function(index){
      el = $(this);
      msg=msgs[i]
      el.removeClass(remove_cl);
      el.addClass(add_cl);
      el.text(msg);
      el.css('visibility', 'visible');
    });
  }
}

//convenience function to update the name of the user in the nav-bar
function updateNameNavBar(new_name){
  $("#profile_first_name").each(function(index){
    $(this).text(new_name);
  })
}




function ajaxListener(selector, csrf_token, url, key, value){

  $.ajax({
    type: "GET",
    url: url,
    data: { key: value , csrfmiddlewaretoken: csrf_token, },
    dataType: 'json',
    success: function(data){

      if(data.has_data){
        new_cls="text-danger";
        rem_cls="text-success"
        msg="email is already registered";
      }
    }});
  }

var delay = (function(){
    var timer = 0;
    return function(callback, ms){
        clearTimeout(timer);
        timer = setTimeout(callback, ms);
      };
    })();
