///////////////////////////////////////
// Utility functions
///////////////////////////////////////

// Add method to Number for radian lookup
if (typeof(Number.prototype.toRad) === "undefined") {
   Number.prototype.toRad = function() {
      return this * Math.PI / 180;
   }
}

// Window.console override for older browsers
if(!window.console)
{
   var __console = function(){
      this.history = [];
   }
   __console.prototype.log = function()
   {
      this.history.push(Array.prototype.slice.call( arguments ));
   }
   window.console = new __console();
}

// Setup getCookie function if not exists
if(typeof getCookie != 'function')
{
   function getCookie(name)
   {
      var cookieValue = null;
      if (document.cookie && document.cookie != '')
      {
         var cookies = document.cookie.split(';');
         for (var i = 0; i < cookies.length; i++)
         {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '='))
            {
               cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
               break;
            }
         }
      }
      return cookieValue;
   }
}

// Adding indexOf method for searching arrays
if (!Array.prototype.indexOf)
{
  Array.prototype.indexOf = function(elt /*, from*/)
  {
    var len = this.length;

    var from = Number(arguments[1]) || 0;
    from = (from < 0)
         ? Math.ceil(from)
         : Math.floor(from);
    if (from < 0)
      from += len;

    for (; from < len; from++)
    {
      if (from in this &&
          this[from] === elt)
        return from;
    }
    return -1;
  };
}

// Get query string parameters
function getParameterByName(name)
{
  name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
  var regexS = "[\\?&]" + name + "=([^&#]*)";
  var regex = new RegExp(regexS);
  var results = regex.exec(window.location.search);
  if(results == null)
    return "";
  else
    return decodeURIComponent(results[1].replace(/\+/g, " "));
}

///////////////////////////////////////
// The main Hotspot object
///////////////////////////////////////
var hotspot = (function($){

   // The default dataType for jQuery AJAX calls
   $.ajaxSetup({  dataType: 'json' });

   var module =
   {
      basePath : '',
      username : null,
      history : [],
      cache: {},
      beacon_id: null,
      contact_phone: null,
      restToken: null,

       init: function(restToken, beacon_id, basePath, contact_phone)
          {
             var self = this;
             this.restToken = restToken;
             this.basePath = basePath || this.basePath;
             this.beacon_id = beacon_id;
             this.contact_phone = contact_phone;

             $(window).unload(function(){
                self = null;
             });
          },

      /* Private methods for making various requests */
      __post: function(url, params, onSuccess, onError)
      {
         this.__makeRequest('POST', url, params, onSuccess, onError);
      },
      __get: function(url, params, onSuccess, onError)
      {
          this.__makeRequest('GET', url, params, onSuccess, onError);
      },
      __put: function(url, params, onSuccess, onError)
      {
         var self = this;
         this.__makeRequest('PUT', url, params, onSuccess, onError, function(xhr, settings){
            self.__beforeSend(xhr, settings);
            xhr.setRequestHeader('X-HTTP-Method-Override', 'PUT');
         });
      },
      __beforeSend: function(xhr, settings)
      {
          if (!(/^http(s)?:.*/.test(settings.url))) {
            xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
            xhr.setRequestHeader('X-Requested-With', 'XML-Http-Request');
            xhr.setRequestHeader('Accept', 'application/json');
         }
      },
      __onError: function(xhr, err, msg)
      {
         console.log("Oops, something went wrong:\n\n"+msg);
      },
      __makeRequest:function(type, url, params, onSuccess, onError, beforeSend)
      {
          var self = this;
	      var beforeSendOverride = beforeSend || this.__beforeSend;
	      var fBeforeSend = function(xhr, settings){
	      beforeSendOverride(xhr, settings);
	      xhr.setRequestHeader('Authorization', 'Token 8c575995189a11e76f49fca27a7fdc3ff7207b5c');
	      }

         $.ajax({
            beforeSend : fBeforeSend,
            url        : self.basePath + url,
            type       : type,
            data       : params || {},
            success    : onSuccess,
            error      : onError || this.__onError
         });
      },
      /* End of private methods */
      // Get current user profile by token
      // TODO: Security - make sure other user profile cannot be loaded

      joinHotspot: function ( success )
      {
         var self = this;
         var url = 'api/follow/';

         this.__post(url, {inviteId : self.restToken}, function( response ){
             hotspot.cache = response;
             if(response)
             {
                 if(success instanceof Function) success.call(self, response);
             }
             else
             {
                 alert("Error: Failed to join Hotspot.");
             }
         });
     },

     postMessage: function( message, success )
      {
         var self = this;
         var url = 'api/message/';

         this.__post(url, { beacon_invite : self.restToken, message : message }, function(response){
                if(success instanceof Function) success.call(self, response);
         });
      },

      getMessages: function ( success )
      {
        var self = this;
        var url = 'api/message/';
          this.__get(url, { beacon : self.beacon_id }, function(response){
//              console.log(response);
              if(success instanceof Function) success.call(self, response);
          });
      },

      getHotspot: function ( success )
      {
        var self = this;
        var url = 'api/beacon/';
          this.__get(url, {beacon_invite : self.restToken}, function(response){
//              console.log(response);
              if(success instanceof Function) success.call(self, response);
          });
      },

      getGuestList: function ( success )
      {
        var self = this;
        var url = 'api/invite/';
          this.__get(url, { beacon_id : self.beacon_id }, function(response){
//              console.log(response);
              if(success instanceof Function) success.call(self, response);
          });
      },
      sawInvite: function ( success )
      {
        var self = this;
        var url = 'api/saw_invite/';
          this.__post(url, { inviteId : self.restToken }, function(response){
//              console.log(response);
              if(success instanceof Function) success.call(self, response);
          });
      },
      getDeal: function ( deal_id, success )
      {
        var self = this;
        var url = 'api/deal_status/';
          this.__get(url, { deal_status_id : deal_id }, function(response){
              if(success instanceof Function) success.call(self, response);
          });
      },
      redeemDeal: function ( deal_id, success )
      {
        var self = this;
        var url = 'api/deal/redeem/';
          this.__post(url, { deal_id : deal_id }, function(response){
              if(success instanceof Function) success.call(self, response);
          });
      }



   };
   return module;
})(jQuery);


