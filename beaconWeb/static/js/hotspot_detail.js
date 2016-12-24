var message_template_string = '<li class="message-string" data-user_id="{0}" data-type="{1}" data-id="{2}"><div class="sender-container"><img class="message-pic" src={3}><span class="message-sender">{4}</span></div><span class="message-content">{5}</span></li>';
var message_template_image = '<li class="message-image" data-user_id="{0}" data-type="{1}" data-id="{2}"><div class="sender-container"><img class="message-pic" src={3}><span class="message-sender">{4}</span></div><img class="message-content" src="{5}"></li>';
var guest_template = '<li><span class="guest-name">{0}</span><img class="guest-status" src={1}></li>';
var chat_bubbles = new Array("#f2d7e8", "#ffdffd", "#dcd7f2", "#dfe9ff", "#d7ecf2", "#cfffef", "#deffe0", "#f1ffcb", "#fffbcf", "#ffe1c6", "#ffcdd3", "#fbcef0");
var current_hotspot;
var iOS = ( navigator.userAgent.match(/(iPad|iPhone|iPod)/g) ? true : false );
var openMapURL;
var iPhone;
var smartbanner = false;
var container_height_set = false;
var map_and_info_is_visible = true;
var keyboard_is_visible = false;
var google_map =
{
	map: null,
	markers : [],
    latitude: null,
    longitude: null,
	initialize: function(lat, lng)
	{
        this.latitude = lat;
        this.longitude = lng;
		var latlng = new google.maps.LatLng(this.latitude, this.longitude);

		var mapOptions = {
		  center: latlng,
		  zoom: 15,
		  disableDefaultUI: true,
		  draggable: false
		};

		this.map = new google.maps.Map(document.getElementById("map-canvas"),
		    mapOptions);

        this.move_to(lat, lng);

	},
	add_marker: function(latitude, longitude)
	{
  		this.delete_markers();
  		var image = new google.maps.MarkerImage("http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/orangeMarker.png", null, null, null, new google.maps.Size(50,50));
  		var latlng = new google.maps.LatLng(latitude, longitude);
  		var marker = new google.maps.Marker({
	    	position: latlng,
	    	icon: image,
	    	map: this.map
  		});
  		this.markers.push(marker);
	},
	clear_markers : function()
	{
		this.set_all_map(null);
	},
	set_all_map : function()
	{
		for (var i = 0; i < this.markers.length; i++) {
    		this.markers[i].setMap(null);
  		}
	},
	delete_markers : function()
	{
		this.clear_markers();
		this.markers = [];
	},
	move_to: function(lat, lng)
	{
		var latlng = new google.maps.LatLng(lat, lng);
		this.add_marker(lat, lng);
		this.map.panTo(latlng);
	},
	zoom_in_on_load: function()
	{
		google.maps.event.addListenerOnce(this.map,"zoom_changed", function() {
     		smoothZoom(this.map, 10, this.map.getZoom()); // call smoothZoom, parameters map, final zoomLevel, and starting zoom level
  		});
	}
}

function fade_out_send_message() {
	$('.send-message-container').fadeOut(100);
}

function fade_in_send_message() {
	$('.send-message-container').fadeIn(100);
}

function hide_map_and_info() {
	$('.notification-center').hide();
	var new_height = map_and_info_height - 48;
	// $('.notification-center').hide();
	$('.main-detail-container').transition({y:-new_height});
	$('#map-canvas').transition({y:-20});
	// $('.nav').css("margin-top", "48px");

}

function show_map_and_info() {
	// $('.send-message-box').blur();
	// $('.main-detail-container').transition({ y: 0}).transition({"height":original_chat_height + "px"});
	$('#map-canvas').transition({y:0});
	$('.main-detail-container').transition({ y: 0});
	// $('.nav').css("margin-top", "0px");
	// $('.notification-center').show();
	// $('.chat-and-guests').css("height", original_chat_height + "px");
//	google_map.move_to();
}

function resize_chat_and_guests_for_tap() {
	var new_chat_height;
	var speed;
	if (map_and_info_is_visible === true) {
		new_chat_height = window_height - 48 - nav_height;
		speed = 50;
	} else {
		new_chat_height = original_chat_height;
		speed = 500;
	}
	$('.chat-and-guests').transition({"height": new_chat_height + "px", duration: speed});
	$('.main-container').css("height", window_height);
	$('body').css("height", window_height);
	$('html').css("height", window_height);
}

