using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.Routing;

namespace YottosCatalog.Code {
    public class MenuPage : Page {
        public RequestContext RequestContext { get; set; }

        protected void Page_PreInit(object sender, EventArgs e) {
            (Master as Catalog).RequestContext = RequestContext;
            if (Request.ServerVariables["http_user_agent"].IndexOf("Safari", StringComparison.CurrentCultureIgnoreCase) != -1)
                Page.ClientTarget = "uplevel";
            if (Request.UserAgent.Contains("AppleWebKit") || Request.UserAgent.Contains("Opera")) Request.Browser.Adapters.Clear();
        }
    }
}
