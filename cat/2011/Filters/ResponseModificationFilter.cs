using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Globalization;
using System.Threading;

namespace YottosCatalog.Filters {
    public class ResponseModificationFilter : CatalogFilterBase {
        private static Regex idProcessor = new Regex(@"(/)?(?<page>\w*)\.aspx\?id=(?<id>\d*)", RegexOptions.Compiled);

        public ResponseModificationFilter(Stream responseStream, YottosCatalogDataContext Database, YottosCatalogUrlMappingsDataContext MappingDatabase) : base(responseStream, Database, MappingDatabase) { }       

        private enum MappingActions { Save, Insert, None }

        protected override void BeforeFlush() {
            var buffer = responseBytes.ToArray();
            var encoding = Encoding.UTF8;
            var html = encoding.GetString(buffer);
            html = idProcessor.Replace(html, (match) => {
                var hrefUrl = match.Value;
                if (!hrefUrl.StartsWith("/")) hrefUrl = "/" + hrefUrl;
                var actualUrls = from _url in mappingDatabase.actual_urls
                                 where _url.url.Equals(hrefUrl)
                                 select _url;
                MappingActions actions = MappingActions.None;
                actual_url actualUrl = null;
                transformed_url transformedUrl = null;
                if (actualUrls.Count() == 1) actualUrl = actualUrls.Single();
                else {
                    actualUrl = new actual_url() { url = hrefUrl };
                    actions = MappingActions.Insert;
                }
                if (actions == MappingActions.None) {
                    var transformedUrls = from _url in actualUrl.transformed_urls
                                          where _url.lcid == Thread.CurrentThread.CurrentCulture.LCID
                                          select _url;
                    if(transformedUrls.Count() == 1) transformedUrl = transformedUrls.Single();                       
                }
                if (transformedUrl != null) return transformedUrl.url;
                else {
                    if (actions == MappingActions.None) actions = MappingActions.Save;
                    transformedUrl = new transformed_url() { 
                        lcid = Thread.CurrentThread.CurrentCulture.LCID
                    };                    
                    switch (match.Result("${page}")) {
                        case "CatalogContents":
                            var subCategoryId = int.Parse(match.Result("${id}"));
                            var subCategory = (from _sub in database.sub_categories
                                               where _sub.id == subCategoryId
                                               select _sub).Single();
                            var rootTree = subCategory.root_sub_category_trees;
                            var urlTokens = new List<string>();
                            urlTokens.Add(subCategory.name);
                            while (rootTree.Count != 0) {
                                subCategory = rootTree.Single().root_sub_category;
                                urlTokens.Add(subCategory.name);
                                rootTree = subCategory.root_sub_category_trees;
                            }
                            urlTokens.Add(subCategory.root_category.name);
                            var resultUrl = new StringBuilder();
                            foreach (var token in urlTokens.Reverse<string>()) resultUrl.AppendFormat("/{0}", token);
                            transformedUrl.url = resultUrl.ToString();
                            break;
                        case "CatalogDetails":
                            var rootCategoryId = int.Parse(match.Result("${id}"));
                            var rootCategoryName = (from _root in database.root_categories
                                                    where _root.id == rootCategoryId
                                                    select _root.name).Single();
                            transformedUrl.url = string.Format("/{0}", rootCategoryName);
                            break;
                        default: return match.Value;
                    }
                    transformedUrl.url = transformedUrl.url.Replace(" ", "_");
                    transformedUrl.actual_url = actualUrl;
                    actualUrl.transformed_urls.Add(transformedUrl);
                }

                switch (actions) { 
                    case MappingActions.Insert:
                        mappingDatabase.actual_urls.InsertOnSubmit(actualUrl);
                        mappingDatabase.SubmitChanges();
                        break;
                    case MappingActions.Save:
                        mappingDatabase.SubmitChanges();
                        break;
                }
                return transformedUrl.url;                              
            });
            buffer = encoding.GetBytes(html);
            baseStream.Write(buffer, 0, buffer.Length);
        }
    }
}
