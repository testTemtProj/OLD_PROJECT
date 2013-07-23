<%@ Page Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="About.aspx.cs" Inherits="YottosCatalog.About" Title="<%$ Resources:CatalogResources, CatalogTitle %>" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">
    <table border="0" cellspacing="0" cellpadding="0" width="100%" style="border-bottom:0;">
        <tr>
            <td style="padding:30px;">
                <p style="text-align:justify">
                    <asp:Label runat="server" Text="<%$ Resources:CatalogResources, AboutCatalogDescription_0 %>" />
                    <asp:HyperLink ID="AddLinkToCatalogHyperLink" runat="server" NavigateUrl="CatalogAddLink.aspx" Target="_self" Text="<%$ Resources:CatalogResources, CatalogAddLinkCaption %>" />
                </p>
                <p style="text-align:justify">
                    <asp:Label runat="server" Text="<%$ Resources:CatalogResources, AboutCatalogDescription_1 %>" />
                    <asp:HyperLink ID="ContactHyperLink" runat="server" NavigateUrl="~/SendMail.aspx" Text="<%$ Resources:CatalogResources, ContactLinkCaption %>" />.
                    <asp:Label runat="server" Text="<%$ Resources:CatalogResources, AboutCatalogDescription_2 %>" />
                </p>
            </td>
         </tr>
     </table>
</asp:Content>
