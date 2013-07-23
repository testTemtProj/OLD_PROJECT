<%@ Page Language="C#" AutoEventWireup="true" Title="yottos catalog sitemap generator" CodeBehind="SitemapGenerator.aspx.cs" Inherits="YottosCatalog.SitemapGenerator" %>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
<head runat="server" />
<body>
    <form runat="server">
        <table align="center">
            <tr>
                <td>локаль: </td>
                <td>
                    <asp:XmlDataSource ID="supportedCultures_DS" runat="server" DataFile="~/App_Data/SupportedCultures.xml" />
                    <asp:DropDownList ID="culturesList" runat="server" Width="200px" 
                        DataSourceID="supportedCultures_DS" 
                        DataTextField="natine_name" DataValueField="lcid" />                 
                </td>                
            </tr>               
            <tr>
                <td colspan="2" align="center">
                    <asp:Button runat="server" Text="генерировать" onclick="Generate_Click" />
                </td>
            </tr>
            <tr>
                <td colspan="2" align="center">
                    <asp:Label ID="statusLabel" runat="server" />
                </td>
            </tr>        
        </table>   
    </form>
</body>
</html>
