using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Text;
using System.Threading;
using System.Globalization;
using YottosCatalog.Filters;
using YottosCatalog.Code;

namespace YottosCatalog {
    public partial class CatalogContents : MenuPage {
        protected void Page_Load(object sender, EventArgs e) {
            var strId = Request["id"];
            var id = 1;
            if (!string.IsNullOrEmpty(strId)) id = int.Parse(strId);
            var subCategory = (from category in new YottosCatalogDataContext().sub_categories
                               where category.id == id
                               select category).Single();
            var titleNodes = new List<string>();
            BuildTitle(subCategory, titleNodes);
            titleNodes.Reverse();
            var resultTitle = new StringBuilder();
            foreach (var titleNode in titleNodes) {
                resultTitle.Append(titleNode);
                if (!titleNode.Equals(titleNodes.Last())) resultTitle.Append(" / ");
            }
            Title = "Yottos | " + resultTitle.ToString();
            Master.Description = subCategory.sub_category_description;
            if (Global.EnableMemorableUrl) {
                var database = new YottosCatalogDataContext();
                var mapping = new YottosCatalogUrlMappingsDataContext();
                Response.Filter = new LinksResultModificationFilter(Response.Filter, database, mapping);
                Response.Filter = new ResponseModificationFilter(Response.Filter, database, mapping);
            }
        }

        private void BuildTitle(sub_category category, List<string> destinationTitle) {
            destinationTitle.Add(category.name);
            foreach (var tree in category.root_sub_category_trees)            
                BuildTitle(tree.root_sub_category, destinationTitle);                        
        }

        protected void Pager_Load(object sender, EventArgs e) {
            var pager = sender as DataPager;
            var pageSize = 10;
            if(Request.Cookies.AllKeys.Contains("page_size"))
                int.TryParse(Request.Cookies["page_size"].Value, out pageSize);
            pager.PageSize = pageSize;
        }
    }
}
