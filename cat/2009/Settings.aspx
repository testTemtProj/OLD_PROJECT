<%@ Page Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="Settings.aspx.cs" Inherits="YottosCatalog.Settings" Title="<%$ Resources:CatalogResources, SettingsTitle %>" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">
    <div>         
        <table style="width: 100%; text-align: left" align="center" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td>
                    <table style="width: 100%; text-align: left" align="center" border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td style="width: 30%; height: 31px;"> &nbsp; </td>
                            <td style="width: 70%; height: 31px;">
                                &nbsp;
                                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, SettingsTitleCaption %>" Font-Bold="True" />
                                <br />
                                <br />
                                <asp:Localize runat="server" Text="<%$ Resources:CatalogResources, SettingsDescriptionCaption %>" />
                            </td>
                        </tr>
                        <tr>
                            <td style="width: 100%; height: 31px;" colspan="2">&nbsp;</td>
                        </tr>
                        <tr>
                            <td align="right" valign="bottom" style="width: 30%; height: 31px;">
                                <br />
                                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, SettingsLanguageCaption %>" CssClass="textovka" />
                                &nbsp;&nbsp;
                            </td>
                            <td align="left" valign="bottom" style="width: 70%; height: 31px;">
                                <asp:XmlDataSource ID="supportedCultures_DS" runat="server" DataFile="~/App_Data/SupportedCultures.xml" />
                                <asp:DropDownList ID="culturesList" runat="server" Width="200px" 
                                    CssClass="textovka" DataSourceID="supportedCultures_DS" 
                                    DataTextField="natine_name" DataValueField="name" 
                                    ondatabound="culturesList_DataBound" />
                                <asp:Button ID="Transfer" runat="server" Text="<%$ Resources:CatalogResources, SettingsTransferButtonCaption %>" onclick="Transfer_Click" />
                            </td>
                        </tr>
                        <tr>
                            <td style="width: 100%; height: 31px;" colspan="2">&nbsp;</td>
                        </tr>
                        <tr>
                            <td align="right" valign="bottom" style="width: 30%; height: 31px; vertical-align: bottom;">
                                <br />
                                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, SettingsPageSizeCaption%>"/>
                                &nbsp;&nbsp;
                            </td>
                            <td align="left" valign="bottom" style="width: 70%; height: 31px;">                                
                                <asp:DropDownList ID="pageSizeDropDown" runat="server" Width="60px" Font-Size="12pt">
                                    <asp:ListItem>10</asp:ListItem>
                                    <asp:ListItem>20</asp:ListItem>
                                    <asp:ListItem>30</asp:ListItem>
                                    <asp:ListItem>50</asp:ListItem>
                                </asp:DropDownList>
                                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, SettingsOnThePageCaption%>" />
                            </td>
                        </tr>
                        <tr>
                            <td style="width: 100%; height: 25px;" colspan="2">&nbsp;</td>
                        </tr>
                    </table>
                    <br />
                    <table style="width: 100%;" border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td align="left" valign="middle" style="width: 50%; height: 31px; padding-left: 30px;">                            
                                <asp:Label ID="SaveLabel" runat="server" Text="<%$ Resources:CatalogResources, SettingsSaveAndReturnCaption%>" CssClass="textovka" />
                            </td>
                            <td align="left" valign="middle" style="width: 50%; height: 31px;">
                                <asp:Button ID="Save" runat="server" Text="<%$ Resources:CatalogResources, SettingsSaveButtonCaption %>" Width="200px" OnClick="Save_Click" />
                            </td>
                        </tr>
                    </table>
                </td>
                <td style="width: 240px; height: 18px;">&nbsp;</td>
            </tr>
        </table>
        <br />
    </div>
</asp:Content>
