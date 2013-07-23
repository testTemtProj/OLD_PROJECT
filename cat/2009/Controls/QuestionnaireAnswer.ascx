<%@ Control Language="C#" AutoEventWireup="true" CodeBehind="QuestionnaireAnswer.ascx.cs" Inherits="YottosCatalog.Controls.QuestionnaireAnswer" %>
<asp:Table runat="server" Width="100%">
    <asp:TableRow>
        <asp:TableCell BackColor="#DCDCDC" HorizontalAlign="Right" VerticalAlign="Middle" Width="30%" Text='<%# AnswerCaption %>' /> 
        <asp:TableCell HorizontalAlign="Left" VerticalAlign="Bottom" Width="70%" CssClass="PStextovka"> 
            &nbsp;&nbsp; 
            <asp:TextBox ID="answer" runat="server" Width="650px" MaxLength="100" />
            <asp:RequiredFieldValidator ID="answer_RequiredFieldValidator" runat="server" ErrorMessage='<%# AnswerErrorMessage %>' Enabled='<%# IsAnswerRequired %>' EnableClientScript='<%# IsAnswerRequired %>' ControlToValidate="answer" Display="Dynamic">*</asp:RequiredFieldValidator><br />         
            &nbsp;&nbsp; 
            <asp:Label runat="server" Text='<%# AnswerHint %>' />                            
        </asp:TableCell>
    </asp:TableRow> 
    <asp:TableRow>
        <asp:TableCell BackColor="#DCDCDC" HorizontalAlign="Right" VerticalAlign="Middle" Width="30%"> 
            <asp:Label runat="server" Text='<%# AnswerLinkCaption %>' />
        </asp:TableCell>
        <asp:TableCell HorizontalAlign="Left" VerticalAlign="Bottom" Width="70%" CssClass="PStextovka"> 
            &nbsp;&nbsp; 
            <asp:TextBox ID="answer_link" runat="server" Width="650px" MaxLength="100" />
        </asp:TableCell>
    </asp:TableRow>
    <asp:TableRow>
        <asp:TableCell BackColor="#DCDCDC" HorizontalAlign="Right" VerticalAlign="Middle" Width="30%"> 
            <asp:Label runat="server" Text='<%# AnswerImageCaption %>' />
        </asp:TableCell>
        <asp:TableCell HorizontalAlign="Left" VerticalAlign="Bottom" Width="70%" CssClass="PStextovka"> 
            &nbsp;&nbsp; 
            <asp:FileUpload ID="answer_photo" runat="server" />
        </asp:TableCell>
    </asp:TableRow>      
</asp:Table>
<hr />