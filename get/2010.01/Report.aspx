<%@ Page Language="C#" AutoEventWireup="true" CodeBehind="Report.aspx.cs" Inherits="GetMyAd.Report" StyleSheetTheme="Theme1" MasterPageFile="~/Default.Master" %>

<asp:Content ID="Content" ContentPlaceHolderID="ContentPlaceHolder" Runat="Server">


    <link type="text/css" href="css/ui-lightness/jquery-ui-1.7.2.custom.css" rel="stylesheet" />
    <link type="text/css" href="css/ui.jqgrid.css" rel="stylesheet" />
    <script src="js/jquery-1.3.2.min.js" type="text/javascript"></script>
    <script src="js/grid.locale-ru.js" type="text/javascript"></script>
    <script src="js/jquery.jqGrid.min.js" type="text/javascript"></script>
    <script type="text/javascript">
        jQuery(document).ready(function() {
        jQuery("#list").jqGrid({
            url: 'reportSummary.ashx',  
            datatype: 'json',
            mtype: 'GET',
            colNames: ['Наименование', 'Показов', 'Переходов', 'Уникальных переходов',
                    'CTR', 'CTR уникальных переходов'],
            colModel: [
              { name: 'Наименование', index: 'Наименование', width: 340, align: 'left' },
              { name: 'Impressions', index: 'Показов', width: 90, align: 'center' },
              { name: 'RecordedClicks', index: 'Переходов', width: 90, align: 'center' },
              { name: 'UniqueClicks', index: 'Уникальных переходов', width: 95, align: 'center' },
              { name: 'CTR', index: 'CTR', width: 100, align: 'center' },
              { name: 'CTR_Unique', index: 'CTR уникальных переходов', width: 100, align: 'center'}],
            pager: jQuery('#pager'),
            rowNum: 500,
            rowList: [10, 25, 50, 100, 200],
            sortname: 'CTR',
            sortorder: "desc",
            viewrecords: true,
            caption: '<%= Session["CurrentUserName"] %>',
            footerrow: true,
            userDataOnFooter: true,
            loadonce: true
        });

        }); 
    </script>
    
    <style type="text/css">
        #list {
         /*   height: 800px;*/
            
        }
    </style>


<table>
<tr>
<td style="width:200px; height: 300px;"> </td>
<td style="vertical-align: top">
    <h2>Отчёт по рекламной выгрузке:</h2>
    <table id="list" class="scroll" cellpadding="0" cellspacing="0"></table>
</td>
</tr>
</table>

            <uc:SummaryTableControl ID="summaryTable" />


    <div style="display: none">
    
<asp:SqlDataSource ID="DataSourceReport" runat="server" 
    ConnectionString="<%$ ConnectionStrings:StatisticConnectionString %>" 
    SelectCommand="report_GetMyAdd" SelectCommandType="StoredProcedure">
    <SelectParameters>
        <asp:Parameter Name="dateStart" Type="DateTime" DefaultValue="2000-01-01" />
        <asp:Parameter Name="dateEnd" Type="DateTime" DefaultValue="2020-01-01" />
        <asp:Parameter Name="GetMyAdUserID" Type="String" />
    </SelectParameters>
</asp:SqlDataSource>

<asp:Label ID="lblReportHeader" runat="server" Text="Report Header"></asp:Label>

<asp:GridView ID="gridReport" runat="server" Height="298px" Width="660px" 
        DataSourceID="DataSourceReport" AutoGenerateColumns="False">
    <Columns>
        <asp:BoundField DataField="ScriptTitle" HeaderText="Выгрузка" />
        <asp:BoundField DataField="LotTitle" HeaderText="Товарное предложение" />
        <asp:BoundField DataField="Impressions" HeaderText="Показов" />
        <asp:BoundField DataField="RecordedClicks" HeaderText="Переходов" />
        <asp:BoundField DataField="UniqueClicks" HeaderText="Уникальных переходов" />
        <asp:BoundField DataField="CTR" DataFormatString="{0:P}" HeaderText="CTR" 
            SortExpression="CTR" />
        <asp:BoundField DataField="CTR_Unique" DataFormatString="{0:P}" 
            HeaderText="CTR уникальных переходов" SortExpression="CTR_Unique" />
    </Columns>
</asp:GridView>

    
    </div>


</asp:Content>
