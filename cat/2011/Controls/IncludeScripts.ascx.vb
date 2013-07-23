
Partial Class Controls_IncludeScripts
    Inherits System.Web.UI.UserControl

    Protected Sub Page_Init(ByVal sender As Object, ByVal e As System.EventArgs) Handles Me.Init
    End Sub

    Protected Sub Page_Load(ByVal sender As Object, ByVal e As System.EventArgs) Handles Me.Load
        Dim manager As ClientScriptManager = Page.ClientScript
        manager.RegisterClientScriptInclude("jquery", ResolveClientUrl("/jQuery/lib/jquery.min.js"))
        manager.RegisterClientScriptInclude("jqueryAutocomplete1", ResolveClientUrl("/jQuery/lib/jquery.bgiframe.min.js"))
        manager.RegisterClientScriptInclude("jqueryAutocomplete2", ResolveClientUrl("/jQuery/lib/jquery.ajaxQueue.js"))
        manager.RegisterClientScriptInclude("jqueryAutocomplete", ResolveClientUrl("/jQuery/jquery.autocomplete.js"))
        manager.RegisterClientScriptInclude("jqueryAutocomplete3", ResolveClientUrl("/jQuery/searchstring.autocomplete.js"))
        manager.RegisterClientScriptInclude("searchQueryBuilder", ResolveClientUrl("/Script/SearchQueryBuilder.js"))
        Dim css As New HtmlLink
        css.Href = ResolveClientUrl("/jQuery/jquery.autocomplete.css")
        css.Attributes.Add("type", "text/css")
        css.Attributes.Add("rel", "stylesheet")
        Me.Controls.Add(css)
    End Sub

    '    <script type="text/javascript" src="/jQuery/lib/jquery.min.js"></script>
    '<script type='text/javascript' src='/jQuery/lib/jquery.bgiframe.min.js'></script>
    '<script type='text/javascript' src='/jQuery/lib/jquery.ajaxQueue.js'></script>
    '<script type='text/javascript' src='/jQuery/jquery.autocomplete.js'></script>
    '<link rel="stylesheet" type="text/css" href="jQuery/jquery.autocomplete.css" />

End Class
