using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Globalization;
using System.Threading;
using YottosCatalog.Filters;
using YottosCatalog.Code;

namespace YottosCatalog {
    public partial class CatalogList : MenuPage {
        protected void Page_Load(object sender, EventArgs e) {
            Master.Description = Resources.CatalogResources.CatalogTitle;
            if (Global.EnableMemorableUrl)
                Response.Filter = new ResponseModificationFilter(Response.Filter, new YottosCatalogDataContext(), new YottosCatalogUrlMappingsDataContext());
        }
    }
}
