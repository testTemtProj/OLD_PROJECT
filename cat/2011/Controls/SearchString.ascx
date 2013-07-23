<%@ Control Language="VB" AutoEventWireup="false" CodeFile="SearchString.ascx.vb" Inherits="Controls_SearchString"  %>
<%@ Register Src="LangInstaller.ascx" TagName="LangInstaller" TagPrefix="uc1" %>
<%@ Register Src="~/Controls/IncludeScripts.ascx" TagName="IncludeScripts" TagPrefix="uc" %>

<script language="javascript" type="text/javascript">
    function cleanQueryBox() {
        var f = document.getElementById("searchString");
        f.value = f.value.replace(/:|^\s*|\s*$/g, '');
    }
</script><uc:IncludeScripts runat="server" ID="Scripts" />
			
<table width="810px" cellpadding="0" cellspacing="0" border="0" style="margin-top: 5px" >
        <tr>
<asp:Panel ID="LogoCell" Visible="true" runat="server">
            <td style="width:154px;  border-left: #ffffff 1px solid;" valign="top">
                <asp:HyperLink ID="WebLogoHyperLink" runat="server" NavigateUrl="~/"> <asp:Image ID="TopImage" runat="server" Width="125" ImageUrl="~/img/Logo.gif" style="vertical-align:bottom; " />
                </asp:HyperLink>
            </td>
</asp:Panel>
            <td align="left" valign="middle" >
                <table>
                    <tr>
                        <td>
                  			<ul class="h-icons">
			                    <li id="icons-web" class="h-icons-web"><asp:HyperLink ID="WebHyperLink" runat="server" Text="Веб" NavigateUrl="http://yottos.ru" onmouseover="buildSearchUrl(this)" /></li>
			                    <li id="icons-zero" class="h-icons-zero"><asp:HyperLink ID="ZeroHyperLink" runat="server"  NavigateUrl="http://zero.yottos.ru" onmouseover="buildSearchUrl(this)">Zero</asp:HyperLink></li>
			                    <li id="icons-news" class="h-icons-news"><asp:HyperLink ID="NewsHyperLink" runat="server" NavigateUrl="http://news.yottos.ru" onmouseover="buildSearchUrl(this)">Новости</asp:HyperLink></li>
			                    <li id="icons-catalog" class="h-icons-catalog"><asp:HyperLink ID="CatalogHyperLink" runat="server" NavigateUrl="http://catalog.yottos.ru" Text="Каталог" onmouseover="buildSearchUrl(this)"></asp:HyperLink></li>
			                    <li id="icons-rynok" class="h-icons-rynok"><asp:HyperLink ID="RynokHyperLink" runat="server" NavigateUrl="http://rynok.yottos.ru" onmouseover="buildSearchUrl(this)" Text="Рынок"></asp:HyperLink></li>
		                    </ul>
                        </td>
                        <td align="center" valign="middle" style="width: 116px" >
                            </td>
                    </tr>
                    <tr>
                        <td>
                            <div id="divQueryBox"><asp:TextBox ID="QueryTextBox" runat="server" style="	width: 528px; height: 22px;	padding: 0;	margin: 0;	border: 1px solid #667; font-size: 10pt;	line-height: 25px;" /></div></td>
                            <td align="center" style="width: 116px; ">
                            <asp:Button ID="SearchButton" runat="server" Text="Поиск в Yottos" Width="115px" OnClick="SearchButton_Click" CausesValidation="False" UseSubmitBehavior="False" OnClientClick="javascript:cleanQueryBox()" /></td>
                    </tr>
                    <tr>
                        <td align="center">
                             &nbsp;</td>
                        <td style="width: 116px" align="center">
                            <asp:HyperLink ID="AdvancedSearchHyperLink" runat="server" CssClass="settinglink" NavigateUrl="~/Расширенный_Поиск" Text="Расширенный поиск"></asp:HyperLink>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
</table>

<script type="text/javascript">
    document.getElementById('<%= QueryTextBox.ClientID  %>').onkeypress = function(e) {
        if (e.keyCode == 13) {
            e.cancelBubble = true;
            var ctrl = document.getElementById("<%= SearchButton.ClientID  %>");
            if (ctrl) {
                ctrl.focus();
                ctrl.click();
            }
            return false;
        }
    };
    function cleanQueryBox() {
        var f = document.getElementById('<%= QueryTextBox.ClientID  %>');
        f.value = f.value.replace(/:|^\s*|\s*$/g, '');
    }
