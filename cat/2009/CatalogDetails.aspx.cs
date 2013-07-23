using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Threading;
using System.Globalization;
using YottosCatalog.Filters;
using YottosCatalog.Code;

namespace YottosCatalog {
    public partial class CatalogDetails : MenuPage {
        protected void Page_Load(object sender, EventArgs e) {
            var strId = Request["id"];
            var id = 1;
            if (!string.IsNullOrEmpty(strId)) id = int.Parse(strId);
            var query = (from root in new YottosCatalogDataContext().root_categories
                         where root.id == id
                         select new { Name = root.name, Description = root.root_category_description }).ToList();
            TitleLabel.Text = string.Empty;
            if (query.Count != 0) { 
                var root = query.Single();
                TitleLabel.Text = root.Name;
                Master.Description = root.Description;
            }            
            Title = "Yottos | " + TitleLabel.Text;
            if (Global.EnableMemorableUrl)
                Response.Filter = new ResponseModificationFilter(Response.Filter, new YottosCatalogDataContext(), new YottosCatalogUrlMappingsDataContext());
        }
    }
}
