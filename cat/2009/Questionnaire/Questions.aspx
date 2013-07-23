<%@ Page Title="<%$ Resources:CatalogResources, QuestionsPageTitle %>" Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="Questions.aspx.cs" Inherits="YottosCatalog.Questionnaire.Questions" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<%@ Register TagPrefix="questionnaire" TagName="AnswerControl" Src="~/Controls/QuestionnaireAnswer.ascx"%>

<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">
    <asp:ScriptManager runat="server" />
    <p align="center">        
        <asp:Localize runat="server" Text="<%$ Resources:CatalogResources, QuestionsMainTitle %>" />
    </p>    
    <br />
    <table width="100%">
        <tr>
            <td align="right" valign="middle" width="30%"> 
                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, QuestionsProfession %>" />
            </td>
            <td align="left" valign="middle" width="70%" class="PStextovka"> 
                &nbsp;&nbsp;
                <asp:TextBox ID="prof" runat="server" Width="650px" MaxLength="100" />
                <asp:RequiredFieldValidator ID="profRequiredFieldValidator" runat="server" ErrorMessage="заполните поле!" ControlToValidate="prof" Display="Dynamic">*</asp:RequiredFieldValidator><br />
                &nbsp;&nbsp;
            </td>
        </tr>
        <tr>
            <td colspan="2" align="center">
                <br />
                <b><asp:Localize runat="server" Text="<%$ Resources:CatalogResources, QuestionsFill %>" /></b>
            </td>
        </tr>        
        <tr>
            <td align="right" valign="middle" width="30%"> 
                <asp:Localize runat="server" Text="<%$ Resources:CatalogResources, QuestionsGiveQuestion %>" />                
            </td>
            <td align="left" valign="middle" width="70%" class="PStextovka"> 
                &nbsp;&nbsp; 
                <asp:TextBox ID="question" runat="server" Width="650px" MaxLength="100" />
                <asp:RequiredFieldValidator ID="questionRequiredFieldValidator" runat="server" ErrorMessage="заполните поле!" ControlToValidate="question" Display="Dynamic">*</asp:RequiredFieldValidator><br />         
                &nbsp;&nbsp; 
                <asp:Localize runat="server" Text="<%$ Resources:CatalogResources, QuestionsGiveAnswersHint %>" />                
            </td>
        </tr>
        <tr>
            <td colspan="2" align="center">
                <br/>
                <h4>
                    <asp:Localize runat="server" Text="<%$ Resources:CatalogResources, QuestionsGiveAnswers %>" />                
                </h4>
            </td>
        </tr>
    </table>
    
    <hr />
    
    <asp:UpdatePanel ID="answersPanel" runat="server">
        <ContentTemplate>       
            <questionnaire:AnswerControl ID="answer_1" runat="server" 
                AnswerCaption="<%$ Resources:CatalogResources, QuestionsAnswerCaption_1 %>" 
                IsAnswerRequired="true"
                AnswerErrorMessage="<%$ Resources:CatalogResources, QuestionsAnswerErrorMessage %>"
                AnswerHint="<%$ Resources:CatalogResources, QuestionsGiveAnswersHint %>"
                AnswerLinkCaption="<%$ Resources:CatalogResources, QuestionsAnswerLinkCaption %>"
                AnswerImageCaption="<%$ Resources:CatalogResources, QuestionsAnswerImageCaption %>" />                       
                                                
            <questionnaire:AnswerControl ID="answer_2" runat="server" 
                AnswerCaption="<%$ Resources:CatalogResources, QuestionsAnswerCaption_2 %>" 
                IsAnswerRequired="false"
                AnswerErrorMessage="<%$ Resources:CatalogResources, QuestionsAnswerErrorMessage %>"
                AnswerHint="<%$ Resources:CatalogResources, QuestionsGiveAnswersHint %>"
                AnswerLinkCaption="<%$ Resources:CatalogResources, QuestionsAnswerLinkCaption %>"
                AnswerImageCaption="<%$ Resources:CatalogResources, QuestionsAnswerImageCaption %>" />
            
            <questionnaire:AnswerControl ID="answer_3" runat="server" 
                AnswerCaption="<%$ Resources:CatalogResources, QuestionsAnswerCaption_3 %>" 
                IsAnswerRequired="false"
                AnswerErrorMessage="<%$ Resources:CatalogResources, QuestionsAnswerErrorMessage %>"
                AnswerHint="<%$ Resources:CatalogResources, QuestionsGiveAnswersHint %>"
                AnswerLinkCaption="<%$ Resources:CatalogResources, QuestionsAnswerLinkCaption %>"
                AnswerImageCaption="<%$ Resources:CatalogResources, QuestionsAnswerImageCaption %>" />          
            
            <questionnaire:AnswerControl ID="answer_4" runat="server" Visible="false" 
                AnswerCaption="<%$ Resources:CatalogResources, QuestionsAnswerCaption_4 %>" 
                IsAnswerRequired="false"
                AnswerErrorMessage="<%$ Resources:CatalogResources, QuestionsAnswerErrorMessage %>"
                AnswerHint="<%$ Resources:CatalogResources, QuestionsGiveAnswersHint %>"
                AnswerLinkCaption="<%$ Resources:CatalogResources, QuestionsAnswerLinkCaption %>"
                AnswerImageCaption="<%$ Resources:CatalogResources, QuestionsAnswerImageCaption %>" />         
            
            <questionnaire:AnswerControl ID="answer_5" runat="server" Visible="false" 
                AnswerCaption="<%$ Resources:CatalogResources, QuestionsAnswerCaption_5 %>" 
                IsAnswerRequired="false"
                AnswerErrorMessage="<%$ Resources:CatalogResources, QuestionsAnswerErrorMessage %>"
                AnswerHint="<%$ Resources:CatalogResources, QuestionsGiveAnswersHint %>"
                AnswerLinkCaption="<%$ Resources:CatalogResources, QuestionsAnswerLinkCaption %>"
                AnswerImageCaption="<%$ Resources:CatalogResources, QuestionsAnswerImageCaption %>" />          
            
            <questionnaire:AnswerControl ID="answer_6" runat="server" Visible="false" 
                AnswerCaption="<%$ Resources:CatalogResources, QuestionsAnswerCaption_6 %>" 
                IsAnswerRequired="false"
                AnswerErrorMessage="<%$ Resources:CatalogResources, QuestionsAnswerErrorMessage %>"
                AnswerHint="<%$ Resources:CatalogResources, QuestionsGiveAnswersHint %>"
                AnswerLinkCaption="<%$ Resources:CatalogResources, QuestionsAnswerLinkCaption %>"
                AnswerImageCaption="<%$ Resources:CatalogResources, QuestionsAnswerImageCaption %>" />                   
            
            <div align="center">
                <asp:Button ID="addAnswer" runat="server" Text="<%$ Resources:CatalogResources, QuestionsAddAnswer %>" OnClick="AdditionalAnswer_Click" CausesValidation="false" />
            </div>        
        </ContentTemplate>
    </asp:UpdatePanel>                   
                   
    <p>
        <asp:Localize runat="server" Text="<%$ Resources:CatalogResources, QuestionsOwnerHint %>" />        
    </p>
    <br />
    <div align="center"><asp:Button ID="finish" runat="server" Text="<%$ Resources:CatalogResources, QuestionsFinish %>" OnClick="finish_Click" /></div>    
</asp:Content>