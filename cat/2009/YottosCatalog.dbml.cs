using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Web;
using System.Configuration;
using System.Threading;
using System.Xml.Linq;
using System.Data.SqlClient;
using System.Data;
using System.Text.RegularExpressions;

namespace YottosCatalog {
    public partial class YottosCatalogDataContext {
        public static IEnumerable<root_category> GetRooCategoriesForMaster() { 
            var roots = new List<root_category>();
            roots.Add(new root_category() { id = 0, name = Resources.CatalogResources.RootAllCategoriesText });
            roots.AddRange(new YottosCatalogDataContext().root_categories.OrderBy(root => root.name));
            return roots;
        }

        public static IEnumerable<sub_category> GetSubcategoriesRoots(int rootCategoryId) {
            return (from subcat in new YottosCatalogDataContext().sub_categories
                    where subcat.root_sub_category_trees.Count == 0 && subcat.root_category_id == rootCategoryId
                    orderby subcat.name
                    select subcat).ToList();
        }

        public static IEnumerable<sub_category> GetNestedCategories(int rootSubCategoryId) {
            return from tree in
                       (from cat in new YottosCatalogDataContext().sub_categories
                        where cat.id == rootSubCategoryId
                        select cat).Single().nested_sub_category_trees
                   select tree.nested_sub_category;
        }

        public static IEnumerable<link> SearchLinks(string searchText, string category) {
            var rootCategoryId = 0;
            int.TryParse(category, out rootCategoryId);            
            if (!string.IsNullOrEmpty(searchText)) {

                var queryT_SQL = new StringBuilder(string.Format("select lnk.* from links as lnk inner join freetexttable(links, *,  N'\"{0}\"', 1049) as ft on lnk.id = ft.[key] ", searchText));
                if (rootCategoryId > 0) queryT_SQL.AppendFormat("where sub_category_id in (select id from sub_categories where root_category_id = {0}) ", rootCategoryId);
                queryT_SQL.Append("order by ft.rank desc, lnk.link_counter");
 	                 
                var database = new YottosCatalogDataContext();
                var linksFound = database.ExecuteQuery<link>(queryT_SQL.ToString()).ToList();

                var lcid = Thread.CurrentThread.CurrentCulture.LCID;
                var supportedCultures = from culture in Global.SupportedCulturesXml.Descendants()
                                        select (int)culture.Attribute("lcid");
                if (!supportedCultures.Contains(lcid)) lcid = supportedCultures.Last();

                var connection = new SqlConnection(database.Connection.ConnectionString);
                connection.Open();
                var query = new SqlCommand("select display_term from sys.dm_fts_parser(N'FORMSOF(FREETEXT, \"" + searchText + "\")', @lcid, 0, 0)", connection);
                var localeId = new SqlParameter("@lcid", lcid);
                query.Parameters.Add(localeId);
                var reader = query.ExecuteReader();
                var termList = new List<string>();
                while (reader.Read()) termList.Add(reader.GetString(0));
                connection.Close();

                foreach (var term in termList) {
                    var termMatch = new Regex(term, RegexOptions.IgnoreCase);
                    foreach (var linkFound in linksFound) {
                        linkFound.caption = termMatch.Replace(linkFound.caption, match => string.Format("<b>{0}</b>", match.Value));
                        linkFound.link_description = termMatch.Replace(linkFound.link_description, match => string.Format("<b>{0}</b>", match.Value));
                        linkFound.url = termMatch.Replace(linkFound.url, match => string.Format("<b>{0}</b>", match.Value));
                    }
                }
                return linksFound;
            }
            return null;
        }

        public static string GetConnectionStringName() {
            var lcid = Thread.CurrentThread.CurrentCulture.LCID;
            var supportedCultures = from culture in Global.SupportedCulturesXml.Descendants()
                                    select (int)culture.Attribute("lcid");
            if (!supportedCultures.Contains(lcid)) lcid = supportedCultures.Last();
            return lcid.ToString();
        }

        public YottosCatalogDataContext() : base(ConfigurationManager.ConnectionStrings[GetConnectionStringName()].ConnectionString) {            
            OnCreated();
        }
    }

    public partial class sub_category {
        public override string ToString() { return name; }
    }

    public partial class root_category {
        public IEnumerable<sub_category> FirstThreeSubCategories {
            get {
                return (from sub in new YottosCatalogDataContext().sub_categories
                        where sub.root_category_id == id && sub.root_sub_category_trees.Count == 0
                        select sub).Take(3);
            }
        }
    }

    public partial class answer {
        public bool HasImage {
            get {
                if (string.IsNullOrEmpty(image_type) | answer_image == null) return false;
                return true;
            }
        }
    }
}