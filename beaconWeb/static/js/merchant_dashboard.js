var start_time_picker;
var end_time_picker;
var add_deal_start_time_picker;
var add_deal_end_time_picker;

    var spinner;

    var spinner_options = {
          lines: 13, // The number of lines to draw
          length: 8, // The length of each line
          width: 4, // The line thickness
          radius: 10, // The radius of the inner circle
          corners: 1, // Corner roundness (0..1)
          rotate: 0, // The rotation offset
          direction: 1, // 1: clockwise, -1: counterclockwise
          color: '#FFF', // #rgb or #rrggbb or array of colors
          speed: 1, // Rounds per second
          trail: 60, // Afterglow percentage
          shadow: false, // Whether to render a shadow
          hwaccel: false, // Whether to use hardware acceleration
          className: 'spinner', // The CSS class to assign to the spinner
          zIndex: 2e9, // The z-index (defaults to 2000000000)
          top: '50%', // Top position relative to parent
          left: '50%' // Left position relative to parent
    };

    function start_spinner() {
        $('#spinner').show();
        var target = document.getElementById('spinner');
        spinner = new Spinner(spinner_options).spin(target);
    }

    function stop_spinner() {
        if (spinner !== undefined) {
            spinner.stop();
        }
        $('#spinner').hide();
    }

