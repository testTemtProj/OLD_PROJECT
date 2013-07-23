<%@ Page Title="<%$ Resources:CatalogResources, QuestionsPageTitle %>" Language="C#" MasterPageFile="~/Catalog.Master" AutoEventWireup="true" CodeBehind="Result.aspx.cs" Inherits="YottosCatalog.Questionnaire.Result" %>
<%@ MasterType VirtualPath="~/Catalog.Master" %>
<asp:Content ContentPlaceHolderID="ContentPlaceHolder" runat="server">    
    <asp:ListView ID="question_List" runat="server" DataKeyNames="id">
        <ItemTemplate>            
            <div align="center">
                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, QuestionsProfession %>" ForeColor="Silver" />            
            </div>
            <div align="center">
                <asp:Label runat="server" Text='<%# Eval("profession") %>' />
            </div>
            
            <div align="center">
                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, QuestionsGiveQuestion %>" ForeColor="Silver" />
            </div>            
            <div align="center">
                <asp:Label runat="server" Text='<%# Eval("question_txt") %>' />          
            </div>       
                                                                 
            <h4 align="center"><asp:Localize runat="server" Text="<%$ Resources:CatalogResources, QuestionResultAnswers %>" /></h4> 
                                    
            <asp:ListView runat="server" DataSource='<%# Eval("answers") %>'>
                <ItemTemplate>
                    <table width="90%" style="padding-left: 10px;">
                        <tr>
                            <td width="30%">
                                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, QuestionResultAnswer %>" ForeColor="Silver" />                                            
                            </td>
                            <td width="70%">
                                <asp:Label runat="server" Text='<%# Eval("answer_txt") %>' />
                            </td>
                        </tr>                        
                        <tr>
                            <td width="30%">
                                <asp:Label runat="server" Text="<%$ Resources:CatalogResources, QuestionResultAnswerLink%>" ForeColor="Silver" />                                            
                            </td>
                            <td width="70%">
                                <asp:HyperLink runat="server" Text='<%# Eval("associated_url") %>' NavigateUrl='<%# Eval("associated_url") %>' />
                            </td>
                        </tr>                        
                    </table>                       
                    <div align="center">
                        <asp:Label Visible='<%# Eval("HasImage") %>' runat="server" Text="<%$ Resources:CatalogResources, QuestionsAnswerImageCaption %>" ForeColor="Silver" />
                        <br />
                        <asp:Image Visible='<%# Eval("HasImage") %>' runat="server" ImageUrl='<%# Eval("image_uid", "~/Questionnaire/Result.aspx?image_uid={0}") %>' />
                    </div>                                                             
                    <hr />                    
                </ItemTemplate>                    
                <LayoutTemplate>
                    <div ID="itemPlaceholderContainer" runat="server" style="">
                        <span ID="itemPlaceholder" runat="server" />                        
                    </div>
                </LayoutTemplate>      
            </asp:ListView>
        </ItemTemplate>            
        <LayoutTemplate>
            <div ID="itemPlaceholderContainer" runat="server" style="">
                <span ID="itemPlaceholder" runat="server" />
            </div>
        </LayoutTemplate>               
    </asp:ListView>
            
    <br />
        <div align="center">
            <asp:Button ID="save" runat="server" OnClientClick="javascript: isTextBox=false;" Text="<%$ Resources:CatalogResources, QuestionResultSave%>" OnClick="save_Click" />
            &nbsp;            
            <asp:Button ID="edit" runat="server" OnClientClick="javascript: isTextBox=false;" Text="<%$ Resources:CatalogResources, QuestionResultEdit%>" OnClick="edit_Click" />
            
            <asp:Localize ID="viewMessage" Visible="false" runat="server" Text="<%$ Resources:CatalogResources, QuestionResultMessage%>" />           
            <br />
            <asp:HyperLink ID="viewLink" Visible="false" runat="server" />
        </div>        
    <br />
    
</asp:Content>
