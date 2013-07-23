using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Globalization;
using System.Threading;
using System.Xml.Linq;
using YottosCatalog.Code;

namespace YottosCatalog {
    public partial class Settings : MenuPage {
        protected void Page_Load(object sender, EventArgs e) {
            Master.Description = Resources.CatalogResources.SettingsTitle;
        }

        private void SaveSettings() {
            var culture = new HttpCookie("culture", culturesList.SelectedValue);
            var pageSize = new HttpCookie("page_size", pageSizeDropDown.SelectedValue);
            Response.Cookies.Add(culture);
            Response.Cookies.Add(pageSize);
            Thread.CurrentThread.CurrentCulture = new CultureInfo(culturesList.SelectedValue);
            Thread.CurrentThread.CurrentUICulture = new CultureInfo(culturesList.SelectedValue); 
        }

        protected void Transfer_Click(object sender, EventArgs e) {
            SaveSettings();
            Response.Redirect(Resources.CatalogResources.Master_WebLink);
        }

        protected void Save_Click(object sender, EventArgs e) {
            SaveSettings();
            Response.Redirect(Resources.CatalogPageUrlsMapping.CatalogList, true);
        }

        protected void culturesList_DataBound(object sender, EventArgs e) {
                var culture = Thread.CurrentThread.CurrentUICulture.Name;
                XElement cultureNode = null;
                try {
                    cultureNode = (from _culture in Global.SupportedCulturesXml.Descendants()
                                   where ((string)_culture.Attribute("name")).Equals(culture, StringComparison.InvariantCultureIgnoreCase)
                                   select _culture).Single();

                } catch { cultureNode = Global.SupportedCulturesXml.Descendants().Last(); } 
                finally {
                    foreach (var item in (sender as DropDownList).Items)
                        if ((item as ListItem).Value.Equals((string)cultureNode.Attribute("name")))
                            (item as ListItem).Selected = true;             
                }             
        }
    }
}