function resize_chat_and_guests_for_keyboard() {
    if (smartbanner === true) {
        smart_banner_adjust = 118;
    } else {
        smart_banner_adjust = 0;
    }
    if (iOS) {
        if (keyboard_is_visible) {
            var new_window_height = window_height - 250 + smart_banner_adjust;
        } else {
            var new_window_height = window.innerHeight;
        }
    } else {
         var new_window_height = window.innerHeight;
    }
	var chat_height = new_window_height - 48 - nav_height;
	hide_map_and_info();
	$('.chat-and-guests').transition({"height" : chat_height + "px"});
	$('.main-container').css("height", new_window_height);
	$('body').css("height", new_window_height);
	$('html').css("height", new_window_height);
	setTimeout(function(){
		fade_in_send_message();
		// $('.notification-center').show();
//		scroll_to_bottom_of_message_thread();
        scroll_to_top_of_container();
	}, 100);
	
}



// Application Helper Functions
function randomFromInterval (from,to) {
  return Math.floor(Math.random()*(to-from+1)+from);
}

function get_distance_string(distance_in_feet) {
	var distance_in_miles = precise_round((distance_in_feet/5280), 2);
	var distance_in_feet = precise_round(distance_in_feet, 0);
	if (distance_in_miles < 0.25) {
		return distance_in_feet + " ft"
	} else {
		return distance_in_miles + " mi"
	}
}

function getDistanceFromLatLonInFt(lat1,lon1,lat2,lon2) {
  var R = 6371; // Radius of the earth in km
  var dLat = deg2rad(lat2-lat1);  // deg2rad below
  var dLon = deg2rad(lon2-lon1);
  var a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
    Math.sin(dLon/2) * Math.sin(dLon/2)
    ;
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  var d = R * c * 3280.84; // Distance in km
  return d;
}

function precise_round(num,decimals) {
    return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals);
}

function deg2rad(deg) {
  return deg * (Math.PI/180)
}

function format_time(date) {
  var hours = date.getHours();
  var minutes = date.getMinutes();
  var ampm = hours >= 12 ? 'pm' : 'am';
  hours = hours % 12;
  hours = hours ? hours : 12; // the hour '0' should be '12'
  minutes = minutes < 10 ? '0'+minutes : minutes;
  var strTime = hours + ':' + minutes + ' ' + ampm;
  return strTime;
}

function get_address(hotspot, success) {
	if (hotspot.address !== "") {
		success(hotspot.address);
	} else {
		get_reverse_geocode(hotspot.latitude, hotspot.longitude, function(response) {
			success(response);
		});
	}
}

function selected(target) {
	$(target).addClass("button-selected");
}

function unselected(target) {
	$(target).removeClass("button-selected");
}

function load_hotspot() {
	hotspot.getHotspot(function(response){
        current_hotspot = response.beacon;
        saw_hotspot();
	    refresh_hotspot_detail(current_hotspot);
	    update_join_button();
        add_event_listeners();
        navigator.geolocation.getCurrentPosition(foundLocation, noLocation);
	    setTimeout(function() {
                set_element_percentage_heights();
                $('.loading-container').fadeOut();
//              google_map.move_to(current_hotspot.latitude, current_hotspot.longitude);
	            setTimeout(function(){
                    set_element_percentage_heights();
                }, 2000);
            }, 1000);
        });
}

 function foundLocation(position) {
       var hotspot_lat = current_hotspot.latitude;
       var hotspot_lng = current_hotspot.longitude;
       google_map.initialize(hotspot_lat, hotspot_lng);
       var currentLat = position.coords.latitude;
       var currentLong = position.coords.longitude;
       var distanceInMiles = "( " + (getDistanceFromLatLonInMi(currentLat, currentLong, hotspot_lat, hotspot_lng)).toFixed(1) + "mi )";
       $('.distance').html(distanceInMiles);
       openMapURL = "http://maps.apple.com/maps?saddr=" + currentLat + "," + currentLong + "&daddr=" + hotspot_lat + "," + hotspot_lng;
       $(".hotspot-location").attr("href",openMapURL);
  }

  function noLocation() {
        console.log('Could not find location');
  }

