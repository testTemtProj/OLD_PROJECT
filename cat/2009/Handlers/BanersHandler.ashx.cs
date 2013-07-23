using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.SessionState;
using System.IO;

namespace YottosCatalog.Handlers {
    public class BanersHandler : IHttpHandler, IRequiresSessionState {
        private List<string> bannerList = new List<string>();
        private static string bannerFolder = @"~\ClientBin\Baners";

        public void ProcessRequest(HttpContext context) {            
            bannerList.AddRange(Directory.GetFiles(context.Server.MapPath(bannerFolder), "*.swf"));
            var bannerIndex = 0;
            if (context.Session["bannerIndex"] == null) context.Session["bannerIndex"] = bannerIndex;
            bannerIndex = (int)context.Session["bannerIndex"];

            context.Response.ContentType = "application/x-shockwave-flash";
            context.Response.WriteFile(bannerList[bannerIndex++]);           
            if (bannerIndex == bannerList.Count) bannerIndex = 0;
            context.Session["bannerIndex"] = bannerIndex;
        }

        public bool IsReusable {
            get { return false; }
        }
    }
}
