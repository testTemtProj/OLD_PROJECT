using System;
using System.Linq;
using System.Web;
using System.Text.RegularExpressions;
using System.Threading;
using System.Globalization;
using System.Configuration;
using System.Text;
using System.Collections.Generic;
using System.IO;
using YottosCatalog.Filters;

namespace YottosCatalog.Modules {
    public class UrlRewriterParserModule : IHttpModule {
        private static Regex dynamicUrlChecker = new Regex(@"^(/[\w\040]){1,}([^;\.]*)$", RegexOptions.Compiled | RegexOptions.IgnoreCase);
        private static Regex linkProcessor = new Regex(@"^(?<category>([/\w+,-\?&!'«»\$]{1,}));(?<link>([\w-]+\.){1,}\w+([/\w+\.\?=-]{0,})?$)", RegexOptions.Compiled);
        private static Regex idProcessor = new Regex(@"(/)?(?<page>\w*)\.aspx\?id=(?<id>\d*)", RegexOptions.Compiled);
        private static Regex linkCaptionProcessor = new Regex(@"^(?<category>([/\w+,-\?&!'«»\$]{1,}));(?<link>([\w,-\?!=\(\)&'«»\$]+))", RegexOptions.Compiled);        

        private static string appThemes = "/App_Themes";

        public void Dispose() { }
       
        public void Init(HttpApplication context) {
            context.BeginRequest += new EventHandler(context_BeginRequest);            
        }

        void context_BeginRequest(object sender, EventArgs e) {            
            var application = sender as HttpApplication;
            var Request = application.Request;
            var Context = application.Context;

            var culture = Request.Cookies["culture"];
            if (culture != null && culture.Value != null) {
                Thread.CurrentThread.CurrentUICulture = new CultureInfo(culture.Value);
                Thread.CurrentThread.CurrentCulture = new CultureInfo(culture.Value);
            }
            Thread.CurrentThread.CurrentUICulture = Thread.CurrentThread.CurrentCulture;

            var requestPath = application.Server.UrlDecode(Request.Path);
            if (Global.EnableMemorableUrl) { 
                if (requestPath.Contains(appThemes) && !requestPath.StartsWith(appThemes)) Context.RewritePath(requestPath.Substring(requestPath.IndexOf("/App_Themes")));
                foreach (var route in Global.routes) if (requestPath.Contains(route.Path)) return;                
            }
            
            if (Global.EnableMemorableUrl) {                                
                if (dynamicUrlChecker.IsMatch(requestPath)) {
                    var mappingDatabase = new YottosCatalogUrlMappingsDataContext();
                    var transformedUrls = from _url in mappingDatabase.transformed_urls
                                          where _url.url.Equals(requestPath)
                                          select _url;
                    if (transformedUrls.Count() == 1) Context.RewritePath(transformedUrls.Single().actual_url.url);
                    else if (transformedUrls.Count() > 1) Context.RewritePath(transformedUrls.First().actual_url.url);
                    else Context.RewritePath("/CatalogList.aspx");
                } else { 
                    var match = linkProcessor.Match(requestPath);
                    if (match.Success) {
                        var categoryTransformed = match.Result("${category}");
                        var linkTransformed = match.Result("${link}");
                        var mapping = new YottosCatalogUrlMappingsDataContext();

                        var categoryActualUrls = (from _trans in mapping.transformed_urls
                                                  where _trans.url.Equals(categoryTransformed)
                                                  select _trans).ToList();
                        transformed_url categoryTransformedUrl = null;

                        if (categoryActualUrls.Count == 1)
                            categoryTransformedUrl = categoryActualUrls.Single();
                        else if (categoryActualUrls.Count > 1)
                            categoryTransformedUrl = categoryActualUrls.First();
                        else Context.RewritePath("/CatalogList.aspx");

                        if (categoryTransformedUrl != null) {
                            var categoryActualUrl = categoryTransformedUrl.actual_url.url;
                            var matchId = idProcessor.Match(categoryActualUrl);
                            if (matchId.Success) {

                                var categoryId = int.Parse(matchId.Result("${id}"));
                                var category = (from _cat in new YottosCatalogDataContext().sub_categories where _cat.id == categoryId select _cat).Single();
                                var clickedLink = from _lnk in category.links where _lnk.url.Contains(linkTransformed) select _lnk;

                                if (clickedLink.Count() == 1)
                                    Context.RewritePath(string.Format("/Handlers/LinkClickHandler.ashx?id={0}", clickedLink.Single().id));

                                else if (clickedLink.Count() > 1) Context.RewritePath(string.Format("/Handlers/LinkClickHandler.ashx?id={0}", clickedLink.First().id));
                                else Context.RewritePath("/CatalogList.aspx");
                            }
                        }
                    }                    
                    else if ((match = linkCaptionProcessor.Match(requestPath)).Success) {
                        var categoryTransformed = match.Result("${category}");
                        var linkCaptionTransformed = match.Result("${link}");
                        var mapping = new YottosCatalogUrlMappingsDataContext();

                        var categoryActualUrls = (from _trans in mapping.transformed_urls
                                                  where _trans.url.Equals(categoryTransformed)
                                                  select _trans).ToList();
                        transformed_url categoryTransformedUrl = null;

                        if (categoryActualUrls.Count == 1)
                            categoryTransformedUrl = categoryActualUrls.Single();
                        else if (categoryActualUrls.Count > 1)
                            categoryTransformedUrl = categoryActualUrls.First();
                        else Context.RewritePath("/CatalogList.aspx");

                        if (categoryTransformedUrl != null) {
                            var categoryActualUrl = categoryTransformedUrl.actual_url.url;
                            var matchId = idProcessor.Match(categoryActualUrl);
                            if (matchId.Success) {
                                var categoryId = int.Parse(matchId.Result("${id}"));
                                var category = (from _cat in new YottosCatalogDataContext().sub_categories where _cat.id == categoryId select _cat).Single();
                                var clickedLink = from _lnk in category.links where linkCaptionTransformed.Equals(_lnk.url_prepared_caption) select _lnk;

                                if (clickedLink.Count() == 1)
                                    Context.RewritePath(string.Format("/Handlers/LinkClickHandler.ashx?id={0}", clickedLink.Single().id));

                                else if (clickedLink.Count() > 1) Context.RewritePath(string.Format("/Handlers/LinkClickHandler.ashx?id={0}", clickedLink.First().id));
                                else Context.RewritePath("/CatalogList.aspx");
                            }
                        }
                    }
                }
            }          
        }
    }
}
