using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Globalization;
using System.Threading;
using System.Xml.Linq;
using System.Text;
using System.IO;
using System.Web.Routing;

namespace YottosCatalog {
    public partial class Catalog : MasterPage {
        public RequestContext RequestContext { get; set; }

        protected void Page_Load(object sender, EventArgs e) {
            currentYearLabel.Text = DateTime.Today.Year.ToString();
            if (!IsPostBack && !string.IsNullOrEmpty(Request.QueryString["q"])) QueryTextBox.Text = Server.UrlDecode(Request.QueryString["q"]);
            if (!IsPostBack && RequestContext != null && RequestContext.RouteData.Values["q"] != null) QueryTextBox.Text = Server.UrlDecode(RequestContext.RouteData.Values["q"].ToString());            

            switch (Thread.CurrentThread.CurrentCulture.Name) {
                case "en-US":
                    cultureMenu.Items[0].Text = "My language is English";
                    cultureMenu.Items[0].ChildItems.RemoveAt(2);
                    break;
                case "uk-UA":
                    cultureMenu.Items[0].Text = "Моя мова Українська";
                    cultureMenu.Items[0].ChildItems.RemoveAt(1);
                    break;
                default:
                    cultureMenu.Items[0].Text = "Мой язык Русский";
                    cultureMenu.Items[0].ChildItems.RemoveAt(0);
                    break;
            }
        }

        /*protected void CatalogSearch_Handler(object sender, EventArgs e) {
            if (Global.EnableMemorableUrl) {
                var lcid = Thread.CurrentThread.CurrentCulture.LCID;
                var supportedCultures = from culture in Global.SupportedCulturesXml.Descendants()
                                        select (int)culture.Attribute("lcid");
                if (!supportedCultures.Contains(lcid)) lcid = supportedCultures.Last();
                var currentRoute = (from route in Global.routes where route.Lcid == lcid select route).Single();
                var currentSearchRoute = currentRoute.Routes["/CatalogSearch.aspx"].Replace("/{q}/{cat}", string.Empty);
                Response.Redirect(string.Format("/{0}/{1}/{2}/{3}", currentRoute.Path, currentSearchRoute, Server.UrlEncode(QueryTextBox.Text), RootCategoriesDropDownList.SelectedValue));                
            }
            else
                Response.Redirect(string.Format("/CatalogSearch.aspx?q={0}&category={1}", Server.UrlEncode(QueryTextBox.Text), RootCategoriesDropDownList.SelectedValue));            
        }*/

        protected void CatalogSearch_Handler(object sender, EventArgs e) {
            var searchQuery = QueryTextBox.Text; //Server.UrlEncode(QueryTextBox.Text);
            if (Global.EnableMemorableUrl) {
                var lcid = Thread.CurrentThread.CurrentCulture.LCID;
                var supportedCultures = from culture in Global.SupportedCulturesXml.Descendants()
                                        select (int)culture.Attribute("lcid");
                if (!supportedCultures.Contains(lcid)) lcid = supportedCultures.Last();
                var currentRoute = (from route in Global.routes where route.Lcid == lcid select route).Single();

                var currentSearchRedirectRoute = string.Empty;
                
                if (RootCategoriesDropDownList.SelectedIndex == 0) {
                    var currentSearchRoute = currentRoute.Routes["/CatalogSearch.aspx"];
                    currentSearchRedirectRoute = string.Format("/{0}{1}", currentRoute.Path, currentSearchRoute.Replace("{*q}", Server.UrlEncode(searchQuery)));
                } else {
                    var currentSearchRoute = currentRoute.Routes["/catalogSearch.aspx"];
                    currentSearchRedirectRoute = string.Format("/{0}{1}", currentRoute.Path, currentSearchRoute.Replace("{*q}", Server.UrlEncode(searchQuery)).Replace("{cat}", RootCategoriesDropDownList.SelectedItem.Text.Replace(" ", "_")));
                }
                Response.Redirect(currentSearchRedirectRoute);
            }
            else
                Response.Redirect(string.Format("/CatalogSearch.aspx?q={0}&category={1}", Server.UrlEncode(searchQuery), RootCategoriesDropDownList.SelectedValue));            
        }

