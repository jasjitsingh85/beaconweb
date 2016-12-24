var map;
var destlat;
var destlong;
var myScroll;
var checkedLocation = false;
var focusedInput = false;

function scrollToBottom() {
    var threadHeight = $('#conversation-thread').height();
    var windowHeight = $('.ui-content').height();
    if (windowHeight < threadHeight) {
        myScroll.scrollToElement('li:last-child', 1000);
    }
}

$(function(){
  $( ".join" ).bind( "tap", tapHandler );

  function tapHandler(event) {
      hotspot.joinHotspot(function(success) {
          changetoJoined();
          loadGuestList();
          mixpanel.track("mobile_going")
      });
  }
});

$(function(){
  $( "#conversation-refresh" ).bind( "tap", convoRefreshHandler);

  function convoRefreshHandler(event) {
//      $.mobile.loading('show');
      getMessages();
//      setTimeout( function() {
//          $.mobile.loading('hide')
//         }, 1000);
  };
});

$(function(){
  $( "#guest-refresh" ).bind( "tap", guestRefreshHandler );

  function guestRefreshHandler(event) {
      $.mobile.loading('show');
      loadGuestList();
      setTimeout( function() {
          $.mobile.loading('hide')
      }, 1000);
  }
});

function changetoJoined() {
    var joins = $(".join");
    joins.addClass('ui-disabled');
    $('#main-join-button div').addClass("main-going-button");
    for (var i = 0; i < joins.length; i++) {
        joins.eq(i).css("width","60px");
        if (joins.eq(i).find(".ui-btn-text").length === 0) {
            joins.eq(i).html("Going");
        } else {
            joins.eq(i).find(".ui-btn-text").text("Going");
        }
    }
    $('.join-button').html("Going").addClass("join-button-going").removeClass("join-invited");
}

  function loadHotspotPreview() {
      hotspot.getHotspot(function(success) {
          var hotspot = success.beacon;
          var name = hotspot.creator.first_name + " " + hotspot.creator.last_name;
          var time = get_time(hotspot.beacon_time);
          if (hotspot.follow === true) {
              changetoJoined()
          }
          destlat = hotspot.latitude;
          destlong = hotspot.longitude;
          if (hotspot.address === ""){
                addAddress(destlat, destlong);
          }
          var otherTense;
          if (hotspot.invite_number <= 1) {
            otherTense = " other...";
          } else {
            otherTense = " others...";
          }
          addRandomPictureToPreview(hotspot);
          var guestDescription = name + " and " + hotspot.invite_number  + otherTense;
          $('.hotspot-guests').find('span').html(guestDescription);
          $('.hotspot-message').find('span').html(hotspot.description);
          $('.hotspot-location').find('.address').html(hotspot.address);
          $('.time-field').html(time);
          get_location_if_permitted();
      });
  }

  function get_location_if_permitted() {
      if (checkedLocation === false) {
          navigator.geolocation.getCurrentPosition(foundLocation, noLocation);
          checkedLocation = true;
      }
  }

  function getRandomInt (min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function addRandomPictureToPreview(hotspot) {
      var pictureUrl;
      var numberOfImages = hotspot.image_urls.length;
      if ( numberOfImages > 0){
          var randomInteger = getRandomInt(0, numberOfImages - 1);
          pictureUrl = 'url(' + hotspot.image_urls[randomInteger] + ')';
      } else {
          pictureUrl = 'url(http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/mobile-placeholder.png)';
      }

      $('.hotspot-image').css("background-image", pictureUrl);
  }

  function addAddress (lat, long) {
      var url = "http://maps.googleapis.com/maps/api/geocode/json?latlng=" + lat + "," + long + "&sensor=true";
      $.get(url, function(data) {
          var address = data.results[0].address_components[0].short_name + " " + data.results[0].address_components[1].short_name;
          $('.hotspot-location').find('.address').html(address);
      });
  }

  function getDistanceFromLatLonInMi(lat1,lon1,lat2,lon2) {
      var R = 6371; // Radius of the earth in km
      var dLat = deg2rad(lat2-lat1);  // deg2rad below
      var dLon = deg2rad(lon2-lon1);
      var a =
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
        Math.sin(dLon/2) * Math.sin(dLon/2)
        ;
      var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
      var d = R * c; // Distance in km
      return convertKmToMiles(d);
  }

  function convertKmToMiles(distanceInKm) {
      return distanceInKm * .621371;
  }

  function deg2rad(deg) {
      return deg * (Math.PI/180)
  }

  function get_time(unixTime) {
      var date = new Date(unixTime * 1000);
      var hours = date.getHours();
      var minutes = date.getMinutes();
      var ampm = hours >= 12 ? 'pm' : 'am';
      hours = hours % 12;
      hours = hours ? hours : 12; // the hour '0' should be '12'
      minutes = minutes < 10 ? '0'+minutes : minutes;
      var strTime = hours + ':' + minutes + ' ' + ampm;
      return strTime;
}

  function foundLocation(position) {
       var currentLat = position.coords.latitude;
       var currentLong = position.coords.longitude;
       var distanceInMiles = "( " + (getDistanceFromLatLonInMi(currentLat, currentLong, destlat, destlong)).toFixed(1) + "mi )";
       $('.hotspot-location').find('.distance').html(distanceInMiles);
       var openMapURL = "http://maps.apple.com/maps?saddr=" + currentLat + "," + currentLong + "&daddr=" + destlat + "," + destlong;
       $(".hotspot-location").find('a').attr("href",openMapURL);
  }

  function noLocation() {
        alert('Could not find location');
  }


  function loadGuestList() {
      hotspot.getGuestList(function(success){
          var here_list = success.here;
          var going_list = success.going;
          var invited_list = success.invited;

          $('#guest-listview').empty();

          for (var x = 0; x < here_list.length; x++) {
              var here_name = here_list[x];
              var here_row = '<li class="ui-li ui-li-static ui-btn-up-c ui-li-last"><div class="ui-grid-a"><div class="ui-block-a"><span class=invitee-text>' + here_name + '</span></div><div class="ui-block-b"><img class="invitee-status" src="http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/status-here.png"></div></div></li>';
              $("#guest-listview").append(here_row);
          }

          for (var i = 0; i < going_list.length; i++) {
              var going_name = going_list[i];
              var going_row = '<li class="ui-li ui-li-static ui-btn-up-c ui-li-last"><div class="ui-grid-a"><div class="ui-block-a"><span class=invitee-text>' + going_name + '</span></div><div class="ui-block-b"><img class="invitee-status" src="http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/status-going.png"></div></div></li>';
              $("#guest-listview").append(going_row);
          }

          for (var n = 0; n < invited_list.length; n++) {
              var invited_name = invited_list[n];
              var invited_row = '<li class="ui-li ui-li-static ui-btn-up-c ui-li-last"><div class="ui-grid-a"><div class="ui-block-a"><span class=invitee-text>' + invited_name + '</span></div><div class="ui-block-b"><img class="invitee-status" src="http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/status-invited.png"></div></div></li>';
              $("#guest-listview").append(invited_row);
          }
      });
  }

  function checkIfMessageExists(position, message) {
      var messageInThread = $('#conversation-thread li').eq(position).data('messageid');
      var messageInObject = message.id;
      if (messageInThread === messageInObject) {
          return true;
      } else {
          return false;
      }
  }

function getRightHtmlForMessageThread(thread_values) {
    var thread_row;
    if (hotspot.contact_phone.toString() !== thread_values.contact_phone){
        thread_row = '<li class="user ' + thread_values.liClass + ' ui-li ui-li-static ui-btn-up-c"' + thread_values.message_id +'><div class="ui-grid-a"><div class="ui-block-a"><img class="thread-image" src="' + thread_values.profile_pic + '"><span class="thread-name">' + thread_values.name + '</span></div><div class="ui-block-b">' + thread_values.message + '</div></div></li>';

    } else {
        thread_row='<li class="sender ' + thread_values.liClass + ' ui-li ui-li-static ui-btn-up-c"' + thread_values.message_id +'><div class="ui-grid-a"><div class="ui-block-a">' + thread_values.message + '</div><div class="ui-block-b"><img class="thread-image" src="' + thread_values.profile_pic + '"><span class="thread-name">' + thread_values.name + '</span></div></div></li>';
    }
    return thread_row
}

function addMessageImage(thread_values, message){
    var thread_row;
    thread_values.message = '<a href="' + message.image.image_url +'" target="_blank"><img class="thumbnail-image" src="' + message.image.image_url + '" /></a>';
    thread_values.liClass = "li-image";
    thread_row = getRightHtmlForMessageThread(thread_values);
    return thread_row
}

function addMessageString(thread_values, message){
    var thread_row;
    var messageLength = message.message.length;

    if (messageLength < 25) {
        thread_values.messageClass = "thread-message";
    } else if (messageLength > 25 && messageLength < 75) {
        thread_values.messageClass = "thread-message-two-line";
    } else {
        thread_values.messageClass = "thread-message-multiline";
    }

    thread_values.message = '<span class="' + thread_values.messageClass + '">' + message.message + '</span>';
    thread_values.liClass = "thread-string";

    if (message.chat_type==="HM") {
        thread_row = '<li class="user ui-li ui-li-static ui-btn-up-c"' + thread_values.message_id + '><div class="ui-grid-a"><div class="ui-block-a"><img class=thread-image src="https://s3.amazonaws.com/hotbot-images/HotbotNeutral.png"><span class="thread-name">Hotbot</span></div><div class="ui-block-b"><span class="hotspot-announcement ' + thread_values.messageClass + '">' + message.message + '</span></div></div></li>';
    } else {
        thread_row = getRightHtmlForMessageThread(thread_values);
    }
    return thread_row
}

function getInitialThreadRowValues (message) {
    var thread_row_values = {};
    thread_row_values.message_id = "data-messageID=" + message.id;

    if (message.sender != null) {
        thread_row_values.name = message.sender.user.first_name;
        thread_row_values.profile_pic = message.sender.avatar_url;
    } else {
        thread_row_values.name = message.contact.name;
        thread_row_values.profile_pic = message.profile_pic;
    }

    if (message.contact !== null) {
        thread_row_values.contact_phone = message.contact.normalized_phone;
    } else {
        thread_row_values.contact_phone = null;
    }
    return thread_row_values
}

function addMessageToThread(message) {
    var thread_row;
    var thread_row_values;
    thread_row_values = getInitialThreadRowValues(message);
    if (message.message !== null) {
        thread_row = addMessageString(thread_row_values, message);
    } else {
        thread_row = addMessageImage(thread_row_values, message);
    }
    $('#conversation-thread').append(thread_row);
}

  function getMessages() {
      hotspot.getMessages( function(success) {
            var messages = success.messages;
            for (var i = 0; i < messages.length; i++) {
                var message = messages[i];
                if (checkIfMessageExists(i, message) !== true) {
                    addMessageToThread(message)
                }
            }
        });
      refreshPageScroll(1000)
  }

function refreshConversationWindowSize() {
    var convo_top = $('#conversation').css('padding-top');
    var convo_bottom = $('#conversation').css('padding-bottom');
    $("#wrapper").css('top', convo_top);
    $("#wrapper").css('bottom', convo_bottom);
}

function refreshPageScroll(mseconds) {
    refreshConversationWindowSize();
    var timedelay = mseconds ? mseconds : 0;
    $.mobile.loading('show');
    setTimeout(function () {
        myScroll.refresh();
        scrollToBottom();
        $.mobile.loading('hide');
    }, timedelay);
}

function hideKeyboard() {
//    $('input, textarea, select').on('focus', function () {
////        console.log("input focus");
//    $('footer').css({'position':'absolute'});
//        focusedInput = $(this);refreshPageScroll(0);
//    }).blur(function () {
//    console.log("input blur");
    $('footer').css({'position':'fixed'});
    $("#message").blur();
	refreshPageScroll(100) ;
//    });
}
//
//jQuery.fn.center = function () {
//    this.css("position","absolute");
//    this.css("top", Math.max(0, (($(window).height() - $(this).outerHeight()) / 2) +
//                                                $(window).scrollTop()) + "px");
//    return this;
//}

$(document).delegate("#guest-list", "pageshow", function() {
    loadGuestList();
});

$(document).delegate("pagecreate", "#preview", function() {
   loadHotspotPreview();
});

$(document).delegate("#preview", "pageshow", function() {
   loadHotspotPreview();
   navigator.geolocation.getCurrentPosition(foundLocation, noLocation);
});

$(document).delegate("#conversation","pageshow", function() {
  getMessages();
});

$(document).ready(function(){
    $(function() {
            FastClick.attach(document.body);
    });
    $("#message-submit").bind("submit", function(event){
      event.preventDefault();
      var message = $("#message").val();
        if (message.length > 0) {
            hotspot.postMessage(message, function() {
                $("#message").val("");
                getMessages();
            });
        }
        hideKeyboard();
        scrollToBottom();
    });
});