</script>
<script type="text/javascript">

    var brName = navigator.appName;
    var updateOpera = false;
    var updateExplorer = false;
    if (brName == 'Opera' && parseFloat(navigator.appVersion) < 9.5)
        updateOpera = true;
    else
        if (brName == 'Microsoft Internet Explorer' && parseFloat((new RegExp("MSIE ([0-9]{1,}[.0-9]{0,})")).exec(navigator.userAgent)[1]) < 6)
        updateExplorer = true; if (!updateOpera && !updateExplorer && (typeof (jQuery) !== typeof (undefined))) {
        curTheme = "";
        $(function() {
            var d = 80;
            function format(item) {
                return item.term;
                if (item.theme != curTheme) {
                    curTheme = item.theme;
                    return "<b>" + item.theme + "</b> " + item.term
                } return item.term
            } $("#ctl00_SearchString1_QueryTextBox").autocomplete("suggest.fcgi", { multiple: false, max: 80, appendTo: "#divQueryBox", selectFirst: false, width: $("#ctl00_SearchString1_QueryTextBox").width(), maxColumnWidth: 400, delay: d, spaceToContinue: true, parse: function(data) { return $.map(eval(data), function(rowTheme) { var theme = rowTheme.t; var terms = $.map(rowTheme.w, function(rowTerm) { return { data: { theme: theme, term: rowTerm[0], childCount: rowTerm[1], charsEntered: rowTerm[2] }, value: rowTerm[0], result: rowTerm[0]} }); return terms }) }, formatItem: function(item) { return format(item) } }).result(function(e, item) { if (document.getElementById("ctl00_SearchString1_SearchButton") != null) { document.getElementById("ctl00_SearchString1_SearchButton").focus(); document.getElementById("ctl00_SearchString1_SearchButton").click() } else { document.getElementById("SearchString1_SearchButton").focus(); document.getElementById("SearchString1_SearchButton").click() } })
        });
    }
</script>
<script type="text/javascript">
    function buildSearchUrl(sender) {
        function getSearchUrl(href) {
            var r = /yottos\.(com\.ua|ru|com)/;
            var domain = window.location.host.match(r);
            var host = domain ? ('http://' + domain[0] + '/') : 'http://yottos.ru/';
            var lang = domain ? domain[1] : 'ru';
            var link = '';
            var txtControl = document.getElementById("searchString") ||
                         document.getElementById("QueryTextBox") ||
                         document.getElementById("ctl00_SearchString1_QueryTextBox") ||
                         document.getElementById("ctl00_QueryTextBox") ||
                         document.getElementById("SearchString_QueryTextBox") ||
                         document.getElementById("ctl00_SearchString_QueryTextBox");
            if (!txtControl || !txtControl.value) return href;
            var query = txtControl.value.replace(/[:;]/g, '');
            switch (lang) {
                case 'com':
                    link = (href.match('news\.yottos\.') && ("http://news.yottos.com/Поиск?" + query)) ||
                       (href.match('rynok\.yottos\.') && ("http://rynok.yottos.com/поиск/" + query)) ||
                       (href.match('catalog\.yottos\.') && ("http://catalog.yottos.com/yottos-каталог/Поиск/" + query)) ||
                       (href.match('zero\.yottos\.') && ("http://zero.yottos.com/Zero.aspx?q=" + query)) ||
                       ("http://yottos.com/Search?" + query);
                    break;
                case 'com.ua':
                    link = (href.match('news\.yottos\.') && ("http://news.yottos.com.ua/Поиск?" + query)) ||
                       (href.match('rynok\.yottos\.') && ("http://rynok.yottos.com.ua/поиск/" + query)) ||
                       (href.match('catalog\.yottos\.') && ("http://catalog.yottos.com.ua/yottos-каталог/Поиск/" + query)) ||
                       (href.match('zero\.yottos\.') && ("http://zero.yottos.com.ua/Zero.aspx?q=" + query)) ||
                       ("http://yottos.com.ua/Результат?" + query);
                    break;

                case 'ru':
                default:
                    link = (href.match('news\.yottos\.') && ("http://news.yottos.ru/Поиск?" + query)) ||
                       (href.match('rynok\.yottos\.') && ("http://rynok.yottos.ru/поиск/" + query)) ||
                       (href.match('catalog\.yottos\.') && ("http://catalog.yottos.ru/yottos-каталог/Поиск/" + query)) ||
                       (href.match('zero\.yottos\.') && ("http://zero.yottos.ru/Zero.aspx?q=" + query)) ||
                       ("http://yottos.ru/Результат?" + query);
                    break;
            }
            return query ? link : (link.match(/^http:\/\/[^\/]*\//)[0] || link);           // Если запрос пустой, возвращает ссылку на домен
        }

        sender.href = getSearchUrl(sender.href);
        return true;
    }
</script>
<uc1:LangInstaller ID="LangInstaller1" runat="server" />
