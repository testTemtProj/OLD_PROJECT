using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Text;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading;
using System.Data.Linq;

namespace YottosCatalog.Filters {
    public class LinksResultModificationFilter : CatalogFilterBase {
        private static Regex linkProcessor = new Regex(@"(/)?Handlers/LinkClickHandler.ashx\?id=(?<id>\d*)&amp;cat=(?<cat>\d*)", RegexOptions.Compiled),
                             linkCaptionProcessor = new Regex(@"(/)?Handlers/LinkClickHandler.ashx\?id=(?<id>\d*)&amp;cat=(?<cat>\d*)&amp;showname=1", RegexOptions.Compiled);

        public LinksResultModificationFilter(Stream responseStream, YottosCatalogDataContext Database, YottosCatalogUrlMappingsDataContext MappingDatabase) : base(responseStream, Database, MappingDatabase) { }

        public static string FilterLinkCaption(string caption) {            
            caption = caption.Replace(":", string.Empty).
                              Replace(";", string.Empty).
                              Replace("+", string.Empty).
                              Replace("/", string.Empty).
                              Replace("\\", string.Empty).
                              Replace("*", string.Empty).
                              Replace("\"", string.Empty).
                              Replace("(", string.Empty).
                              Replace(")", string.Empty).
                              Replace("[", string.Empty).
                              Replace("]", string.Empty).
                              Replace("-", "_").
                              Replace("–", "_").
                              Replace("—", "_").
                              Replace("&nbsp;", "_").                              
                              Replace(".", ",").
                              Replace("?", string.Empty).
                              Replace("@", string.Empty).
                              Replace("&", string.Empty).
                              Replace("|", string.Empty).
                              Replace(" ", "_");
            return caption;
        }

        protected override void BeforeFlush() {
            var buffer = responseBytes.ToArray();
            var encoding = Encoding.UTF8;
            var html = encoding.GetString(buffer);
            responseBytes.AddRange(buffer);
            html = encoding.GetString(buffer);
            html = linkCaptionProcessor.Replace(html, (match) => {
                return BuildLink(match, true);
            });
            html = linkProcessor.Replace(html, (match) => {
                return BuildLink(match, false);
            });
            buffer = encoding.GetBytes(html);
            baseStream.Write(buffer, 0, buffer.Length);
        }
        
        private string BuildLink(Match match, bool needName) { 
            var categoryIdName = string.Format("/CatalogContents.aspx?id={0}", match.Result("${cat}"));
            var linkTransformedUrl = new StringBuilder();
            var actualCategories = (from actual_cat in mappingDatabase.actual_urls
                                    where actual_cat.url.Equals(categoryIdName)
                                    select actual_cat).ToList();
            if (actualCategories.Count == 1) {
                var tranformedCategories = (from transformed in actualCategories.Single().transformed_urls
                                            where transformed.lcid == Thread.CurrentThread.CurrentCulture.LCID
                                            select transformed).ToList();
                if (tranformedCategories.Count == 1) {
                    linkTransformedUrl.Append(tranformedCategories.Single().url);
                    var currentLink = (from lnk in database.links
                                       where lnk.id == int.Parse(match.Result("${id}"))
                                       select lnk).Single();
                    if (string.IsNullOrEmpty(currentLink.url_prepared_caption)) {
                        currentLink.url_prepared_caption = FilterLinkCaption(currentLink.caption);
                        database.SubmitChanges(ConflictMode.FailOnFirstConflict);
                    }
                    if(!needName)
                        linkTransformedUrl.AppendFormat(";{0}", currentLink.url.ToLower().Replace("http://", string.Empty).TrimEnd('/'));
                    else linkTransformedUrl.AppendFormat(";{0}", currentLink.url_prepared_caption);
                }
            }
            return linkTransformedUrl.ToString();         
        }       
    }
}