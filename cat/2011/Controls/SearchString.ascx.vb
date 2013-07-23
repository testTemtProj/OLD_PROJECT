Imports System.Collections.Generic

''' <summary>
''' Строка поиска
''' </summary>
''' <remarks></remarks>
''' 
Public Enum Projects
    Web
    Zero
    News
    Catalog
    Rynok
End Enum
Partial Class Controls_SearchString
    Inherits System.Web.UI.UserControl


    Delegate Sub OnSearchDelegate(ByRef sender As Object, ByVal query As String)
    Public OnSearch As New OnSearchDelegate(AddressOf Search)



    Private queryPrevious As String

    ''' <summary>
    ''' Отображать логотип или нет
    ''' </summary>
    ''' <value></value>
    ''' <returns></returns>
    ''' <remarks></remarks>
    Public Property ShowLogo() As Boolean
        Get
            Return LogoCell.Visible
        End Get
        Set(ByVal value As Boolean)
            LogoCell.Visible = value
        End Set
    End Property


    Public Property CurrentProject() As Projects
        Get
            Return ""
        End Get
        Set(ByVal value As Projects)
            Select Case value
                Case Projects.News
                    NewsHyperLink.CssClass = "icons-active"
                    NewsHyperLink.NavigateUrl = "#"
                Case Projects.Zero
                    ZeroHyperLink.CssClass = "icons-active"
                    ZeroHyperLink.NavigateUrl = "#"
                Case Projects.Rynok
                    RynokHyperLink.CssClass = "icons-active"
                    RynokHyperLink.NavigateUrl = "#"
                Case Projects.Catalog
                    CatalogHyperLink.CssClass = "icons-active"
                    CatalogHyperLink.NavigateUrl = "#"
                Case Projects.Web
                    WebHyperLink.CssClass = "icons-active"
                    WebHyperLink.NavigateUrl = "#"
                Case Else
                    WebHyperLink.CssClass = "icons-active"
                    WebHyperLink.NavigateUrl = "#"
            End Select
        End Set
    End Property



    Protected Sub Page_Init(ByVal sender As Object, ByVal e As System.EventArgs) Handles Me.Init
        CurrentProject = Projects.Catalog
        'RynokHyperLink.CssClass = "icons-active"
    End Sub



    Protected Sub Page_Load(ByVal sender As Object, ByVal e As System.EventArgs) Handles Me.Load
        If Page.IsPostBack Then Return
        'todo: Исправить локализацию
        'DateTime.Parse()
        Select Case Links.Links.CurrentDomain
            Case "com"
                WebHyperLink.Text = "Web"
                RynokHyperLink.Text = "Rynok"
                CatalogHyperLink.Text = "Catalog"
                NewsHyperLink.Text = "News"
                SearchButton.Text = "Search Yottos"
                AdvancedSearchHyperLink.Text = "Extended Search"
                'SettingsHyperLink.Text = "Settings"
                'InResultCheckBox.Text = "In result"
                'RegionCheckBox.Text = "In region"
                'RegionRadioButtonList.Items(0).Text = "Search in Web"
                'RegionRadioButtonList.Items(1).Text = "Search in Russia"
                'RegionRadioButtonList.Items(2).Text = "Search in Ukraine"
                'RegionRadioButtonList.SelectedIndex = 0
                'RegionRadioButtonList.Visible = False
                TopImage.ImageUrl = "http://catalog.yottos.com/Image/Logo_en.gif"
            Case "ru"
                'RegionRadioButtonList.SelectedIndex = 1
                'If RegionRadioButtonList.Items.Count >= 3 Then RegionRadioButtonList.Items.RemoveAt(2)
                TopImage.ImageUrl = "http://catalog.yottos.ru/Image/Logo_ru.gif"
            Case "com.ua"
                RynokHyperLink.Text = "Ринок"
                NewsHyperLink.Text = "Новини"
                SearchButton.Text = "Пошук Yottos"
                AdvancedSearchHyperLink.Text = "Розширений пошук"
                '                SettingsHyperLink.Text = "Налаштування"
                'InResultCheckBox.Text = "В знайденому"
                'RegionCheckBox.Text = "У регіоні"
                'RegionRadioButtonList.Items(0).Text = "Пошук в інтернет"
                'RegionRadioButtonList.Items(1).Text = "Пошук в Росії"
                'RegionRadioButtonList.Items(2).Text = "Пошук в Україні"

                TopImage.ImageUrl = "http://catalog.yottos.com.ua/Image/Logo_ua.gif"
                'RegionRadioButtonList.SelectedIndex = 2
            Case Else
                TopImage.ImageUrl = "http://catalog.yottos.com/Image/Logo.gif"
        End Select


        'Dim region As Integer
        'If Not Integer.TryParse(Me.Session.Item("$Region$"), region) Then
            'Return
        'End If

        'If region < RegionRadioButtonList.Items.Count Then
         '   RegionRadioButtonList.SelectedIndex = region
        'End If


        NewsHyperLink.NavigateUrl = Links.Links.News
        RynokHyperLink.NavigateUrl = Links.Links.Rynok
        ZeroHyperLink.NavigateUrl = Links.Links.Zero
        CatalogHyperLink.NavigateUrl = Links.Links.Catalog
        '        SettingsHyperLink.NavigateUrl = Links.Links.Settings
        AdvancedSearchHyperLink.NavigateUrl = Links.Links.AdvancedSearch



        'If String.IsNullOrEmpty(Me.Session.Item("City")) Then
        '    RegionCheckBox.Visible = False
        '    RegionHyperLink.Visible = False
        'Else
        '    RegionHyperLink.Text = Me.Session.Item("City")
        'End If        
        'If (Not String.IsNullOrEmpty(Request.QueryString.Item("q"))) Then
        '    queryPrevious = HttpUtility.UrlDecode(Request.QueryString("q"), System.Text.Encoding.GetEncoding("windows-1251"))
        '    QueryTextBox.Text = queryPrevious
        'End If
        If (Not String.IsNullOrEmpty(QueryString)) Then
            QueryTextBox.Text = QueryString
        End If

    End Sub



    Protected Sub SearchButton_Click(ByVal sender As Object, ByVal e As System.EventArgs) Handles SearchButton.Click 'Handles SearchButton.Click
        OnSearch(Me, CleanQuery)

        'If Not String.IsNullOrEmpty(Query) Then
        '    Me.Session.Add("$Region$", RegionRadioButtonList.SelectedValue)
        '    If InResultCheckBox.Checked Then
        '        Me.Response.Redirect(String.Format("~/Результат/{0}", HttpUtility.UrlEncode(String.Concat(queryPrevious, " ", CleanQuery)).Replace("+", "%20")))
        '    Else
        '        Me.Response.Redirect(String.Format("~/Результат/{0}", HttpUtility.UrlEncode(CleanQuery).Replace("+", "%20")))
        '    End If
        'End If


        'If Not String.IsNullOrEmpty(Me.QueryTextBox.Text) Then
        '    HttpContext.Current.Cache.Item("$Region$") = Me.SwitchRadioButtonList.SelectedValue
        '    Me.Response.Redirect(String.Format("~/Результат/{0}", HttpUtility.HtmlEncode(Me.QueryTextBox.Text)))
        'End If
    End Sub


    Private Sub Search(ByRef sender As Object, ByVal query As String)
        'todo: Добавить в links поиск по каталогу
        Dim q As String = Me.Query
        Response.Redirect(Links.Links.Catalog & "/yottos-каталог/Поиск/" & q)
        '        Response.Redirect("http://yottos." & Links.Links.CurrentDomain & "/CatalogSearch.aspx?q=" & query)
    End Sub


    Private _initialQuery As String        ' Запрос, который изначально был в строке
    Public Property Query() As String
        Get
            Return QueryTextBox.Text
        End Get
        Set(ByVal value As String)
            If String.IsNullOrEmpty(_initialQuery) Then _initialQuery = value
            QueryTextBox.Text = value
        End Set
    End Property

    Public ReadOnly Property CleanQuery() As String
        Get
            Return Query.Replace(":", " ").Trim
        End Get
    End Property


    'Public ReadOnly Property Area() As Integer
    '    Get
    ''        Return RegionRadioButtonList.SelectedValue
     '   End Get
    'End Property


    'Public ReadOnly Property InRegion() As Boolean
    '    Get
    '        Return RegionCheckBox.Checked
    '    End Get
    'End Property


    'Protected Sub RegionCheckBox_CheckedChanged(ByVal sender As Object, ByVal e As System.EventArgs) Handles RegionCheckBox.CheckedChanged
    '    Me.Session.Add("$InCity$", RegionCheckBox.Checked)
    'End Sub
    Function isCyrillic(ByVal str As String) As Boolean
        For Each s As Char In str
            If (s >= "А" And s <= "я") Then
                Return True
            End If
        Next
        Return False
    End Function


    Protected ReadOnly Property QueryString() As String
        Get
            Dim q1 As String = HttpUtility.UrlDecode(Request.RawUrl, System.Text.Encoding.UTF8)
            If (isCyrillic(q1) = False) Then
                q1 = HttpUtility.UrlDecode(Request.RawUrl, System.Text.Encoding.GetEncoding(1251))
            End If
            Return ParseRequestParams(q1)
        End Get
    End Property
    Private Function ParseRequestParams(ByVal QueryWord As String) As String
        Try
            'I am very ashamed
            Dim queryWithParams As String
            'If QueryWord.IndexOf("?") > 0 Then
            '    queryWithParams = QueryWord.Substring(QueryWord.IndexOf("?") + 1) ' Request.QueryString("q")
            'Else
            If QueryWord.IndexOf("Поиск/") > 0 Then
                queryWithParams = QueryWord.Substring(QueryWord.IndexOf("Поиск/") + 6)
            Else
                queryWithParams = QueryWord
            End If
            'End If
            Dim match As Match = Regex.Match(queryWithParams, "^(?'search_query'[^/]*)(?=/.+=.*)/(?'params'.*)|^(?'search_query'[^/]*)/?")
            If match.Success Then
                Dim r As String = match.Groups("search_query").Value
                QueryWord = r

                Dim paramsString As String = match.Groups("params").Value
                requestParams = SplitParameters(paramsString)
                Return QueryWord
            End If
        Catch
            Return QueryWord
        End Try
    End Function
    Private Function SplitParameters(ByVal paramsString As String) As Dictionary(Of String, String)
        Dim result As Dictionary(Of String, String) = New Dictionary(Of String, String)
        Dim match As Match = Regex.Match(paramsString, "(?'pair'(?'param'[^;=]*)=(?'value'[^;=]*))\z?")
        While match.Success
            Dim param As String = match.Groups("param").Value.ToLower()
            Dim value As String = match.Groups("value").Value
            result.Add(param, value)
            match = match.NextMatch()
        End While
        Return result
    End Function
    Private Function ForOldSearch(ByVal QueryWord As String) As String
        If (Regex.Match(QueryWord, "Search", RegexOptions.IgnoreCase).Success) Then
            Return QueryWord.Substring(QueryWord.IndexOf("Search/") + 7)
        End If
        If (Regex.Match(QueryWord, "Пошук", RegexOptions.IgnoreCase).Success) Then
            Return QueryWord.Substring(QueryWord.IndexOf("Пошук/") + 6)
        End If
        If (Regex.Match(QueryWord, "Поиск", RegexOptions.IgnoreCase).Success) Then
            Return QueryWord.Substring(QueryWord.IndexOf("Поиск/") + 6)
        End If
        If (Regex.Match(QueryWord, "Результат", RegexOptions.IgnoreCase).Success) Then
            Return QueryWord.Substring(QueryWord.IndexOf("Результат/") + 10)
        Else
            Return QueryWord.Substring(QueryWord.IndexOf("Результат/") + 10)
        End If
    End Function
    Dim requestParams As Dictionary(Of String, String) = New Dictionary(Of String, String)

End Class
