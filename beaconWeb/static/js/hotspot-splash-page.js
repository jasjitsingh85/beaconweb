var isVideoWatched = false;
var isTextSent = false;

//var tag = document.createElement('script');
//
//tag.src = "https://www.youtube.com/iframe_api";
//var firstScriptTag = document.getElementsByTagName('script')[0];
//firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

$(document).ready(function(){

//    $('.iphone').waypoint(function(direction){
//        if( direction === "down") {
//           top_navbar_fade_out();
//        } else if (direction === "up") {
//           top_navbar_fade_in();
//        }
//    }, {offset:0});
//
//    $('.main-video-row').waypoint(function(direction){
//        if( direction === "down") {
//           bottom_navbar_fade_in();
//        } else if (direction === "up") {
//           bottom_navbar_fade_out();
//        }
//    }, {offset:50});
//
//    $('.watch-video').hover(function(){
//        $('.play-button').animate({top: '-10px'}, 550, "easeInOutBack");
//        setTimeout(function(){
//            $('.play-button-shadow').fadeTo(350, 0);
//        }, 200);
//        }, function() {
//        $('.play-button').animate({top: '10px'}, 550, "easeInOutBack");
//        setTimeout(function(){
//            $('.play-button-shadow').fadeTo(350, 1);
//        }, 200);
//    });

//    $('.phone-box').keyup(function(event){
//        if ($(this).val().length === 10) {
//            $('.second-box').focus();
//        }
//    });
//
//    $('.second-box').keyup(function(event){
//        if ($(this).val().length === 3) {
//            $('.third-box').focus();
//        }
//    });

    $('.phone-box').keyup(function(){
        if ($(this).val().length === 10) {
//            alert("working");
//            $('#text-button-image').animate({top: '-10px'}, 250, "easeInOutBack");
//            setTimeout(function(){
//                $('#text-button-text').fadeIn();
//            }, 50)
            validate_phone_number();
        } else {
//            $('#text-button-image').animate({top: '0px'}, 350, "easeInOutBack");
//                setTimeout(function(){
//                    $('#text-button-text').fadeOut(100);
//                }, 10)
            validate_phone_number();
        }
    });

//    $('.phone-box').blur(function(){
//        $('#text-button-image').animate({top: '0px'}, 350, "easeInOutBack");
//        setTimeout(function(){
//            $('#text-button-text').fadeOut(100);
//        }, 10)
//    });

    $('#text-button-image').click(function(){
        mixpanel.track('splash_page_action', {"action":"send_sms"});
//        $('#text-button-image').hide();
//        $('#text-button-loader').css("display","block");
        var phone = get_phone_number();
        sendAppTextLink(phone, function(){
//            $('#text-button-loader').css("display","none");
//            $('#text-sent').fadeIn();
//            setTimeout(function(){
//                $('#text-sent').hide();
//                $('#text-button-image').show();
//            }, 2000);


        })
    });
//
//    $('.text-container').hover(function(){
////        $('#text-button-image').animate({top: '-10px'}, 350, "easeInOutBack");
//        $('.text-app-to-phone').fadeIn();
////        setTimeout(function(){
////            $('#text-button-text').fadeIn(100);
////        }, 50)
//        }, function() {
////        $('#text-button-image').animate({top: '0px'}, 450, "easeInOutBack");
//        $('.text-app-to-phone').fadeOut();
////        setTimeout(function(){
////            $('#text-button-text').fadeOut(100);
////        }, 10)
//    });

//    add_hover_to_social_icons(".social-icon-container");
////    add_hover_to_social_icons("#twitter-icon");
////    add_hover_to_social_icons("#blog-icon");
////    add_hover_to_social_icons("#email-icon");
//
//    $('#facebook-share').click(function(){
//       FB.ui(
//          {
//            method: 'feed',
//            name: 'Check out Hotspot',
//            link: 'http://www.GetHotspotApp.com',
//            picture: 'http://s3-us-west-2.amazonaws.com/hotspot-static/static/static/img/hotspot-facebook-picture.png',
////            caption: 'Check this out',
//            description: 'Skip the texting back-and-forth. Hotspot is a new app that makes it easy to meet up with your friends in real life.'
//          },
//          function(response) {
//            if (response && response.post_id) {
//              alert('Post was published.');
//            } else {
//              alert('Post was not published.');
//            }
//          }
//        );
//    });

//    $('.watch-video').click(function(){
//        mixpanel.track('splash_page_action', {"action":"watch_video"});
//        scroll_to_video();
//    });
//
//    $('.share-video span').click(function(){
//        scroll_to_video();
//    });
});

