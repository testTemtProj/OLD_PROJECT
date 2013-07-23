<%@ Page Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="CatalogList.aspx.cs" Inherits="YottosCatalog.CatalogList" Title="<%$ Resources:CatalogResources, CatalogTitle %>" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">    
    <div style="width: 100%; padding-left: 10px;">
        <asp:LinqDataSource ID="root_categories_DS" runat="server" ContextTypeName="YottosCatalog.YottosCatalogDataContext"
            OrderBy="name" Select="new (name, id, FirstThreeSubCategories)" 
            TableName="root_categories">
        </asp:LinqDataSource>
        <asp:ListView runat="server" DataSourceID="root_categories_DS" GroupItemCount="2">
            <ItemTemplate>
                <td valign="top">
                    <asp:HyperLink runat="server" NavigateUrl='<%# Eval("id", "/CatalogDetails.aspx?id={0}") %>' CssClass="rubrika" Text='<%# Eval("name") %>' />
                    <br />
                    <div style="margin-right: 5px;">
                        <asp:DataList GridLines="Both" RepeatLayout="Flow" runat="server" DataKeyField="id" DataSource='<%# Eval("FirstThreeSubCategories") %>' RepeatDirection="Horizontal">
                            <ItemTemplate>
                                <asp:HyperLink runat="server" NavigateUrl='<%# Eval("id", "/CatalogContents.aspx?id={0}") %>' CssClass="razdel" Text='<%# Eval("name") %>' />
                            </ItemTemplate>
                            <SeparatorTemplate>,&nbsp;</SeparatorTemplate>
                        </asp:DataList>,                    
                        <asp:HyperLink runat="server" NavigateUrl='<%# Eval("id", "/CatalogDetails.aspx?id={0}") %>' CssClass="razdel" Text="..." />                    
                    </div>         
                    <br /><br />
                </td>
            </ItemTemplate>
            <LayoutTemplate>
                <table id="groupPlaceholderContainer" runat="server" width="100%">
                    <tr id="groupPlaceholder" runat="server" />
                </table>
            </LayoutTemplate>
            <GroupTemplate>
                <tr id="itemPlaceholderContainer" runat="server">
                    <td id="itemPlaceholder" runat="server" />
                </tr>
            </GroupTemplate>
        </asp:ListView>
    </div>
    <table width="100%" border="0" cellspacing="0" cellpadding="0">
        <tr>
            <td style="border-top: 0px; border-left: #4c6bdf 1px solid; height: 12px; font-size: 2px;">
                &nbsp;
            </td>
        </tr>
    </table>
</asp:Content>
