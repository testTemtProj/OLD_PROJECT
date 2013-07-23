using System;
using System.Collections.Generic;
using System.Linq;
using System.Xml.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Threading;
using System.Configuration;
using System.Text;
using System.Globalization;
using System.IO;
using YottosCatalog.Code;

namespace YottosCatalog {
    public partial class SitemapGenerator : Page {
        protected void Page_Load(object sender, EventArgs e) {
            
        }

        protected void Generate_Click(object sender, EventArgs e) {
            new Thread(new ParameterizedThreadStart(lcid => {
                var database = new YottosCatalogDataContext(ConfigurationManager.ConnectionStrings[lcid.ToString()].ConnectionString);
                XNamespace xmlns = "http://www.sitemaps.org/schemas/sitemap/0.9";
                var sitemapRoot = new XElement(xmlns + "urlset");                
                var catalogUrl = "http://catalog.yottos.";
                var sitemapFilename = "sitemap.";
                switch (lcid.ToString()) { 
                    case "1033":
                        catalogUrl += "com/";
                        sitemapFilename += "com.xml";
                        break;
                    case "1049":
                        catalogUrl += "ru/";
                        sitemapFilename += "ru.xml";
                        break;
                    case "1058":
                        catalogUrl += "com.ua/";
                        sitemapFilename += "ua.xml";
                        break;
                }
                foreach (var root in database.root_categories) 
                    sitemapRoot.Add(new XElement("url", new XElement("loc", catalogUrl + root.name.Replace(" ", "_"))));
                foreach (var subCat in database.sub_categories) {
                    var resultUrl = new StringBuilder(catalogUrl + subCat.root_category.name);
                    var urlTokens = new List<string>();
                    urlTokens.Add(subCat.name);
                    var currentCategory = subCat;
                    while (currentCategory.root_sub_category_trees.Count != 0) {
                        currentCategory = currentCategory.root_sub_category_trees.Single().root_sub_category;
                        urlTokens.Add(currentCategory.name);
                    }
                    urlTokens.Reverse();
                    foreach (var urlToken in urlTokens) resultUrl.AppendFormat("/{0}", urlToken);
                    sitemapRoot.Add(new XElement("url", new XElement("loc", resultUrl.ToString().Replace(" ", "_"))));
                }
                File.WriteAllText(Server.MapPath("~/" + sitemapFilename), sitemapRoot.ToString().Replace(" xmlns=\"\"", ""));                
            })).Start(culturesList.SelectedValue);
            statusLabel.Text = string.Format("начат процесс генерации sitemap для локали {0}", new CultureInfo(int.Parse(culturesList.SelectedValue)));
        }
    }
}
