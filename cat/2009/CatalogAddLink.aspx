<%@ Page Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="CatalogAddLink.aspx.cs" Inherits="YottosCatalog.CatalogAddLink" Title="<%$ Resources:CatalogResources, CatalogTitle %>" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">
    <asp:ScriptManager runat="server" />
    <table style="width:100%;border:0px">
       <tr>
           <td style="width:30%;" />
           <td style="width:70%;padding-left:10px">
               <b>
                   <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddTitle %>" /></b><br />
               <ul>
                   <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddTitleDescr_0 %>" />
               </ul>
               <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddTitleDescr_1 %>" />
           </td>
       </tr>
       <tr>
            <td align="left" valign="middle" style="width:30%;padding:10px; height: 51px;" />
            <td style="width:70%; height: 51px;"><asp:ValidationSummary ID="ValidationSummary" runat="server" /></td>
       </tr>                     
       <tr>       
           <td colspan="2">       
                <asp:UpdatePanel runat="server" ChildrenAsTriggers="True">
                    <ContentTemplate>              
                       <table style="width:100%;border:0px">       
                           <tr>
                                <td align="right" valign="middle" style="width:30%;padding-left:30px;" >
                                    <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddSelectRootCategory %>" />
                                </td>
                                <td align="left" valign="middle" style="width:70%;">
                                    <asp:LinqDataSource ID="root_categories_DS" runat="server" 
                                        ContextTypeName="YottosCatalog.YottosCatalogDataContext" 
                                        Select="new (name, id)" TableName="root_categories" OrderBy="name">
                                    </asp:LinqDataSource>                
                                    &nbsp;&nbsp;<asp:DropDownList ID="rootCategoriesDropDownList" runat="server" CausesValidation="false" 
                                        Width="300px" CssClass="textovka" AutoPostBack="True"
                                        DataSourceID="root_categories_DS" DataTextField="name" DataValueField="id" 
                                        OnSelectedIndexChanged="rootCategoryList_SelectedIndexChanged" 
                                        OnDataBound="rootCategoryDropDownList_DataBound" />
                                </td>
                           </tr>
                           <tr><td style="width:100%;height: 31px;" colspan="2">&nbsp;</td></tr>
                           <tr>
                                <td align="right" valign="middle" style="width:30%;padding-left:30px;">                                
                                    <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddSelectSubCategory %>" />
                                </td>
                                <td align="center" valign="middle" style="width:70%;"> 
                                    <asp:TreeView ID="SubCategoriesTree" runat="server" ShowLines="True" />
                                    <br />
                                </td>
                           </tr>       
                       </table>       
                    </ContentTemplate>                   
                </asp:UpdatePanel>              
           </td>
       </tr>              
       <tr><td style="width:100%;height: 31px;" colspan="2">&nbsp;</td></tr>
       <tr>
            <td align="right" valign="middle" style="width:30%;padding-left:30px;" >
                <asp:Label ID="URLLabel" runat="server" Text="<%$ Resources:CatalogResources, CatalogAddSiteUrl %>" />
            </td>
            <td align="left" valign="middle" style="width:70%;" class="PStextovka">
                &nbsp;&nbsp;
                <asp:TextBox ID="LinkTextBox" runat="server" Width="650px" Text="http://" MaxLength="100" CssClass="textovka" />
                <asp:RegularExpressionValidator ID="URLRegularExpressionValidator" runat="server" ErrorMessage="<%$ Resources:CatalogResources, CatalogAddURLRegular %>" ValidationExpression="(http(s)?://)?([\w-]+\.)+[\w-]+(/[\w- ./?%&~=#]*)?" ControlToValidate="LinkTextBox" Display="Dynamic">*</asp:RegularExpressionValidator>
                <asp:RequiredFieldValidator ID="URLRequiredFieldValidator" runat="server" ControlToValidate="LinkTextBox" ErrorMessage="<%$ Resources:CatalogResources, CatalogAddURLRequired %>" Display="Dynamic">*</asp:RequiredFieldValidator><br />
                &nbsp;&nbsp;
                <asp:Label ID="URLDescrLabel" runat="server" Text="<%$ Resources:CatalogResources, CatalogAddURLDescr %>" />
            </td>
       </tr>
       <tr><td style="width:100%;height: 31px;" colspan="2">&nbsp;</td></tr>
       <tr>
            <td align="right" valign="middle" style="width:30%;padding-left:30px;" >
                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddSiteName %>" />
            </td>
            <td align="left" valign="middle" style="width:70%;" class="PStextovka">
                &nbsp;&nbsp;
                <asp:TextBox ID="TitleTextBox" runat="server" Width="650px" MaxLength="100" />
                <asp:RequiredFieldValidator ID="TitleRequiredFieldValidator" runat="server" ErrorMessage="<%$ Resources:CatalogResources, CatalogAddTitleRequired %>" ControlToValidate="TitleTextBox" Display="Dynamic">*</asp:RequiredFieldValidator><br />
                &nbsp;&nbsp;
                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddNameDescr %>" />
            </td>
       </tr>
       <tr><td style="width:100%;height: 31px;" colspan="2">&nbsp;</td></tr>
       <tr>
            <td align="right" valign="middle" style="width:30%;padding-left:30px; height: 109px;">            
                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddAbout %>" />
            </td>
            <td align="left" valign="middle" style="width:70%;height: 109px;" class="PStextovka">
		        &nbsp;&nbsp;
		        <asp:TextBox ID="AboutTextBox" runat="server" Height="106px" TextMode="MultiLine" Width="650px" MaxLength="1000" CssClass="textovka" />                
                <asp:RequiredFieldValidator ID="AboutRequiredFieldValidator" runat="server" ErrorMessage="<%$ Resources:CatalogResources, CatalogAddAboutRequired %>" ControlToValidate="AboutTextBox" Display="Dynamic">*</asp:RequiredFieldValidator><br />
                &nbsp;&nbsp;
                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddAboutDescr %>" />
            </td>
       </tr>
       <tr><td style="width:100%;height: 31px;" colspan="2">&nbsp;</td></tr>
       <tr>
            <td align="right" valign="middle" style="width:30%;padding-left:30px;">
            <asp:Label runat="server" Text="<%$ Resources:CatalogResources, CatalogAddEmail %>" /></td>
            <td align="left" valign="middle" style="width:70%;"> 
                &nbsp;&nbsp;
                <asp:TextBox ID="EmailTextBox" runat="server" Width="300px" MaxLength="100" CssClass="textovka"></asp:TextBox>
                <asp:RegularExpressionValidator ID="EmailRegularExpressionValidator" runat="server" ErrorMessage="<%$ Resources:CatalogResources, CatalogAddEmailRegular %>" ValidationExpression="\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*" ControlToValidate="EmailTextBox" Display="Dynamic">*</asp:RegularExpressionValidator>
                <asp:RequiredFieldValidator ID="EmailRequiredFieldValidator" runat="server" ControlToValidate="EmailTextBox" ErrorMessage="<%$ Resources:CatalogResources, CatalogAddEmailRequired %>" Display="Dynamic">*</asp:RequiredFieldValidator>
            </td>
       </tr>
       <tr><td style="width:100%;height: 31px;" colspan="2">&nbsp;</td></tr>
       <tr>
            <td style="width:100%;height: 31px;" colspan="2">
                <div style="vertical-align:bottom ; text-align:center ; " >
                    <asp:Label ID="SecretWordLabel" runat="server" Text="<%$ Resources:CatalogResources, CatalogAddSecretWord %>" CssClass="textovka" />
                    <br/>
                    <asp:TextBox ID="SecretWordTextBox" runat="server" ReadOnly="false" Width="100px" CssClass="textovka" />
                    <asp:CustomValidator ID="AutoCustomValidator" runat="server" Display="Dynamic" ErrorMessage="<%$ Resources:CatalogResources, CatalogAddAutoCustom %>">*</asp:CustomValidator>
                    <asp:Image ID="NumImage" runat="server" ImageUrl="~/Handlers/CheckImageHandler.ashx" />
                </div>                
            </td>
       </tr>
       <tr><td style="width:100%;height: 31px;" colspan="2">&nbsp;</td></tr>
       <tr>
            <td colspan="2" style="width:100%; height: 20px;">
                <center>
                    <asp:Button ID="addButton" runat="server" Text="<%$ Resources:CatalogResources, CatalogAddButtonText %>" OnClick="AddButton_Click" />
                 </center>
            </td>           
       </tr>
   </table>
</asp:Content>