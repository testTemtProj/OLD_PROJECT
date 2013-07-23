using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.Routing;
using System.Web.Compilation;
using YottosCatalog.Code;

namespace YottosCatalog.Handlers {
    public class CatalogRouteHandler : IRouteHandler {
        private string destination;

        public CatalogRouteHandler(string Destination) {
            destination = Destination;
        }

        public IHttpHandler GetHttpHandler(RequestContext requestContext) {
            var result = BuildManager.CreateInstanceFromVirtualPath(destination, typeof(MenuPage)) as MenuPage;
            result.RequestContext = requestContext;            
            return result;
        }
    }
}