function validate_phone_number(){
    var phone = parseInt(get_phone_number());
    if (phone.toString().length === 10) {
        $('#text-button-image').css('opacity', '1');
        return true;
    } else {
        $('#text-button-image').css('opacity', '.5');
        return false;
    }

}

function get_phone_number() {
    var phone = $('.phone-box').val();
    return phone;
}

//function add_hover_to_social_icons(target) {
//    $(target).hover(function(){
//        $(this).animate({top: '-7px'}, 250, "easeOutBack");
//        $(this).find('span').fadeIn();
//        }, function() {
//        $(this).animate({top: '0px'}, 250, "easeOutBack");
//        $(this).find('span').fadeOut();
//    });
//}

//function show_share_buttons() {
//    $('.share-video').fadeIn();
//}
//
//function hide_video_div() {
//    $('.watch-video, .play-button-shadow').fadeOut();
//}
//
//function scroll_to_video() {
//    $('body,html').animate({
//            scrollTop: $("#player").offset().top - 100
//       }, 800, "easeOutQuart");
//       player.playVideo();
//}

//function scroll_back_from_video() {
//
//    $('body,html').animate({
//            scrollTop: $('.main').offset().top
//       }, 1500, "easeOutQuart", function(){
//       hide_video_div();
//       show_share_buttons();
//    });
//}
//
//function change_in_black_icons() {
//    $('#hotspot-logo').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/logo-black.png');
//    $('#email-icon').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/email-nav-black.png');
//    $('#blog-icon').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/blog-nav-black.png');
//    $('#twitter-icon').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/twitter-nav-black.png');
//    $('#facebook-icon').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/facebook-nav-black.png');
//}
//
//function change_in_white_icons() {
//    $('#hotspot-logo').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/logo.png');
//    $('#email-icon').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/email-nav.png');
//    $('#blog-icon').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/blog-nav.png');
//    $('#twitter-icon').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/twitter-nav.png');
//    $('#facebook-icon').attr('src','http://s3-us-west-2.amazonaws.com/hotspot-static/static/img/facebook-nav.png');
//}
//
//function top_navbar_fade_out() {
//    $(".navbar-fixed-top").fadeOut(300, function(){
//        change_in_black_icons();
//    });
//}
//
//function top_navbar_fade_in() {
//    change_in_white_icons();
//    $(".navbar-fixed-top").fadeIn(300);
//}
//
//function bottom_navbar_fade_out() {
//    $(".navbar-fixed-top").fadeOut(300, function(){
//        change_in_white_icons();
//    });
//}
//
//function bottom_navbar_fade_in() {
//    change_in_black_icons();
//    $(".navbar-fixed-top").fadeIn(300);
//}
//
//var player;
//function onYouTubeIframeAPIReady() {
//    player = new YT.Player('player', {
//      height: '540',
//      width: '960',
//      videoId: 'MNzRAH6gX_k',
//      events: {
//        'onReady': onPlayerReady,
//        'onStateChange': onPlayerStateChange
//      }
//    });
//}
//
//function onPlayerReady(event) {
//    //event.target.playVideo();
//}
//
//function onPlayerStateChange(event) {
//    if (event.data == YT.PlayerState.ENDED) {
//        isVideoWatched = true;
//        scroll_back_from_video();
//    } else if (event.data == YT.PlayerState.PAUSED) {
//        isVideoWatched = true;
//        scroll_back_from_video();
//        $('.share-video span').html("(Or continue watching the video)");
//    } else if (event.data == YT.PlayerState.PLAYING) {
//        isVideoWatched = true;
//        setTimeout('scroll_back_from_video()', 75000);
//    }
//}

//function stopVideo() {
//    player.stopVideo();
//}

function sendAppTextLink (phone, success) {
    var text_message_url = 'http://www.gethotspotapp.com/api/text-app-link/';
    $.post(text_message_url, {phone : phone}, function(){
        success("SMS successful");
    });
}