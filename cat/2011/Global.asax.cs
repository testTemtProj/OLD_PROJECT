using System;
using System.Linq;
using System.Web;
using System.Web.SessionState;
using System.Xml.Linq;
using System.Threading;
using System.Globalization;
using System.Configuration;
using System.Collections.Generic;
using System.Text;
using System.IO;
using System.Web.Routing;
using YottosCatalog.Handlers;
using YottosCatalog.Code;

namespace YottosCatalog {
    public class Global : HttpApplication {
        public static XElement SupportedCulturesXml { get; private set; }
        public static bool EnableMemorableUrl = true;
        public static List<CatalogRouting> routes;

        protected void Application_Start(object sender, EventArgs e) {
            SupportedCulturesXml = XElement.Load(Server.MapPath("~/App_Data/SupportedCultures.xml"));
            bool.TryParse(ConfigurationManager.AppSettings["enable_memorable_url"], out EnableMemorableUrl);

            if (EnableMemorableUrl && routes == null) {
                routes = new List<CatalogRouting>();
                var routesXml = XElement.Load(Server.MapPath("~/App_Data/RouteTable.xml"));
                var roots = from root in routesXml.Descendants("root") select root;
                foreach (var root in roots) {
                    var route = new CatalogRouting() {
                        Lcid = (int)root.Attribute("lcid"),
                        Path = (string) root.Attribute("path")
                    };
                    foreach (var transformed in root.Descendants("transformed")) {
                        route.Routes.Add((string)transformed.Attribute("actual"), (string)transformed.Attribute("path"));
                        var newRoute = new Route(string.Format("{0}{1}", route.Path, (string)transformed.Attribute("path")), new CatalogRouteHandler((string)transformed.Attribute("actual")));
                        if (newRoute.Url.Contains("cat")) {
                            newRoute.Defaults = new RouteValueDictionary();
                            newRoute.Defaults.Add("cat", "0");
                        }
                        RouteTable.Routes.Add(newRoute);
                    }
                    routes.Add(route);
                }                
            }
            

            /*
             * код генерации стартового мапинга ссылок
            var databaseCommon = new YottosCatalogDataContext();
            var database1033 = new YottosCatalogDataContext(ConfigurationManager.ConnectionStrings["1033"].ConnectionString);
            var database1049 = new YottosCatalogDataContext(ConfigurationManager.ConnectionStrings["1049"].ConnectionString);
            var database1058 = new YottosCatalogDataContext(ConfigurationManager.ConnectionStrings["1058"].ConnectionString);

            var mapping = new YottosCatalogUrlMappingsDataContext();
            var actualUrls = new List<actual_url>();

            foreach (var root in databaseCommon.root_categories)
            {
                var actualUrl = new actual_url() { url = string.Format("/CatalogDetails.aspx?id={0}", root.id) };
                var transformed1033 = new transformed_url()
                {
                    actual_url = actualUrl,
                    lcid = 1033,
                    url = "/" + (from _root in database1033.root_categories
                                 where _root.id == root.id
                                 select _root).Single().name.Replace(" ", "_")
                };
                var transformed1049 = new transformed_url()
                {
                    actual_url = actualUrl,
                    lcid = 1049,
                    url = "/" + (from _root in database1049.root_categories
                                 where _root.id == root.id
                                 select _root).Single().name.Replace(" ", "_")
                };
                var transformed1058 = new transformed_url()
                {
                    actual_url = actualUrl,
                    lcid = 1058,
                    url = "/" + (from _root in database1058.root_categories
                                 where _root.id == root.id
                                 select _root).Single().name.Replace(" ", "_")
                };
                actualUrl.transformed_urls.Add(transformed1033);
                actualUrl.transformed_urls.Add(transformed1049);
                actualUrl.transformed_urls.Add(transformed1058);
                actualUrls.Add(actualUrl);
            }

            Func<YottosCatalogDataContext, int, string> getSubcats = (data, id) => {
                var subcat = (from cat in data.sub_categories
                              where cat.id == id
                              select cat).Single();
                var resultUrl = new StringBuilder("/" + subcat.root_category.name);
                var urlTokens = new List<string>();
                urlTokens.Add(subcat.name);
                var currentCategory = subcat;
                while (currentCategory.root_sub_category_trees.Count != 0)
                {
                    currentCategory = currentCategory.root_sub_category_trees.Single().root_sub_category;
                    urlTokens.Add(currentCategory.name);
                }
                urlTokens.Reverse();
                foreach (var urlToken in urlTokens) resultUrl.AppendFormat("/{0}", urlToken);
                return resultUrl.ToString();
            };

            foreach (var subCat in databaseCommon.sub_categories) {
                var actualUrl = new actual_url() { url = string.Format("/CatalogContents.aspx?id={0}", subCat.id) };
                var transformed1033 = new transformed_url() {
                    actual_url = actualUrl,
                    lcid = 1033,
                    url = getSubcats(database1033, subCat.id).Replace(" ", "_")
                };
                var transformed1049 = new transformed_url() {
                    actual_url = actualUrl,
                    lcid = 1049,
                    url = getSubcats(database1049, subCat.id).Replace(" ", "_")
                };
                var transformed1058 = new transformed_url() {
                    actual_url = actualUrl,
                    lcid = 1058,
                    url = getSubcats(database1058, subCat.id).Replace(" ", "_")
                };
                actualUrl.transformed_urls.Add(transformed1033);
                actualUrl.transformed_urls.Add(transformed1049);
                actualUrl.transformed_urls.Add(transformed1058);
                actualUrls.Add(actualUrl);
            }
            mapping.actual_urls.InsertAllOnSubmit(actualUrls);
            mapping.SubmitChanges();*/
        }

