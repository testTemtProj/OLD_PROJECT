using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Globalization;
using System.Threading;
using YottosCatalog.Code;

namespace YottosCatalog {
    public partial class About : MenuPage {
        protected void Page_Load(object sender, EventArgs e) {
            Master.Description = Resources.CatalogResources.CatalogTitle;
        } 
    }
}
