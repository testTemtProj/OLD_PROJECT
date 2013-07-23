<%@ Page Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="CatalogSearch.aspx.cs" Inherits="YottosCatalog.CatalogSearch" Title="<%$ Resources:CatalogResources, SearchTitle %>" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<script runat="server">

    protected void searchResult_SelectedIndexChanged(object sender, EventArgs e)
    {

    }
</script>
<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">
    <asp:Substitution runat="server" />
    <asp:ObjectDataSource ID="links_DS" runat="server" 
        SelectMethod="SearchLinks" TypeName="YottosCatalog.YottosCatalogDataContext">
        <SelectParameters>
            <asp:QueryStringParameter DefaultValue="yottos" Name="searchText" QueryStringField="q" Type="String" />
            <asp:QueryStringParameter DefaultValue="0" Name="category" QueryStringField="category" Type="String" />
        </SelectParameters>
    </asp:ObjectDataSource>    
    <div style="padding: 10px;">                                       
        <asp:ListView ID="searchResult" runat="server" DataSourceID="links_DS" 
            onselectedindexchanged="searchResult_SelectedIndexChanged">
            <ItemTemplate>
                <asp:Table runat="server" BorderWidth="0" CellPadding="0" CellSpacing="0" Width="100%">
                    <asp:TableRow>
                        <asp:TableCell Width="100%">
                            <asp:HyperLink runat="server" CssClass="catalogTitle" NavigateUrl='<%# Eval("id", "/Handlers/LinkClickHandler.ashx?id={0}&")+Eval("sub_category_id", "cat={0}&showname=1") %>' Target="_blank" Text='<%# Eval("caption") %>' />
                        </asp:TableCell></asp:TableRow><asp:TableRow>
                        <asp:TableCell Width="90%" Height="19px">
                            <asp:Label runat="server" CssClass="catalogDescription" Font-Names="Arial" Font-Size="11pt" Text='<%# Eval("link_description") %>' />
                        </asp:TableCell></asp:TableRow><asp:TableRow>
                        <asp:TableCell Width="90%" Height="19px">
                            <asp:HyperLink runat="server" CssClass="catalogUrl" ForeColor="Green" NavigateUrl='<%# Eval("id", "/Handlers/LinkClickHandler.ashx?id={0}&")+Eval("sub_category_id", "cat={0}") %>' Target="_blank" Text='<%# Eval("url") %>' />
                            &nbsp;
                            <asp:HyperLink Visible='<%# ShowSubCategory %>' runat="server" CssClass="catalogTitle" NavigateUrl='<%# Eval("sub_category_id", "CatalogContents.aspx?id={0}") %>' Target="_blank" Text='<%# Eval("sub_category") %>' ForeColor="Silver" />
                        </asp:TableCell></asp:TableRow></asp:Table><br />
            </ItemTemplate>
            <LayoutTemplate>
                <div id="itemPlaceholderContainer" runat="server" width="100%" style="padding: 10px;">
                    <span ID="itemPlaceholder" runat="server" width="100%" />                                            
                </div>
                <br />
                <div align="center">
                    <asp:DataPager runat="server" OnLoad="Pager_Load">
                        <Fields>                                                    
                            <asp:NextPreviousPagerField ButtonType="Image" ShowFirstPageButton="False" 
                                ShowNextPageButton="False" ShowPreviousPageButton="True"                                         
                                PreviousPageImageUrl="~/Image/Arrow-Left.gif" />
                            <asp:NumericPagerField ButtonType="Link" NumericButtonCssClass="q" NextPageText="" PreviousPageText="" ButtonCount="10" />
                            <asp:NextPreviousPagerField ButtonType="Image" ShowLastPageButton="False" 
                                ShowNextPageButton="True" ShowPreviousPageButton="False"  
                                NextPageImageUrl="~/Image/Arrow-Right.gif" />
                        </Fields>                                            
                    </asp:DataPager> 
                </div>                                                                       
            </LayoutTemplate>
            <EmptyDataTemplate>
                <asp:Label runat="server" OnLoad="NoResults_Load" /> 
            </EmptyDataTemplate>
        </asp:ListView>                                     
    </div>  
</asp:Content>
