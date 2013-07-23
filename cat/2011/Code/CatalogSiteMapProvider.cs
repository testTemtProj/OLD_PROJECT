using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Collections;
using System.IO;
using System.Collections.Specialized;
using System.Text.RegularExpressions;

namespace YottosCatalog.Code {
    public class CatalogSiteMapProvider : SiteMapProvider {
        private static Regex idExtractor = new Regex(@"(http(s)?://)?[\w/\.]\.aspx\?id=(?<id>\d*)", RegexOptions.Compiled); 

        public override SiteMapNode FindSiteMapNode(string rawUrl) {
            var database = new YottosCatalogDataContext();
            if (rawUrl.Contains("CatalogList.aspx") || rawUrl.Contains("CatalogDetails.aspx"))
                return new SiteMapNode(this, string.Empty, "/", Resources.CatalogResources.ToCatalogListLinkCaption, Resources.CatalogResources.ToCatalogListLinkCaption);
            else if (rawUrl.Contains("CatalogContents.aspx")) {
                var match = idExtractor.Match(rawUrl);
                if (match.Success) {
                    int id = 1;                    
                    int.TryParse(match.Result("${id}"), out id);
                    var currentSubCategory = (from category in database.sub_categories
                                              where category.id == id
                                              select category).Single();
                    return new SiteMapNode(this, string.Empty, string.Format("/CatalogContents.aspx?id={0}", currentSubCategory.id), currentSubCategory.name, currentSubCategory.name);
                }
            }
            return null;
        }
        
        public override SiteMapNode GetParentNode(SiteMapNode node) {
            var database = new YottosCatalogDataContext();
            if (node.Url.Contains("CatalogList.aspx")) return null;
            else if (node.Url.Contains("CatalogDetails.aspx")) return new SiteMapNode(this, string.Empty, "/", Resources.CatalogResources.ToCatalogListLinkCaption, Resources.CatalogResources.ToCatalogListLinkCaption);             
            else if (node.Url.Contains("CatalogContents.aspx")) {
                var match = idExtractor.Match(node.Url);
                if (match.Success) {
                    int id = 1;
                    int.TryParse(match.Result("${id}"), out id);
                    var currentSubCategory = (from category in database.sub_categories
                                              where category.id == id
                                              select category).Single();
                    if (currentSubCategory.root_sub_category_trees.Count == 0) return new SiteMapNode(this, string.Empty, string.Format("/CatalogDetails.aspx?id={0}", currentSubCategory.root_category_id), currentSubCategory.root_category.name, currentSubCategory.root_category.root_category_description);
                    var parentSubcategory = currentSubCategory.root_sub_category_trees.Single().root_sub_category;
                    return new SiteMapNode(this, string.Empty, string.Format("/CatalogContents.aspx?id={0}", parentSubcategory.id), parentSubcategory.name, parentSubcategory.name);
                }
            }
            return null;
        }

        public override SiteMapNodeCollection GetChildNodes(SiteMapNode node) {
            /*var result = new SiteMapNodeCollection();
            var strId = node.Url.Substring(node.Url.LastIndexOf("=") + 1);
            var id = int.Parse(strId);
            var currentSubCategory = (from category in database.sub_categories
                                      where category.id == id
                                      select category).Single();
            if (currentSubCategory.nested_sub_category_trees.Count > 0) 
                foreach (var nestedSubCategory in from tree in currentSubCategory.nested_sub_category_trees select tree.nested_sub_category) 
                    result.Add(new SiteMapNode(this, string.Empty, string.Format("CatalogContents.aspx?id={0}", nestedSubCategory.id), nestedSubCategory.name, nestedSubCategory.name));                            
            return result;*/
            throw new NotImplementedException("this feature is never used for SiteMapPath!");
        }
        protected override SiteMapNode GetRootNodeCore() {
            //return new SiteMapNode(this, string.Empty, "CatalogList.aspx", Resources.CatalogResources.ToCatalogListLinkCaption, Resources.CatalogResources.ToCatalogListLinkCaption);
            throw new NotImplementedException("this feature is never used for SiteMapPath!");
        }
    }
}
