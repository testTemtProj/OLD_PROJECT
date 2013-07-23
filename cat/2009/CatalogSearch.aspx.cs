using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Text;
using System.Threading;
using System.Globalization;
using System.Resources;
using System.Configuration;
using YottosCatalog.Filters;
using YottosCatalog.Code;
using System.Web.Routing;

namespace YottosCatalog {
    public partial class CatalogSearch : MenuPage {
        protected bool ShowSubCategory { get; set; }

        /*protected void Page_Load(object sender, EventArgs e) {
            var rootCategoryId = 0;
            int.TryParse(Request.QueryString["category"], out rootCategoryId);
            var searchText = Server.UrlDecode(Request.QueryString["q"]);                        
            Master.Description = Resources.CatalogResources.SearchTitle;
            
            if (Global.EnableMemorableUrl) {
                if (Master.RequestContext != null) {
                    if (Master.RequestContext.RouteData.Values["q"] != null)
                        searchText = links_DS.SelectParameters["searchText"].DefaultValue = Master.RequestContext.RouteData.Values["q"].ToString();
                    if (Master.RequestContext.RouteData.Values["cat"] != null) {
                        links_DS.SelectParameters["category"].DefaultValue = Master.RequestContext.RouteData.Values["cat"].ToString();
                        int.TryParse(Master.RequestContext.RouteData.Values["cat"].ToString(), out rootCategoryId);
                    }
                }
                var database = new YottosCatalogDataContext();
                var mapping = new YottosCatalogUrlMappingsDataContext();
  
                Response.Filter = new LinksResultModificationFilter(Response.Filter, database, mapping);
                Response.Filter = new ResponseModificationFilter(Response.Filter, database, mapping);
            }
            if (string.IsNullOrEmpty(searchText)) Response.Redirect("~/", true);
            if (!string.IsNullOrEmpty(searchText)) ShowSubCategory = rootCategoryId == 0;
        }*/

        protected void Page_Load(object sender, EventArgs e) {
            var rootCategoryId = 0;
            int.TryParse(Request.QueryString["category"], out rootCategoryId);
            var searchText = Server.UrlDecode(Request.QueryString["q"]);                        
            Master.Description = Resources.CatalogResources.SearchTitle;
            
            if (Global.EnableMemorableUrl) {
                var database = new YottosCatalogDataContext();
                var mapping = new YottosCatalogUrlMappingsDataContext();

                if (Master.RequestContext != null) {
                    if (Master.RequestContext.RouteData.Values["q"] != null)
                        searchText = links_DS.SelectParameters["searchText"].DefaultValue = Master.RequestContext.RouteData.Values["q"].ToString();
                    if (Master.RequestContext.RouteData.Values["cat"] != null) {
                        var catName = Master.RequestContext.RouteData.Values["cat"].ToString();
                        if (!catName.Equals(Resources.CatalogResources.RootAllCategoriesText) && !catName.Equals("0")) 
                            rootCategoryId = (from root in database.root_categories
                                              where root.name.Replace(" ", "_").Equals(catName)
                                              select root.id).Single();                      

                        links_DS.SelectParameters["category"].DefaultValue = rootCategoryId.ToString();                        
                    }
                }  
                Response.Filter = new LinksResultModificationFilter(Response.Filter, database, mapping);
                Response.Filter = new ResponseModificationFilter(Response.Filter, database, mapping);
            }
            if (string.IsNullOrEmpty(searchText)) Response.Redirect("~/", true);
            if (!string.IsNullOrEmpty(searchText)) ShowSubCategory = rootCategoryId == 0;
        }

        protected void NoResults_Load(object sender, EventArgs e) {            
            var query = Request.QueryString["q"];
            if(Master.RequestContext != null && Master.RequestContext.RouteData.Values["q"] != null) query = Master.RequestContext.RouteData.Values["q"].ToString();

            var webUrl = string.Format("{0}/{1}{2}",  Resources.CatalogResources.Master_WebLink, "Result.aspx?q=", Master.EncodeParameter_cp1251(query));
            
            (sender as Label).Text = Resources.CatalogResources.SearchNoResults.Replace("#", query).
                Replace("'$'", string.Format("<a href=\"{0}\">{1}<a/>", 
                    webUrl, Resources.CatalogResources.SearchNoResultInternet));
        }

        protected void Pager_Load(object sender, EventArgs e) {
            var pager = sender as DataPager;
            var pageSize = 10;
            if (Request.Cookies.AllKeys.Contains("page_size"))
                int.TryParse(Request.Cookies["page_size"].Value, out pageSize);
            pager.PageSize = pageSize;            
        }
    }
}