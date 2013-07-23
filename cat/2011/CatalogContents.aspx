<%@ Page Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="CatalogContents.aspx.cs" Inherits="YottosCatalog.CatalogContents" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">
    <div style="width: 100%; padding-left: 10px;">
        <div style="padding-bottom: 10px;">
            <asp:SiteMapPath ID="CatalogMapPath" runat="server" RenderCurrentNodeAsLink="False">
                <NodeTemplate>
                    <asp:HyperLink runat="server" CssClass="rubrika" Text='<%# Eval("Title") %>' NavigateUrl='<%# Eval("Url") %>' />
                </NodeTemplate>
                <CurrentNodeTemplate>
                    <asp:Label runat="server" CssClass="rubrikCurentTitle" Text='<%# Eval("Title") %>' />
                </CurrentNodeTemplate>
                <PathSeparatorTemplate>&nbsp;/&nbsp;</PathSeparatorTemplate>
            </asp:SiteMapPath>
        </div>
        <asp:ObjectDataSource ID="nested_sub_categories_DS" runat="server" SelectMethod="GetNestedCategories"
            TypeName="YottosCatalog.YottosCatalogDataContext">
            <SelectParameters>
                <asp:QueryStringParameter DefaultValue="1" Name="rootSubCategoryId" QueryStringField="id"
                    Type="Int32" />
            </SelectParameters>
        </asp:ObjectDataSource>
        <asp:ListView runat="server" DataSourceID="nested_sub_categories_DS" GroupItemCount="2">
            <ItemTemplate>
                <td runat="server" style="" width="50%">
                    <div style="padding-bottom: 10px;">
                        <asp:HyperLink runat="server" NavigateUrl='<%# Eval("id", "/CatalogContents.aspx?id={0}") %>' CssClass="rubrika" Text='<%# Eval("name") %>' />
                    </div>
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
        <asp:LinqDataSource ID="links_DS" runat="server" ContextTypeName="YottosCatalog.YottosCatalogDataContext"
            OrderBy="link_counter desc" Select="new (id, url, caption, link_description, sub_category_id, link_counter)"
            TableName="links" Where="sub_category_id == @sub_category_id &amp;&amp; is_accepted == @is_accepted">
            <WhereParameters>
                <asp:QueryStringParameter DefaultValue="1" Name="sub_category_id" QueryStringField="id"
                    Type="Int32" />
                <asp:Parameter DefaultValue="True" Name="is_accepted" Type="Boolean" />
            </WhereParameters>
        </asp:LinqDataSource>
        <div>
            <table border="0" cellspacing="0" cellpadding="0" width="100%" style="table-layout: fixed">
                <tr>
                    <td>
                        <div style="padding: 10px;">
                            <asp:ListView ID="links_ListView" runat="server" DataSourceID="links_DS">
                                <ItemTemplate>
                                    <table border="0" cellspacing="0" cellpadding="0" width="100%">
                                        <tr>
                                            <td style="width:100%;">                                
                                                <asp:HyperLink runat="server" CssClass="catalogTitle" NavigateUrl='<%# Eval("id", "/Handlers/LinkClickHandler.ashx?id={0}&")+Eval("sub_category_id", "cat={0}&showname=1") %>' Target="_blank" Text='<%# Eval("caption") %>' />
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="width: 90%; height: 19px;">
                                                <asp:Label runat="server" CssClass="catalogDescription" Font-Names="Arial" Font-Size="11pt" Text='<%# Eval("link_description") %>' />
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="width: 90%; height: 19px;">
                                                <asp:HyperLink runat="server" CssClass="catalogUrl" ForeColor="Green" NavigateUrl='<%# Eval("id", "/Handlers/LinkClickHandler.ashx?id={0}&")+Eval("sub_category_id", "cat={0}") %>' Target="_blank" Text='<%# Eval("url") %>' />                                                
                                            </td>
                                        </tr>
                                    </table>
                                    <br />
                                </ItemTemplate>
                                <LayoutTemplate>
                                    <div id="itemPlaceholderContainer" runat="server">
                                        <span ID="itemPlaceholder" runat="server" />                                            
                                    </div>
                                    <br />
                                    <div align="center">
                                        <asp:DataPager runat="server" OnLoad="Pager_Load">
                                            <Fields>                                                    
                                                <asp:NextPreviousPagerField ButtonType="Image" ShowFirstPageButton="False" 
                                                    ShowNextPageButton="False" ShowPreviousPageButton="True"                                         
                                                    PreviousPageImageUrl="/Image/Arrow-Left.gif" />
                                                <asp:NumericPagerField ButtonType="Link" NumericButtonCssClass="q" NextPageText="" PreviousPageText="" ButtonCount="10" />
                                                <asp:NextPreviousPagerField ButtonType="Image" ShowLastPageButton="False" 
                                                    ShowNextPageButton="True" ShowPreviousPageButton="False"  
                                                    NextPageImageUrl="/Image/Arrow-Right.gif" />
                                            </Fields>                                            
                                        </asp:DataPager> 
                                    </div>                                                                       
                                </LayoutTemplate>
                            </asp:ListView>                                                        
                        </div>
                    </td>
                </tr>           
            </table>
        </div>
    </div>          
</asp:Content>
