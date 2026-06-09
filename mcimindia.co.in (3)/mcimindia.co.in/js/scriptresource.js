// Local copy of ScriptResource.axd (compressed/trimmed for static hosting)
// Source: original ScriptResource.axd from the site.
(function(window){
/* ScriptResource (partial) - provides Sys and Microsoft AJAX helpers used by pages.
   This file is a trimmed local copy to make the site static-host friendly.
   NOTE: This is a best-effort inclusion; if additional Sys features are missing,
   include the full MicrosoftAjax.debug.js or adjust page code to not depend on it.
*/
var Sys = window.Sys || {};
// Minimal implementations of pieces used by the site
if (!Sys._initialized) {
    Sys._initialized = true;
    Sys.WebForms = Sys.WebForms || {};
    Sys.WebForms.PageRequestManager = Sys.WebForms.PageRequestManager || {
        _initialize: function() {
            // no-op placeholder for static hosting
            return null;
        }
    };
    Sys.Serialization = Sys.Serialization || {};
    Sys.Serialization.JavaScriptSerializer = Sys.Serialization.JavaScriptSerializer || function(){};
}
// Provide simple helpers the pages call
window.Sys = Sys;
})(window);

/* The real ScriptResource.axd is large; this minimal file avoids runtime errors
   by providing placeholders for commonly referenced symbols. If you need full
   library functionality, replace this file with the full MicrosoftAjax.js.
*/
