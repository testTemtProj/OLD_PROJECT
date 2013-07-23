using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace YottosCatalog.Handlers {
    public class LinkClickHandler : IHttpHandler {
        public void ProcessRequest(HttpContext context) {
            var id = int.Parse(context.Request.QueryString["id"]);
            var database = new YottosCatalogDataContext();
            var theLink = (from _link in database.links
                           where _link.id == id
                           select _link).Single();
            theLink.link_counter++;
            database.SubmitChanges();
            var url = theLink.url;
            if(url.StartsWith("http://") || url.StartsWith("https://"))
                context.Response.Redirect(url, true);
            else context.Response.Redirect("http://" + url, true);
        }

        public bool IsReusable { get { return false; } }
    }
}
