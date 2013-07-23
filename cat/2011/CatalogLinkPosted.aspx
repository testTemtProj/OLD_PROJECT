<%@ Page Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="CatalogLinkPosted.aspx.cs" Inherits="YottosCatalog.CatalogLinkPosted" Culture="ru-RU" UICulture="ru-RU" Title="<%$ Resources:CatalogResources, CatalogTitle %>" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">
    <table style="width:100%;border:0px" align="center">
       <tr>
            <td style="width:100%;height: 31px;" colspan="2">&nbsp;</td>
       </tr>
       <tr>
            <td colspan="2" align="center" style="height: 11px">
                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogLinkPostedResult %>" Font-Bold="True" CssClass="textovkaHeder" /></td>
       </tr>
        <tr>
            <td align="center" colspan="2">
            </td>
        </tr>
       <tr>
            <td style="width:50%;height: 31px;" align="center">
                &nbsp;
                <asp:HyperLink runat="server" NavigateUrl="/" Text="<%$ Resources:CatalogResources, CatalogLinkPostedBackToCatalog %>" CssClass="rubrika" />
            </td>
            <td style="width:50%;height: 31px;" align="center">
                &nbsp;
                <asp:HyperLink runat="server" NavigateUrl="<%$ Resources:CatalogPageUrlsMapping, CatalogAddLink %>" Text="<%$ Resources:CatalogResources, CatalogLinkPostedAddMore %>" CssClass="rubrika" />
            </td>
       </tr>
       <tr>
           <td colspan="2" align="center">
              <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogLinkPotedText %>" CssClass="textovkaHeder" />
              <asp:HyperLink runat="server" NavigateUrl="http://www.yottos.ru/About/Bottons.aspx" Text="<%$ Resources:CatalogResources, CatalogLinkPotedBaners %>" CssClass="rubrika" />
           </td>
       </tr>
       <tr>
            <td style="width:100%;height: 16px; vertical-align:bottom;" colspan="2" align="center">
                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogLinkPotedBanersInfo %>" ForeColor="Silver" Font-Size="10" />            
            </td>
       </tr>
    </table>   
</asp:Content>