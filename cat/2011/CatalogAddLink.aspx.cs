using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Data.Linq;
using System.Net;
using System.Threading;
using System.Globalization;
using YottosCatalog.Code;

namespace YottosCatalog {
    public partial class CatalogAddLink : MenuPage {
        protected void Page_Load(object sender, EventArgs e) 
        {
            Response.Write("!");
        }

        protected void rootCategoryDropDownList_DataBound(object sender, EventArgs e) {
            var selectedValStr = (sender as DropDownList).SelectedValue;
            var database = new YottosCatalogDataContext();
            var rootCategory = (from root in database.root_categories
                                where root.id == int.Parse(selectedValStr)
                                select root).Single();
            var subCategoriesRoot = from subCat in rootCategory.sub_categories
                                    where subCat.root_sub_category_trees.Count == 0
                                    select subCat;
            SubCategoriesTree.Nodes.Clear();
            foreach (var subCategory in subCategoriesRoot)
                SubCategoriesTree.Nodes.Add(BuildNodeTree(subCategory));
            if (SubCategoriesTree.Nodes.Count > 0) SubCategoriesTree.Nodes[0].Select();
            SubCategoriesTree.CollapseAll();
            Master.Description = Resources.CatalogResources.CatalogTitle;
        }

        protected void rootCategoryList_SelectedIndexChanged(object sender, EventArgs e) {
            rootCategoryDropDownList_DataBound(sender, e);
        }

        private TreeNode BuildNodeTree(sub_category category) {
            var node = new TreeNode(category.name, category.id.ToString());
            foreach (var nestedSubCategory in from tree in category.nested_sub_category_trees
                                              select tree.nested_sub_category) 
                node.ChildNodes.Add(BuildNodeTree(nestedSubCategory));            
            return node;
        }

        protected void AddButton_Click(object sender, EventArgs e) {
            if (!SecretWordTextBox.Text.Equals(Session["secret_word"])) {
                AutoCustomValidator.IsValid = false;
                return;
            }
            var database = new YottosCatalogDataContext();
            var subCategory = (from category in database.sub_categories
                               where category.id == int.Parse(SubCategoriesTree.SelectedValue)
                               select category).Single();

            var postingLink = new link() { 
                url = LinkTextBox.Text,
                caption = TitleTextBox.Text,
                link_description = AboutTextBox.Text,
                author_email = EmailTextBox.Text,
                date_add = DateTime.Now.Date,
                sub_category = subCategory,
                last_checked = DateTime.Now.Date
            };
            database.SubmitChanges(ConflictMode.FailOnFirstConflict);
            new Thread((linkIdBoxed) => {
                var linkId = (int)linkIdBoxed;
                if (linkId > 0) {
                    var theDatabase = new YottosCatalogDataContext();
                    var link = (from _link in theDatabase.links
                                where _link.id == linkId
                                select _link).Single();
                    
                    var client = new WebClient();
                    client.Headers.Add(HttpRequestHeader.UserAgent, "Mozilla/5.0 (compatible; YottosCatalogBot/1.0; +http://catalog.yottos.com)");
                    try {
                        client.DownloadString(link.url);
                        link.is_accepted = true;
                    } catch {
                        link.is_accepted = false;
                    } finally { theDatabase.SubmitChanges(); }
                }

            }).Start(postingLink.id);
            
            Response.Redirect(Resources.CatalogPageUrlsMapping.CatalogLinkPosted, true);
        }
    }
}