        protected void Session_Start(object sender, EventArgs e) { }

        protected void Application_BeginRequest(object sender, EventArgs e) {
            var domainExt = Request.Url.DnsSafeHost;
            domainExt = domainExt.Substring(domainExt.LastIndexOf(".") + 1);
            var dimainDependCulture = "en-US";
            switch (domainExt) { 
                case "com":
                    dimainDependCulture = "en-US";
                    break;
                case "ua":
                    dimainDependCulture = "uk-UA";
                    break;
                default:
                    dimainDependCulture = "ru-RU";
                    break;
            }
            Thread.CurrentThread.CurrentUICulture = new CultureInfo(dimainDependCulture);
            Thread.CurrentThread.CurrentCulture = new CultureInfo(dimainDependCulture);

            /*var culture = Request.Cookies["culture"];
            if (culture != null && culture.Value != null) {
                Thread.CurrentThread.CurrentUICulture = new CultureInfo(culture.Value);
                Thread.CurrentThread.CurrentCulture = new CultureInfo(culture.Value);
            }*/

            /*else {
                var fullUrl = Request.Url.DnsSafeHost;
                var cultureNode = from _culture in Global.SupportedCulturesXml.Descendants()
                                  where fullUrl.EndsWith((string)_culture.Attribute("domain_ext"))
                                  select _culture;
                if (cultureNode.Count() == 0) {
                    Thread.CurrentThread.CurrentUICulture = new CultureInfo((string)SupportedCulturesXml.Descendants().Last().Attribute("name"));
                    Thread.CurrentThread.CurrentCulture = new CultureInfo((string)SupportedCulturesXml.Descendants().Last().Attribute("name"));
                } else {
                    Thread.CurrentThread.CurrentUICulture = new CultureInfo((string)cultureNode.Single().Attribute("name"));
                    Thread.CurrentThread.CurrentCulture = new CultureInfo((string)cultureNode.Single().Attribute("name"));                
                }
            }*/
        }

        protected void Application_AuthenticateRequest(object sender, EventArgs e) {

        }

        protected void Application_Error(object sender, EventArgs e) {

        }

        protected void Session_End(object sender, EventArgs e) {

        }

        protected void Application_End(object sender, EventArgs e) {

        }
    }
   
}