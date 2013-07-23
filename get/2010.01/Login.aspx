<%@ Page Language="C#" AutoEventWireup="true" CodeBehind="Login.aspx.cs" Inherits="GetMyAd.Login" MasterPageFile="~/Default.Master" StyleSheetTheme="Theme1" %>

<asp:Content ID="Content" ContentPlaceHolderID="ContentPlaceHolder" Runat="Server">

    <table>
<tr>
<td style="width: 100%; vertical-align: top; padding-left: 138px;">

<div style="width: 600px">
<h2>Для вебмастеров, желающих заработать: </h2>

<ul>
<li> зарабатывайте на своём сайте, размещая на своих страницах товарные предложения с помощью программы <b>GetMyAd</b> и
    <b>получайте деньги за клики</b> совершаемые вашими пользователями по каждому предложению!
</li>
<li>Настраивайте предложения под дизайн своего сайта.</li>
</ul>
</div>


<br />




<asp:Image ImageUrl="~/Image/example.jpg"  ID="ExampleImage" runat="server"/>

</td>
<td style="vertical-align: top">
<div style="height: 170px;  width: 100%; margin-right: 20px;">
    <asp:Login ID="Login1" runat="server" 
        FailureText="Неверный логин или пароль. Попробуйте ещё раз." 
        LoginButtonText="Вход" onauthenticate="Login1_Authenticate" 
        PasswordLabelText="Пароль&amp;nbsp;&amp;nbsp;&amp;nbsp;" PasswordRequiredErrorMessage="Введите пароль!" 
        RememberMeText="Запомнить меня" TitleText="Вход в GetMyAd" 
        UserNameLabelText="Логин&amp;nbsp;&amp;nbsp;&amp;nbsp;" UserNameRequiredErrorMessage="Введите логин!" 
        Width="267px" BorderColor="#B5C7DE" BorderPadding="4" BorderWidth="1px" 
        BackColor="#EFF3FB" BorderStyle="Solid" 
        ForeColor="#333333">
        <TextBoxStyle Width="200px" />
        <LoginButtonStyle CssClass="forButton" />
        <InstructionTextStyle Font-Italic="True" ForeColor="Black" />
        <LabelStyle CssClass="LoginLabel" />
        <TitleTextStyle BackColor="#0099FF" CssClass="LoginTitle" Font-Bold="True" 
            Font-Size="1.2em" ForeColor="White" />
    </asp:Login>
</div>

<div style="text-align: left; width: 100%; margin-left: 10px;">
    <p style="color: #33f; font-weight: bold; font-size: larger; text-align: center; width: 250px;">Как начать зарабатывать?</p>
    <asp:HyperLink ID="RegisterHyperLink" NavigateUrl="~/Регистрация" runat="server">
        <img src="Image/RegisterButton.gif" border="0" alt="Стать участником!"/>
    </asp:HyperLink>
    <p>Добавьте Ваш сайт в рекламную сеть Yottos!</p>
</div>


</td>
</tr>
</table>

</asp:Content>