        protected void RootCategoriesDropDownList_DataBound(object sender, EventArgs e) {
            var category = Request.QueryString["category"];
            if (!string.IsNullOrEmpty(category)) RootCategoriesDropDownList.Items.FindByValue(category).Selected = true;
        }

        public string Description {
            set {
                if (!string.IsNullOrEmpty(value)) {
                    if (value.Length > 200) throw new ArgumentException("Description too long.");
                    description.Attributes["content"] = value;
                }
            }
        }

        protected void Page_PreRender(object sender, EventArgs e) { 
            Page.ClientScript.RegisterStartupScript(Page.GetType(), "addClickBehavior", "addClickBehavior(document.getElementById('" + cultureMenu.ClientID + "'));", true);
        }        

        protected void CultureMenu_MenuItemDataBound(object sender, MenuEventArgs e) {
            if (e.Item.Value.Equals("cultures")) {
                var culture = Thread.CurrentThread.CurrentUICulture.Name;
                XElement cultureNode = null;
                try {
                    cultureNode = (from _culture in Global.SupportedCulturesXml.Descendants()
                                   where ((string)_culture.Attribute("name")).Equals(culture, StringComparison.InvariantCultureIgnoreCase)
                                   select _culture).Single();

                } catch { cultureNode = Global.SupportedCulturesXml.Descendants().Last(); } 
                finally {
                    e.Item.Text = ((string)cultureNode.Value).Replace("&nbsp;", "");
                    e.Item.Value = (string)cultureNode.Attribute("name");
                }
            }          
        }

        protected void CultureMenu_DataBound(object sender, EventArgs e) {
            var currentCulture = Thread.CurrentThread.CurrentCulture.Name;
            var menu = sender as Menu;
            var indexToRemove = 0;
            foreach (var item in menu.Items[0].ChildItems) {
                if ((item as MenuItem).Value.Equals(currentCulture, StringComparison.InvariantCultureIgnoreCase))
                    break;
                indexToRemove++;
            }
            menu.Items[0].ChildItems.RemoveAt(indexToRemove);
        }

        protected void ExitClick(object sender, EventArgs e) { userLoginArea.Visible = false; }

        protected void CultureMenu_MenuItemClick(object sender, MenuEventArgs e) {
            var requestId = Request.QueryString["id"];

            var cookie = new HttpCookie("culture");
            cookie.Value = e.Item.Value;
            Response.Cookies.Add(cookie);
            Thread.CurrentThread.CurrentCulture = new CultureInfo(e.Item.Value);
            Thread.CurrentThread.CurrentUICulture = new CultureInfo(e.Item.Value);

            if (requestId != null && Global.EnableMemorableUrl) {
                var mapping = new YottosCatalogUrlMappingsDataContext();
                var transformedUrls = (from trans in mapping.transformed_urls
                                       where trans.url.Equals(Request.UrlReferrer.LocalPath)
                                       select trans).ToList();
                transformed_url transformedUrl;
                if (transformedUrls.Count == 1) transformedUrl = transformedUrls.Single();
                else if (transformedUrls.Count > 1) transformedUrl = transformedUrls.First();
                else { 
                    Response.Redirect("/", true);
                    return;
                }

                var actualTransformed = (from trans in transformedUrl.actual_url.transformed_urls
                                         where trans.lcid == Thread.CurrentThread.CurrentCulture.LCID
                                         select trans).Single();

                Response.Redirect(actualTransformed.url);
            }
            else if (Request.Url.PathAndQuery.Contains("CatalogList.aspx")) Response.Redirect("/");
            else Response.Redirect(Request.Url.PathAndQuery);
        }

        protected void TraverseLink_Click(object sender, EventArgs e) {
            if (QueryTextBox != null && sender != null)
                try {
                    var nav = (sender as LinkButton).CommandName;
                    if (!string.IsNullOrEmpty(QueryTextBox.Text))
                        nav += (sender as LinkButton).CommandArgument + EncodeParameter_cp1251(QueryTextBox.Text);                    
                    Response.Redirect(nav, true);
                } catch (Exception) { }                
        }

        public string EncodeParameter_cp1251(string param) {
            var result = new StringBuilder();
            foreach (var bt in Encoding.GetEncoding("windows-1251").GetBytes(param)) result.AppendFormat("%{0}", bt.ToString("X02"));
            return result.ToString();           
        }
    }
}