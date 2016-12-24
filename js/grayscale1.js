/*!
 * Start Bootstrap - Grayscale Bootstrap Theme (http://startbootstrap.com)
 * Code licensed under the Apache License v2.0.
 * For details, see http://www.apache.org/licenses/LICENSE-2.0.
 */
// jQuery to collapse the navbar on scroll

$(document).ready(function(){
    $( "#phoneinput" ).keyup(function(){
        validate_phone_number();
    });

    $(document).on("click", ".btn", function(){
        $('#myModal').modal('show');
    });

    $(document).on("click", ".mbtn", function(){
        mixpanel.track('splash_page_action', {"action":"send_sms"})
        var phone = get_phone_number();
        sendAppTextLink(phone, function(){})
    });
    $('#phoneinput').keypress(function (e) {
        var key = e.which;
        if(key == 13) {
            $('#text-button-image').click();
        }
    }); 
});

function get_phone_number() {
    var phone = $('#phoneinput').val();
    return phone;
};

function validate_phone_number(){
    var phone = parseInt(get_phone_number());
    if (phone.toString().length === 10) {
        $('#text-button-image').css('opacity', '1');
	$('.mbtn').prop('disabled', false);
        return true;
    } else {
        $('#text-button-image').css('opacity', '.7');
	$('.mbtn').prop('disabled', true);
        return false;
    }
};

function sendAppTextLink (phone, success) {
    var text_message_url = 'http://www.gethotspotapp.com/api/text-app-link/';
    $.post(text_message_url, {phone : phone, promo : 1}, function(){
        success("SMS successful");
    });
}

$(window).scroll(function() {
    if ($(".navbar").offset().top > 50) {
        $(".navbar-fixed-top").addClass("top-nav-collapse");
    } else {
        $(".navbar-fixed-top").removeClass("top-nav-collapse");
    }
});

// jQuery for page scrolling feature - requires jQuery Easing plugin
$(function() {
    $('a.page-scroll').bind('click', function(event) {
        var $anchor = $(this);
        $('html, body').stop().animate({
            scrollTop: $($anchor.attr('href')).offset().top
        }, 1500, 'easeInOutExpo');
        event.preventDefault();
    });
});

// Closes the Responsive Menu on Menu Item Click
$('.navbar-collapse ul li a').click(function() {
    $('.navbar-toggle:visible').click();
});
