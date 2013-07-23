<%@ Register TagPrefix="cc1" Namespace="WebControlCaptcha" Assembly="WebControlCaptcha" %>
<%@ Page Title="" Language="C#" MasterPageFile="~/Default.Master" AutoEventWireup="true" CodeFile="Register.aspx.cs" Inherits="Register" StylesheetTheme="Theme1" Theme="Theme1" EnableSessionState="True" %>

<asp:Content ID="Content1" ContentPlaceHolderID="head" Runat="Server" >
</asp:Content>
<asp:Content ID="Content2" ContentPlaceHolderID="ContentPlaceHolder" Runat="Server" EnableViewState="false">


<script type="text/javascript">
    function agreeClicked(obj) {
       document.getElementById('<%=SubmitButton.ClientID%>').disabled = !obj.checked;
   }
    
</script>


<asp:Panel ID="PanelMain" runat="server" Visible="true">
<div style="padding-left: 100px">
<h2>Добро пожаловать в программу GetMyAd! </h2>
<p> Заполните, пожалуйста, требуемые данные, ваша заявка будет расмотрена в течении 3 дней. </p>

<table cellpadding="6">

<tr>
    <td>Ваше имя*: </td>
    <td><asp:TextBox ID="UserNameText" runat="server" Width="200px" />
    <asp:RequiredFieldValidator runat="server" id="reqUserName" ControlToValidate="UserNameText" Text="*" ErrorMessage="Введите Ваше имя!" />
    </td>
</tr>
<tr>
    <td>URL главной страницы  сайта*:</td>
    <td><asp:TextBox ID="SiteUrl" runat="server" Width="300px" />
    <asp:RequiredFieldValidator runat="server" id="reqUrl" ControlToValidate="SiteUrl" Text="*" ErrorMessage="Введите Url страницы сайта!" />
    </td>
</tr>    
<tr>
    <td>Номер телефона*: <br />(<i style="color: #777;">+380 (44) 123-45-67</i>) </td>
    <td><asp:TextBox ID="PhoneNumber" runat="server" Width="200px" />
    <asp:RequiredFieldValidator runat="server" id="reqPhoneNumber" ControlToValidate="PhoneNumber" Text="*" ErrorMessage="Введите номер телефона!" />
    </td>
</tr>
<tr>
    <td>Эл. почта*: </td>
    <td><asp:TextBox ID="Email" runat="server" Width="200px" />
    <asp:RegularExpressionValidator runat="server" id="reqEmail" ControlToValidate="Email" ValidationExpression=".*@.*\..*" Text="*" ErrorMessage="Введите адрес электронной почты!" />
    </td>
</tr>
<tr>
    <td>Введите символы*:</td>
    <td><cc1:captchacontrol id="CaptchaControl1" runat="server"  CaptchaLineNoise="High"
            CacheStrategy="HttpRuntime" Text="" onprerender="CaptchaControl1_PreRender" ></cc1:captchacontrol>
    </td>
</tr>
<tr>
<td colspan="2">
    <asp:CheckBox ID="AgreeCheckBox" runat="server" onclick="agreeClicked(this);" Text="Я ознакомлен и согласен с <a href='http://getmyad.yottos.com/Правила_программы_Yottos_GetMyAd' target='_blank'>Правилами программы GetMyAd</a>."   />
</td>
</tr>

<tr>
<td colspan="2">
        <asp:ValidationSummary ID="ValidationSummary1" runat="server"  />
</td>
</tr>

<tr>
<td colspan="2">
<br /><p style="text-align: center;"><asp:Button ID="SubmitButton" runat="server" 
            Text="Отправить" Height="3em" Width="200px" Enabled="false"
            onclick="SubmitButton_Click" /></p>
</td>
</tr>

</table>
</div>
</asp:Panel>



<asp:Panel ID="PanelThankYou" runat="server" Visible="false">
<div style="padding-left: 100px">
<h2>Заявка на регистрацию успешно принята!</h2>
<p>Благодарим Вас за регистрацию! Ваша заявка была успешно принята и будет рассмотрена модераторами в ближайшее время. </p>
<p><asp:HyperLink ID="HyperLinkBack" NavigateUrl="~" Text="Вернуться на главную" runat="server" /> </p>
</div> 
</asp:Panel>




</asp:Content>

