<%@ Page Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="CatalogDetails.aspx.cs" Inherits="YottosCatalog.CatalogDetails" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">
    <div style="width:100%; padding-left:10px;">
      <div style="padding-bottom:10px;">
          <table runat="server">
              <tr>
                  <td style="vertical-align: top; text-align: left">
                      <asp:HyperLink runat="server" CssClass="rubrika" Text="<%$ Resources:CatalogResources, ToCatalogListLinkCaption %>" NavigateUrl="/" />               
                  </td>
                  <td style="vertical-align: top; text-align: left">
                      &nbsp;/&nbsp;
                      <asp:Label ID="TitleLabel" runat="server" CssClass="rubrikCurentTitle" />
                  </td>
              </tr>
          </table>         
      </div>   
      <asp:ObjectDataSource ID="sub_categories_DS" runat="server" 
            SelectMethod="GetSubcategoriesRoots" 
            TypeName="YottosCatalog.YottosCatalogDataContext">
          <SelectParameters>
              <asp:QueryStringParameter ConvertEmptyStringToNull="False" DefaultValue="1" Name="rootCategoryId" QueryStringField="id" Type="Int32" />
          </SelectParameters>
      </asp:ObjectDataSource>      
      <asp:ListView runat="server" DataSourceID="sub_categories_DS" GroupItemCount="2">
          <ItemTemplate>
              <td runat="server" style="" width="50%">  
                <div style="padding-bottom:10px;">
                    <asp:HyperLink runat="server" NavigateUrl='<%# Eval("id", "/CatalogContents.aspx?id={0}") %>' CssClass="rubrika" Text='<%# Eval("name") %>' />
                </div>
              </td>
          </ItemTemplate>
          <LayoutTemplate>                                        
              <table ID="groupPlaceholderContainer" runat="server" width="100%">
                  <tr ID="groupPlaceholder" runat="server" />
              </table>                 
          </LayoutTemplate>              
          <GroupTemplate>
              <tr ID="itemPlaceholderContainer" runat="server">
                  <td ID="itemPlaceholder" runat="server" />
              </tr>
          </GroupTemplate>           
      </asp:ListView>      
    </div>
</asp:Content>