$(document).ready(function(){

    var current_deal;
    var place_name;

    var docURL = document.URL;
    var url;
    if (docURL.indexOf("localhost") !== -1) {
      url = "http://localhost:8000/";
    } else {
      url = "http://www.gethotspotapp.com/";
      mixpanel.track("dashboard_loaded");
    }

    var cookie_token = $.cookie("merchant_token");
    stop_spinner();
    merchant.init(url);

    initialize_time_picker();

//    var active_deals;

    if (cookie_token !== "undefined" && cookie_token !== undefined) {
        merchant.init (url, cookie_token);
            start_spinner();
            merchant.getDeals(function(success){
            stop_spinner();
            if (success !== undefined) {
//                active_deals = success.active_deals;
                fade_out_and_load_merchant_dashboard(success);
            } else {
                load_login_container();
            }
        });
    } else {
        load_login_container();
    }

    function load_login_container() {
        $('#login-container').show();
        $('#dashboard-container').hide();
        $('.main').css('background', 'transparent');
    }

    function add_tooltips() {
        $('#deal-title').tooltipster({
            content: $('<span class="tooltip-pic"><img src="'+ static_url +'img/title-pic.png" /></span>'),
            trigger: 'click',
            position: 'right',
            theme: 'tooltipster-noir'
        });

        $('#invite-prompt').tooltipster({
            content: $('<span class="tooltip-pic"><img src="'+ static_url +'img/sms-pic.png" /></span>'),
            trigger: 'click',
            position: 'right',
            theme: 'tooltipster-noir'
        });

        $('#deal-description').tooltipster({
            content: $('<span class="tooltip-pic"><img src="'+ static_url +'img/deal-pic.png" /></span>'),
            trigger: 'click',
            position: 'left',
            theme: 'tooltipster-noir'
        });

        $('#deal-title-update').tooltipster({
            content: $('<span class="tooltip-pic"><img src="'+ static_url +'img/title-pic.png" /></span>'),
            trigger: 'click',
            position: 'right',
            theme: 'tooltipster-noir'
        });

        $('#invite-prompt-update').tooltipster({
            content: $('<span class="tooltip-pic"><img src="'+ static_url +'img/sms-pic.png" /></span>'),
            trigger: 'click',
            position: 'right',
            theme: 'tooltipster-noir'
        });

        $('#deal-description-update').tooltipster({
            content: $('<span class="tooltip-pic"><img src="'+ static_url +'img/deal-pic.png" /></span>'),
            trigger: 'click',
            position: 'left',
            theme: 'tooltipster-noir'
        });
    }

    function fade_out_and_load_merchant_dashboard(deals) {
        mixpanel.register({
           "venue": deals.default_deal[0].place.name
        });
        mixpanel.track("deals_loaded");
        $('#login-container').fadeOut(500, load_merchant_dashboard);
        $('#registration-container').fadeOut(500, load_merchant_dashboard);
        place_name = deals.default_deal[0].place.name.toUpperCase();
        $('.main').css('background', '#FFFFFF');
        load_place_name();
        add_tooltips();
        merchant.place_id = deals.default_deal[0].place.id;
        load_active_deals(deals.recurring_deal);
        load_primary_deal(deals.default_deal[0])
    }

    function load_primary_deal(deal) {
        $('.primary-deal-title').html(deal.deal_description);
    }

    function load_place_name() {
        $(".section-title").html(place_name);
    }

    var html_for_deal_list = '<tr class="special-deal-item"><td class="preview-time">{0}</td><td>{1}</td><td class="edit-button" data-id={2}><a>EDIT</a></td></tr>';
    function load_active_deals(active_deals) {
        load_deal_list(active_deals);
        $('.edit-button').on('click', function() {
            merchant.getDeal($(this).data('id'), function(success) {
                show_update(success.deals);
            });
        });

    }

    days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    function get_deal_time_string(hours) {
        if (hours.length > 0) {
            var day_int = get_day_int(hours[0].days);
            return days_of_week[day_int];
        } else {
            return "";
        }
    }

    function load_deal_list(active_deals) {
        $('.special-deal-item').remove();
        for (var i = 0; i < active_deals.length; i++) {
            var time_string = get_deal_time_string(active_deals[i].hours);
            var updated_html_for_deal_list = html_for_deal_list.replace("{0}", time_string).replace("{1}",active_deals[i].deal_description_short).replace("{2}", active_deals[i].id);
            $('.deal-list').append(updated_html_for_deal_list);
        }
    }

    function get_time_in_array(time) {
        hour_and_minutes = [];
        hour_and_minutes[0] = Math.floor(time/3600);
        hour_and_minutes[1] = (time%3600)/60;
        return hour_and_minutes;
    }

    function get_day_int(day_bit_string) {
        return (day_bit_string.indexOf("1") - 1).toString();
    }

    function show_update(deal_info) {
        $("#deal-type-update").val(deal_info.deal_type);
        $("#deal-title-update").val(deal_info.deal_description_short);
        var start_time = get_time_in_array(deal_info.hours[0].start);
        var end_time = get_time_in_array(deal_info.hours[0].end);
        var day = get_day_int(deal_info.hours[0].days);
        $("#day-update").val(day);
        start_time_picker.set('select', start_time);
        end_time_picker.set('select', end_time);
        var deal_description = deal_info.deal_description;
        $("#deal-description-update").val(deal_description.substring(deal_description.indexOf("-") + 2));
        $("#more-info-update").val(deal_info.additional_info);
        $("#invite-prompt-update").val(deal_info.invite_prompt);
        $("#min-invites-update").val(deal_info.invite_requirement);
        $('#main-deal-list').fadeOut(300, function() {
            current_deal = deal_info;
            $('#update-deal-container').fadeIn();
            $('.section-title').html("EDIT DEAL");
        });

    }

    function load_merchant_dashboard() {
        $('#dashboard-container').fadeIn();
    }

    function save_token(token) {
        merchant.restToken = token;
        $.cookie("merchant_token", token, {expires: 365});
    }

    function login_merchant(email, password) {
        start_spinner();
        $.ajax({
            url: url + 'api/merchant/login/',
            type: 'POST',
            data: {email: email, password: password},
            success: function(success) {
                stop_spinner();
                if ('default_deal' in success) {
                    save_token(success.merchant_token);
                    fade_out_and_load_merchant_dashboard(success);
                } else {
                    alert(success.message);
                }
            }
        });

//        merchant.login(email, password, function(success) {
//            if ('active_deals' in success) {
//                dashboard = success;
//                this.restToken = success.merchant_token;
//                fade_out_and_load_merchant_dashboard();
//            } else {
//                alert(success.message);
//            }
//        });
    }

    function login_clicked() {
        var email = $('#login-email').val();
        var password = $('#login-password').val();
        login_merchant(email, password);
    }

    function get_time_in_seconds(time) {
        return (time.hour * 60 * 60) + (time.mins * 60);
    }

    function remove_deal() {
        merchant.removeDeal(current_deal.id, "RG", function(success) {
            mixpanel.track('removed_deal', {
                "deal_id": current_deal.id
            });
            reset_update_deal();
           show_main_from_update_deal(success);
        });
    }

    function update_deal() {
        var deal_data = {};
        deal_data.day = parseInt($('#day-update').val());
        deal_data.start_time = get_time_in_seconds(start_time_picker.get('select'));
        deal_data.end_time = get_time_in_seconds(end_time_picker.get('select'));
        deal_data.deal_type = "RG";
        deal_data.deal_id = current_deal.id;
        deal_data.description = $('#deal-description-update').val();
        deal_data.title = $('#deal-title-update').val();
        deal_data.invite_requirement = parseInt($('#min-invites-update').val());
        deal_data.additional_info = $('#more-info-update').val();
        deal_data.invite_prompt = $('#invite-prompt-update').val();
        deal_data.place_id = merchant.place_id;
        mixpanel.track("deal_updated", deal_data);
        start_spinner();
        merchant.updateDeal(deal_data, function(success) {
            stop_spinner();
           reset_update_deal();
           show_main_from_update_deal(success);
        });
    }

    function reset_update_deal() {
        $("#update-deal-container input").val("");
        $("#deal-type-update").val("DT");
        $("#min-invites-update").val("1");

    }

    function reset_add_deal() {

    }

    function add_deal() {
        var deal_data = {};
        deal_data.deal_type = "RG";
        deal_data.day = parseInt($('#day').val());
        deal_data.start_time = get_time_in_seconds(add_deal_start_time_picker.get('select'));
        deal_data.end_time = get_time_in_seconds(add_deal_end_time_picker.get('select'));
        deal_data.title = $('#deal-title').val();
        deal_data.invite_requirement = parseInt($('#min-invites').val());
        deal_data.additional_info = $('#more-info').val();
        deal_data.invite_prompt = $('#invite-prompt').val();
        deal_data.place_id = merchant.place_id;
        mixpanel.track("deal_added", deal_data);
        start_spinner();
        merchant.addDeal(deal_data, function(success) {
           stop_spinner();
           reset_add_deal();
           show_main_from_add_deal(success);
        });
    }

    function show_main_from_add_deal(deals) {
        $('#add-deal-container').fadeOut(300, function() {
            load_active_deals(deals.recurring_deal);
            show_main();
            $('#main-deal-list').fadeIn();
        });
    }

    function show_main_from_update_deal(deals) {
        $('#update-deal-container').fadeOut(300, function() {
            load_active_deals(deals.recurring_deal);
           $('#main-deal-list').fadeIn();
        });
    }

    function go_back_from_add_deal() {
        $('#add-deal-container').fadeOut(300, function() {
            load_place_name();
           $('#main-deal-list').fadeIn();
        });
    }

    function go_back_from_update_deal() {
        $('#update-deal-container').fadeOut(300, function() {
            load_place_name();
           $('#main-deal-list').fadeIn();
        });
    }

    function show_main() {
//        merchant.getDeals(function(success) {
//            load_active_deals(active_deals);
//        });
        $('#main-deal-list').fadeIn();
    }

    function show_add_deal() {
        $('#main-deal-list').fadeOut(300, function() {
            $('#add-deal-container').fadeIn();
        })
    }

    function initialize_time_picker() {
        var start_time = $('#start-time').pickatime({
            onSet: function() {
                var current_val = start_time_picker.get('select');
                end_time_picker.set('select', [current_val.hour + 3, current_val.mins]);
            }
        });
        var end_time = $('#end-time').pickatime();

        start_time_picker = start_time.pickatime('picker');
        end_time_picker = end_time.pickatime('picker');

        var add_deal_start_time = $('#add-deal-start-time').pickatime({
            onSet: function() {
                var add_deal_current_val = add_deal_start_time_picker.get('select');
                add_deal_end_time_picker.set('select', [add_deal_current_val.hour + 3, add_deal_current_val.mins]);
            }
        });
        var add_deal_end_time = $('#add-deal-end-time').pickatime();

        add_deal_start_time_picker = add_deal_start_time.pickatime('picker');
        add_deal_end_time_picker = add_deal_end_time.pickatime('picker');
    }

    function show_change_password_dialog() {
        $('#changePassword').modal('show');
    }

    function logout_clicked() {
        $('#dashboard-container').fadeOut(400, function() {
            $.removeCookie("merchant_token");
            $('.main').css('background', 'transparent');
            $('#login-container').fadeIn();
        });
    }

    function reset_change_password_fields() {
        $('#old-password').val("");
        $('#new-password').val("");
        $('#confirm-password').val("");
    }

    function submit_change_password() {
        var old_password = $('#old-password').val();
        var new_password = $('#new-password').val();
        var confirm_password = $('#confirm-password').val();
        reset_change_password_fields();
        if (new_password !== confirm_password) {
            alert("Passwords don't match");
        } else {
            if (new_password === "" || old_password === "") {
                alert("Please complete each field");
            } else {
               $('#changePassword').modal('hide');
                start_spinner();
                merchant.changePassword(old_password, new_password, function() {
                    stop_spinner();
                    alert("Your password was successfully changed");
                });
            }
        }
    }

    $('.login-button').on('click', login_clicked);
    $('.logout').on('click', logout_clicked);
    $('.link-to-add-deal').on('click', show_add_deal);
    $('.add-deal-back-button').on('click', go_back_from_add_deal);
    $('.update-deal-back-button').on('click', go_back_from_update_deal);
    $('.add-deal-button').on('click', add_deal);
    $('.update-deal-button').on('click', update_deal);
    $('.update-delete-button').on('click', remove_deal);
    $('.change-password').on('click', show_change_password_dialog);
    $('#submit-change-password').on('click', submit_change_password);
});