function update_join_button(){
    if (current_hotspot.follow === true) {
        change_to_going();
    } else {
        change_to_join();
    }
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

function change_to_join() {
   $(".hotspot-button").html("Join").css('opacity',"1");
   $(".hotspot-button").hammer().on('touchstart', function(){
        hotspot.joinHotspot(function(){
           change_to_going();
           load_messages();
           load_guests();
           mixpanel.track("mobile_going");
        });
   });
}

function change_to_going() {
    $(".hotspot-button").html("Going").css('opacity',"0.5");
}

function refresh_hotspot_detail(hotspot) {
    refresh_elements();
	update_hotspot_info(hotspot);
	$('.guest-thread').empty();
	load_messages();
   	load_guests();
}

function refresh_elements() {
	$('.main-detail-container').transition({ y: 0});
}

var messages_global;
function load_messages() {
	hotspot.getMessages(function(success){
		messages_global = success.messages;
        $('.message-thread').empty();
		var messages = success.messages;
		load_each_message(messages);
		style_messages();
//		scroll_to_bottom_of_message_thread();
		// set_element_percentage_heights();
	});
}

function style_messages() {
	$('.message-string').each(function(index){
		if ($(this).data('type') === "UM") {
			var message_length = $(this).find('.message-content').html().length;
			var current_width = parseInt($(this).find('.message-content').css('width'));
			var color_index = parseInt($(this).data('user_id'))%12;
			if (message_length > 40) {
				$(this).find('.message-content').css("width", "65%").css("text-align","left").css("line-height","1.25").css("padding", "2% 5%");
			}

		}
		$(this).find('.message-content').css("background", chat_bubbles[color_index]);
		// $(this).find('.message-content').css("width", new_width + "px");
	});
}

var window_height;
var window_width;
var nav_height;
var original_chat_height;
var map_and_info_height;
function set_element_percentage_heights() {
    window_height = window.innerHeight;
    window_width = window.innerWidth;
	map_and_info_height = $('.map-and-info').height();
	nav_height = (0.08 * window_height);
	original_chat_height = 0.45 * window_height;
    $('.send-message-container').css("height", (0.08 * window_height) + "px");
    $('.nav').css("height", nav_height + "px");
    $('.preview-top-container').css("height", (0.25 * window_height) + "px");
    $('.preview-bottom-container').css("height", (0.15 * window_height) + "px");
    $('.chat-and-guests').css("height", original_chat_height + "px");
}	

function load_each_message(messages) {
	for (var i = 0; i < messages.length; i++) {
		current_message = get_current_message(messages[i]);
		$('.message-thread').append(current_message);
		if (messages[i].contact !== null) {
			format_message(messages[i]);
		}
	}
    scroll_to_bottom_of_message_thread();
}


function format_message(message) {
    if (message.contact.normalized_phone === hotspot.contact_phone && message.chat_type !== "HM") {
        $('.message-thread li').last().find('.sender-container').addClass("float-right");
        $('.message-thread li').last().find('.message-content').addClass("float-right");
    }
}

var current_message;
function replace_string(template, message) {
	current_message = message;
	var name = get_message_sender(message);
	var profile_pic = message.profile_pic;
	var message_id = get_message_id(message);
	var this_message = template.replace("{0}", message_id).replace("{1}", message.chat_type).replace("{2}", message.id).replace('{3}', profile_pic).replace('{4}', name);
	return this_message;
}

function get_message_id(message) {
	if (message.sender !== null) {
		return message.sender.user.id;
	} else {
		return message.contact.id;
	}
}

function get_current_message(message) {
	if (message.image) {
		this_message = replace_string(message_template_image, message)
		this_message = this_message.replace('{5}', message.image.image_url);
	} else if (message.message){
		this_message = replace_string(message_template_string, message)
		this_message =  this_message.replace('{5}', message.message);
	}
	return this_message;
}

function get_message_sender(message) {
	if (message.chat_type==="HM") {
		return "Hotbot"
	} else if (message.chat_type==="UM") {
		return get_user_first_name_from_message(message);
	}
}

function get_user_first_name_from_message(message) {
	if (message.contact === null) {
		return message.sender.user.first_name;
	} else {
		var first_name_from_contact = message.contact.name.split(" ")[0];
		return first_name_from_contact;
	}
	
}

function saw_hotspot() {
	hotspot.sawInvite(current_hotspot.id, function() {
		console.log("User saw invitation");
	});
}

function load_guests() {
    hotspot.getGuestList(function(success){
        var guests = success;
        $('.guest-thread').empty();
        load_here(guests.here);
        load_going(guests.going);
        load_invited(guests.invited);
        $('.guests').html(get_guest_string(guests));
    });
}

function load_here(guests) {
	for (var i = 0; i < guests.length; i++) {
        var current_guest = guest_template.replace("{0}", guests[i]).replace("{1}", "http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/statusHere.png");
        $('.guest-thread').append(current_guest);
	}
}

function load_going(guests) {
	for (var i = 0; i < guests.length; i++) {
        var current_guest = guest_template.replace("{0}", guests[i]).replace("{1}", "http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/statusGoing.png");
        $('.guest-thread').append(current_guest);
	}
}

function load_invited(guests) {
	for (var i = 0; i < guests.length; i++) {
        var current_guest = guest_template.replace("{0}", guests[i]).replace("{1}", "http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/statusInvited.png");
        $('.guest-thread').append(current_guest);
	}
}

function scroll_to_bottom_of_message_thread() {
   	$("#wrapper").scrollTo(".message-thread li:last-child", 1000);
}

function scroll_to_top_of_container() {
	$('html,body').animate({scrollTop:0},0);
}

function get_status(guest) {
	if (guest.status === "invited") {
		return "images/statusInvited.png";
	} else if (guest.status === "going" ) {
		return "images/statusGoing.png";
	} else if (guest.status === "here" ) {
		return "images/statusHere.png";
	}
}

function remove_active() {
	$('.active').removeClass("active");
}

function add_active (self) {
	self.addClass('active');
}

function switch_from_chat_to_guest(self) {
	self.find('img').attr("src","http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/chatButtonSelected@2x.png");
	self.find('img').transition({ scale: [1.25, 1.25], duration: 100 }).transition({ scale: [1, 1], delay: 25 });
	$('.guest-tab').find('img').attr("src","http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/invitedButtonNormal@2x.png");
	$('.guest-list').hide();
	$('.chat-list').show();
    setTimeout(function(){
        scroll_to_bottom_of_message_thread();
    }, 500);
}

function switch_from_guest_to_chat(self) {
	$('.chat-tab').find('img').attr("src","http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/chatButtonNormal@2x.png");
	self.find('img').attr("src","http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/invitedButtonSelected@2x.png");
	self.find('img').transition({ scale: [1.25, 1.25], duration: 100 }).transition({ scale: [1, 1], delay: 25 });
	$('.chat-list').hide();
	$('.guest-list').show();
}

function toggle_map_and_info() {
	fade_out_send_message();
	if (map_and_info_is_visible === false) {
		resize_chat_and_guests_for_tap();
		show_map_and_info();
		map_and_info_is_visible = true;
	} else {
		hide_map_and_info();
		resize_chat_and_guests_for_tap();
		map_and_info_is_visible = false;
	}

	setTimeout(function(){
		fade_in_send_message();
	}, 300);
}

function select_chat(self) {
	if (self.hasClass('active')) {
		toggle_map_and_info();
	} else {
		switch_from_chat_to_guest(self);
	}
	remove_active();
	add_active(self);
}

function select_guests(self) {
	if (self.hasClass('active')) {
		toggle_map_and_info();
	} else {
		switch_from_guest_to_chat(self);
	}
	remove_active();
	add_active(self);
}

function remove_touch_events() {
	$('.chat-tab, .guest-tab').hammer().off('touch');
	$('.chat-tab, .guest-tab').hammer().off('release');
}

function add_event_listeners() {
	remove_touch_events();

	$('.chat-tab').hammer().on('touch', function() {
		var chat_image = $(this).find('img');
		selected(chat_image);
	});

	$('.chat-tab').hammer().on('release', function() {
		var self = $(this);
		unselected(self.find('img'));
		select_chat(self);
	});

	$('.guest-tab').hammer().on('touch', function() {
		var chat_image = $(this).find('img');
		selected(chat_image);
	});

	$('.guest-tab').hammer().on('release', function() {
		var self = $(this);
		unselected(self.find('img'));
		select_guests(self);
	});

	add_message_event_listener();
}

function add_message_event_listener() {
	$('#send-message').on('submit', function(event){
		event.preventDefault();
		post_message();
	});
}

function post_message() {
	var message_content = $('.send-message-box').val();
	add_message_to_thread();
	if (message_content !== "") {
		hotspot.postMessage(message_content, function() {
            hotspot.getMessages(function(success){
                update_message_thread(success.messages);
            });
		});
	}
}

function add_message_to_thread() {
	$('.send-message-box').val("");
	$(".send-message-box").blur();
}

function get_temporary_message(message) {
	var temp_message = message_template_string.replace("{2}", "-1").replace("{3}", user_info.avatar_url).replace("{4}", user_info.first_name).replace("{5}", message);
	return temp_message;
}

function update_message_thread(messages) {
	for (var i = 0; i < messages.length; i++) {
		if (messages[i].id !== $('.message-thread li').eq(i).data("id")) {
			var current_message = get_current_message(messages[i]);
			$('.message-thread li').eq(i - 1).after(current_message);
			if (messages[i].contact.normalized_phone === hotspot.contact_phone) {
				$('.message-thread li').eq(i).find('.sender-container').css("float","right");
				$('.message-thread li').eq(i).find('.message-content').css("float","right");
			}
		}
	}
	style_messages();
	scroll_to_bottom_of_message_thread();
}

function update_hotspot_info(hotspot) {
	$('.time').html(format_unix_time(hotspot.beacon_time));
	$('.description').html(hotspot.description);
	get_address(hotspot, function(success){
		$('.address').html(success);
	});
}

function get_address(hotspot, success) {
	if (hotspot.address !== "") {
		success(hotspot.address);
	} else {
		get_reverse_geocode(hotspot.latitude, hotspot.longitude, function(response) {
			success(response);
		});
	}
}

function get_reverse_geocode(latitude, longitude, success) {
	var reverse_geocode_url = "http://maps.googleapis.com/maps/api/geocode/json?latlng={0},{1}&sensor=true";
	var url = reverse_geocode_url.replace("{0}", latitude).replace("{1}", longitude);
	console.log(url);
	try {
		$.get(url, function( data ) {
			var address = data.results[0].address_components;
		 	success(address[0].short_name + " " + address[1].short_name);
		});
	} catch(error) {
		console.log(error);
	}

}

function format_unix_time(unixTime) {
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

function get_guest_string(guests) {
    var guests_here = guests.here.length;
    var total_guests = guests_here + guests.going.length + guests.invited.length;
    return guests_here + " here, " + total_guests + " invited";
}

function get_guest_name(guest) {
	if (guest.profile !== null) {
		return guest.profile.user.first_name;
	} else {
		return guest.contact.name.split(" ")[0]
	}
}

function detect_iphone() {
   var iHeight = window.screen.height;
    if (iHeight == (960/2)){
        iPhone = 4;
        setTimeout(function(){
            if (window.innerHeight < 320) {
                    smartbanner = true;
            }
        }, 500);
    } else if (iHeight == (1136/2)) {
        iPhone = 5;
        setTimeout(function(){
            if (window.innerHeight < 380) {
                    smartbanner = true;
            }
        }, 500);
    } else {
        iPhone = null;
    }
}

jQuery.fn.scrollTo = function(elem, speed) { 
    $(this).animate({
        scrollTop:  $(this).scrollTop() - $(this).offset().top + $(elem).offset().top 
    }, speed == undefined ? 1000 : speed); 
    return this; 
}

$(document).ready(function(){
    $(function() {
        FastClick.attach(document.body);
    });

    if (iOS){
        detect_iphone();
    }
    load_hotspot();

    $('.hotspot-header').hammer().on('touchstart', function(){
         location.href = "http://www.GetHotspotApp.com?src=webview";
    });

	$('.send-message-container').hammer().on('touchstart', function(){
		if (container_height_set === false) {
			set_element_percentage_heights();
			container_height_set = true;
//			$('.send-message-box').click();
		}
	});

	$('.send-message-box').on("focus", function(){
		keyboard_is_visible = true;
        if (iOS) {
            resize_chat_and_guests_for_keyboard();
        }
		// fade_out_send_message();
		hide_map_and_info();
	});

	$('.send-message-box').on("blur", function(){
		keyboard_is_visible = false;
        if (iOS) {
            resize_chat_and_guests_for_keyboard();
        }
	});

    $('.preview-top-container').hammer().on('touchstart', function(){
        //TODO
        location.href = openMapURL;
    });

	$(window).on('resize', function(){
        if (iOS === false) {
            resize_chat_and_guests_for_keyboard();
        }
	});

    window.addEventListener('onorientationchange', function () {
        if (window.orientation % 180 === 0) {
            load_hotspot();
        }
    }, true);

});
